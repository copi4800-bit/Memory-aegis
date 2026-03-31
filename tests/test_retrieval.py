import pytest
import json
from aegis_py.conflict.core import ConflictManager
from aegis_py.app import AegisApp
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.ingest import IngestEngine
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery

@pytest.fixture
def temp_engine(tmp_path):
    db_file = tmp_path / "test_aegis_retrieval.db"
    storage = StorageManager(str(db_file))
    engine = IngestEngine(storage)
    return storage, engine

def test_retrieval_scope_isolation(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    
    # Ingest into Scope A
    engine.ingest("Secret recipe for project A", scope_id="A", scope_type="project")
    # Ingest into Scope B
    engine.ingest("Secret recipe for project B", scope_id="B", scope_type="project")
    
    # Search Scope A
    query_a = SearchQuery(query="recipe", scope_id="A", scope_type="project", include_global=False)
    results_a = pipeline.search(query_a)
    assert len(results_a) == 1
    assert "project A" in results_a[0].memory.content
    
    # Search Scope B
    query_b = SearchQuery(query="recipe", scope_id="B", scope_type="project", include_global=False)
    results_b = pipeline.search(query_b)
    assert len(results_b) == 1
    assert "project B" in results_b[0].memory.content

def test_retrieval_reranking(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    
    # Ingest some memories
    engine.ingest("Python is a great language", scope_id="test")
    engine.ingest("Python is fun to learn", scope_id="test")
    
    # Ingest one and boost its activation score manually
    mem_to_boost = engine.ingest("Python is very fast", scope_id="test")
    with storage._get_connection() as conn:
        conn.execute(
            "UPDATE memories SET activation_score = 5.0 WHERE id = ?", (mem_to_boost.id,)
        )
        conn.commit()
    
    query = SearchQuery(query="Python", scope_id="test", scope_type="session")
    results = pipeline.search(query)
    
    assert len(results) >= 3
    # The boosted memory should be near the top due to activation boost
    assert results[0].memory.id == mem_to_boost.id
    assert "Active context boost" in results[0].reason

def test_retrieval_explainability(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    
    engine.ingest("Tokyo is the capital of Japan", scope_id="world", scope_type="session", type="semantic")
    
    query = SearchQuery(query="Tokyo", scope_id="world", scope_type="session")
    results = pipeline.search(query)
    
    assert len(results) > 0
    assert "Japan" in results[0].memory.content
    assert results[0].reason == "Strong semantic fact match."
    assert results[0].provenance.startswith("[message]")
    assert results[0].trust_state == "strong"
    assert "high-confidence" in results[0].trust_reason or "solid direct match" in results[0].trust_reason


def test_retrieval_can_include_global_fallback_without_cross_project_leakage(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    project_memory = engine.ingest("Aegis release checklist for project scope", scope_id="A", scope_type="project")
    global_memory = engine.ingest("Aegis release checklist for all projects", scope_id="global-default", scope_type="global")
    engine.ingest("Aegis release checklist for another project", scope_id="B", scope_type="project")

    query = SearchQuery(query="release checklist", scope_id="A", scope_type="project", include_global=True, limit=5)
    results = pipeline.search(query)

    result_ids = [result.memory.id for result in results]
    assert project_memory.id in result_ids
    assert global_memory.id in result_ids
    assert all(result.memory.scope_id != "B" for result in results)


def test_retrieval_returns_empty_list_for_unmatched_query(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    engine.ingest("Aegis stores deployment runbooks", scope_id="P1", scope_type="project")

    query = SearchQuery(query="volcano", scope_id="P1", scope_type="project", include_global=False)
    results = pipeline.search(query)

    assert results == []


def test_retrieval_handles_punctuation_heavy_queries_without_fts_failure(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    stored = engine.ingest("Release gate checklist stays searchable.", scope_id="P1", scope_type="project")

    query = SearchQuery(query="release-gate", scope_id="P1", scope_type="project", include_global=False)
    results = pipeline.search(query)

    assert len(results) == 1
    assert results[0].memory.id == stored.id


def test_retrieval_surfaces_conflict_visibility(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    conflicts = ConflictManager(storage)

    engine.ingest(
        "The release gate is enabled for aegis.",
        scope_id="P1",
        scope_type="project",
        type="episodic",
        subject="release.gate",
    )
    engine.ingest(
        "The release gate is not enabled for aegis.",
        scope_id="P1",
        scope_type="project",
        type="episodic",
        subject="release.gate",
    )
    conflicts.scan_conflicts("release.gate")

    query = SearchQuery(query="release gate", scope_id="P1", scope_type="project", include_global=False)
    results = pipeline.search(query)

    assert len(results) == 2
    assert any(result.conflict_status == "open" for result in results)
    assert any("conflict_visible" in result.reasons for result in results)
    assert all(result.trust_state == "conflicting" for result in results)


def test_retrieval_marks_relationship_expansion_as_uncertain(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    seed = engine.ingest(
        "Sync envelopes track revision history.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="sync.history",
    )
    neighbor = engine.ingest(
        "Revision stamps prevent stale imports.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="sync.history",
    )
    assert seed is not None and neighbor is not None

    query = SearchQuery(query="sync envelopes", scope_id="P1", scope_type="project", include_global=False, limit=5)
    results = pipeline.search_with_expansion(query)

    by_id = {result.memory.id: result for result in results}
    assert by_id[seed.id].trust_state == "strong"
    assert by_id[neighbor.id].trust_state == "uncertain"


def test_retrieval_filters_invalidated_and_draft_states(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    validated = engine.ingest(
        "Validated release evidence.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="release.state",
    )
    draft = engine.ingest(
        "Low confidence release rumor.",
        scope_id="P1",
        scope_type="project",
        type="episodic",
        subject="release.state",
        confidence=0.58,
        activation_score=1.0,
    )
    invalidated = engine.ingest(
        "Release gate is enabled.",
        scope_id="P1",
        scope_type="project",
        type="episodic",
        subject="release.gate",
    )
    replacement = engine.ingest(
        "Release gate is not enabled.",
        scope_id="P1",
        scope_type="project",
        type="episodic",
        subject="release.gate",
    )
    assert validated is not None
    assert draft is None
    assert invalidated is not None
    assert replacement is not None

    storage.execute("UPDATE memories SET status = ? WHERE id = ?", ("superseded", invalidated.id))

    query = SearchQuery(query="release", scope_id="P1", scope_type="project", include_global=False, limit=10)
    results = pipeline.search(query)
    ids = [result.memory.id for result in results]

    assert validated.id in ids
    assert invalidated.id not in ids


def test_retrieval_marks_hypothesized_state_as_uncertain(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    first = engine.ingest(
        "The rollout checklist is approved.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="rollout.checklist",
    )
    second = engine.ingest(
        "The rollout checklist is not approved.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="rollout.checklist",
    )
    assert first is not None and second is not None

    query = SearchQuery(query="rollout checklist", scope_id="P1", scope_type="project", include_global=False, limit=10)
    results = pipeline.search(query)
    by_id = {result.memory.id: result for result in results}

    assert by_id[first.id].trust_state in {"strong", "conflicting"}
    assert by_id[second.id].admission_state == "hypothesized"
    assert by_id[second.id].trust_state == "uncertain"


def test_v8_dynamic_scoring_prefers_higher_evidence_and_lower_conflict(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    conflicts = ConflictManager(storage)

    strong = engine.ingest(
        "Release plan evidence-backed checklist for launch.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="release.plan.strong",
        source_ref="spec://release-plan/strong",
    )
    weak = engine.ingest(
        "Release plan rumor checklist for launch.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="release.plan.weak",
        source_ref="spec://release-plan/weak",
    )
    challenger = engine.ingest(
        "Release plan rumor checklist is not approved.",
        scope_id="P1",
        scope_type="project",
        type="semantic",
        subject="release.plan.weak",
        source_ref="spec://release-plan/challenger",
    )
    assert strong is not None and weak is not None and challenger is not None

    storage.create_evidence_event(
        scope_type="project",
        scope_id="P1",
        memory_id=strong.id,
        source_kind="manual",
        source_ref="spec://release-plan/supporting-evidence",
        raw_content="Independent evidence confirms the release plan checklist.",
        metadata={"capture_stage": "test_support"},
    )
    conflicts.scan_conflicts("release.plan.weak")

    query = SearchQuery(query="release plan checklist", scope_id="P1", scope_type="project", include_global=False, limit=5)
    results = pipeline.search(query)

    assert results[0].memory.id == strong.id
    assert "v8_evidence_strong" in results[0].reasons
    weak_result = next(result for result in results if result.memory.id == weak.id)
    assert "v8_conflict_pressure" in weak_result.reasons


def test_v8_dynamic_scoring_prefers_usage_reinforced_memory(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)

    cold = engine.ingest(
        "Deployment runbook applies to release automation.",
        scope_id="P1",
        scope_type="project",
        type="procedural",
        subject="deployment.runbook",
    )
    warm = engine.ingest(
        "Deployment runbook applies to release automation and rollback.",
        scope_id="P1",
        scope_type="project",
        type="procedural",
        subject="deployment.runbook.alt",
    )
    assert cold is not None and warm is not None

    storage.execute("UPDATE memories SET access_count = ?, activation_score = ? WHERE id = ?", (8, 2.5, warm.id))

    query = SearchQuery(query="deployment runbook", scope_id="P1", scope_type="project", include_global=False, limit=5)
    results = pipeline.search(query)

    assert results[0].memory.id == warm.id
    assert results[0].v8_core_signals is not None
    assert results[0].v8_core_signals["usage_signal"] > 0.0
    assert "v8_usage_reinforced" in results[0].reasons


def test_v8_outcome_feedback_updates_dynamic_state_and_retrieval_preference(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8_feedback.db"))
    strong = app.put_memory(
        "Deploy rollback checklist for release trains.",
        type="procedural",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        source_ref="spec://v8-feedback/strong",
        subject="deploy.rollback",
    )
    weak = app.put_memory(
        "Deploy rollback checklist for release trains with stale notes.",
        type="procedural",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        source_ref="spec://v8-feedback/weak",
        subject="deploy.rollback.alt",
    )
    assert strong is not None and weak is not None

    positive = app.apply_v8_outcome_feedback(
        strong.id,
        success_score=1.0,
        relevance_score=1.0,
        override_score=0.0,
    )
    negative = app.apply_v8_outcome_feedback(
        weak.id,
        success_score=0.15,
        relevance_score=0.2,
        override_score=0.9,
    )

    assert positive["updated_dynamics"]["usage_signal"] > 0.0
    assert positive["updated_dynamics"]["belief_score"] > 0.5
    assert positive["signals"]["usage_signal"] >= positive["updated_dynamics"]["usage_signal"] - 1e-6
    assert negative["updated_dynamics"]["regret_signal"] > 0.0
    assert negative["updated_dynamics"]["decay_signal"] > 0.0
    assert negative["signals"]["regret_signal"] >= negative["updated_dynamics"]["regret_signal"] - 1e-6
    persisted = app.storage.get_memory(strong.id)
    assert persisted is not None
    assert "v8_state" in persisted.metadata
    assert "v8_dynamics" in persisted.metadata
    assert persisted.metadata["v8_state"]["belief_score"] == positive["signals"]["belief_score"]
    assert persisted.metadata["v8_state"]["usage_signal"] == positive["signals"]["usage_signal"]
    assert persisted.metadata["v8_state"]["trust_score"] == positive["signals"]["trust_score"]
    assert positive["signals"]["persisted_state"]["belief_score"] == positive["signals"]["belief_score"]
    assert positive["signals"]["derived_state"]["evidence_signal"] == positive["signals"]["evidence_signal"]

    results = app.search("deploy rollback checklist", scope_type="project", scope_id="P1", limit=5)
    assert results[0].memory.id == strong.id
    weak_result = next(result for result in results if result.memory.id == weak.id)
    assert "v8_regret_pressure" in weak_result.reasons

    governance = app.inspect_governance(scope_type="project", scope_id="P1")
    assert any(event["event_kind"] == "v8_outcome_feedback_applied" for event in governance["events"])
    artifacts = app.evidence_artifacts(scope_type="project", scope_id="P1")
    assert any(item["artifact_kind"] == "v8_outcome_feedback" for item in artifacts["artifacts"])


def test_v8_retrieval_bundle_feedback_assigns_credit_and_regret_across_results(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8_bundle_feedback.db"))
    chosen = app.put_memory(
        "Incident rollback checklist with verified release steps.",
        type="procedural",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        source_ref="spec://v8-bundle/chosen",
        subject="incident.rollback.primary",
    )
    bypassed = app.put_memory(
        "Incident rollback checklist with outdated steps.",
        type="procedural",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        source_ref="spec://v8-bundle/bypassed",
        subject="incident.rollback.secondary",
    )
    assert chosen is not None and bypassed is not None

    initial = app.search("incident rollback checklist", scope_type="project", scope_id="P1", limit=5)
    assert {item.memory.id for item in initial} >= {chosen.id, bypassed.id}

    bundle = app.apply_v8_retrieval_feedback(
        query="incident rollback checklist",
        scope_id="P1",
        scope_type="project",
        success_score=1.0,
        selected_memory_ids=[chosen.id],
        override_memory_ids=[bypassed.id],
        limit=5,
    )

    assert bundle["applied"] is True
    assert bundle["before_snapshot"]["bundle_size"] >= 2.0
    assert bundle["after_snapshot"]["bundle_size"] >= 2.0
    assert bundle["before_snapshot"]["energy"] >= 0.0
    assert bundle["after_snapshot"]["objective"] >= 0.0
    assignments = {item["memory_id"]: item for item in bundle["assignments"]}
    assert assignments[chosen.id]["contribution_weight"] > assignments[bypassed.id]["contribution_weight"]
    assert assignments[chosen.id]["feedback"]["usage_signal"] > assignments[bypassed.id]["feedback"]["usage_signal"]
    assert assignments[bypassed.id]["feedback"]["regret_signal"] > 0.0

    updated = app.search("incident rollback checklist", scope_type="project", scope_id="P1", limit=5)
    by_id = {item.memory.id: item for item in updated}
    assert updated[0].memory.id == chosen.id
    assert "v8_regret_pressure" in by_id[bypassed.id].reasons

    governance = app.inspect_governance(scope_type="project", scope_id="P1")
    assert any(event["event_kind"] == "v8_retrieval_feedback_applied" for event in governance["events"])
    artifacts = app.evidence_artifacts(scope_type="project", scope_id="P1")
    assert any(item["artifact_kind"] == "v8_retrieval_feedback_bundle" for item in artifacts["artifacts"])


def test_app_can_report_v8_bundle_snapshot(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8_bundle_snapshot.db"))
    stored = app.put_memory(
        "Release runbook for rollback and recovery.",
        type="procedural",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        source_ref="spec://v8-bundle-snapshot",
        subject="release.runbook",
    )
    assert stored is not None

    payload = app.v8_bundle_snapshot(
        query="release runbook",
        scope_type="project",
        scope_id="P1",
        limit=5,
    )

    snapshot = payload["snapshot"]
    assert payload["backend"] == "python"
    assert stored.id in payload["memory_ids"]
    assert snapshot["bundle_size"] >= 1.0
    assert snapshot["energy"] >= 0.0
    assert snapshot["objective"] >= 0.0


def test_app_can_report_v8_field_snapshot(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8_field_snapshot.db"))
    first = app.put_memory(
        "Release checklist is evidence-backed.",
        type="semantic",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        subject="release.checklist",
    )
    second = app.put_memory(
        "Rollback runbook stays ready for incidents.",
        type="procedural",
        scope_type="project",
        scope_id="P1",
        source_kind="manual",
        subject="rollback.runbook",
    )
    assert first is not None and second is not None

    payload = app.v8_field_snapshot(scope_type="project", scope_id="P1")

    assert payload["backend"] == "python"
    assert payload["scope"]["scope_type"] == "project"
    assert payload["scope"]["scope_id"] == "P1"
    assert first.id in payload["memory_ids"]
    assert second.id in payload["memory_ids"]
    assert sum(payload["counts"].values()) >= 2
    assert 0.0 <= payload["averages"]["belief_score"] <= 1.0
    assert 0.0 <= payload["averages"]["trust_score"] <= 1.0
    assert 0.0 <= payload["averages"]["readiness_score"] <= 1.0
    assert payload["energy"]["bundle_size"] >= 2.0
    assert payload["energy"]["energy"] >= 0.0
    assert payload["energy"]["objective"] >= 0.0


def test_app_can_explain_v8_core_signals_and_transition_gate(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8_core.db"))
    stored = app.put_memory(
        "Validated release policy for launch trains.",
        type="semantic",
        scope_type="project",
        scope_id="P1",
        subject="release.policy",
        source_kind="manual",
        source_ref="spec://release-policy",
    )
    assert stored is not None

    app.storage.create_evidence_event(
        scope_type="project",
        scope_id="P1",
        memory_id=stored.id,
        source_kind="manual",
        source_ref="spec://release-policy/evidence",
        raw_content="Operator evidence confirms the release policy.",
        metadata={"capture_stage": "test_support"},
    )
    metadata = dict(stored.metadata)
    metadata["memory_state"] = "draft"
    metadata["admission_state"] = "draft"
    app.storage.execute(
        "UPDATE memories SET metadata_json = ?, access_count = ?, activation_score = ? WHERE id = ?",
        (json.dumps(metadata, ensure_ascii=True), 10, 2.5, stored.id),
    )

    signals_payload = app.v8_core_signals(stored.id)
    gate_payload = app.v8_transition_gate(stored.id)

    signals = signals_payload["signals"]
    assert signals_payload["backend"] == "python"
    assert signals_payload["observables"]["trust"]["score"] == signals["trust_score"]
    assert signals_payload["observables"]["readiness"]["score"] == signals["readiness_score"]
    assert signals_payload["observables"]["state"] == signals["admission_state"]
    assert all(0.0 <= signals[key] <= 1.0 for key in [
        "evidence_signal",
        "support_signal",
        "conflict_signal",
        "usage_signal",
        "regret_signal",
        "stability_signal",
        "decay_signal",
        "belief_score",
        "trust_score",
        "readiness_score",
    ])
    assert "persisted_state" in signals
    assert "derived_state" in signals
    assert "interaction_inputs" in signals
    assert signals["persisted_state"]["belief_score"] == signals["belief_score"]
    assert signals["derived_state"]["conflict_signal"] == signals["conflict_signal"]
    assert signals["interaction_inputs"]["support"]["aggregate_weight"] == signals["support_weight"]
    assert signals["interaction_inputs"]["conflict"]["aggregate_weight"] == signals["conflict_weight"]
    assert signals["derived_state"]["interaction_inputs"]["conflict"]["direct_conflict_open"] == signals["direct_conflict_open"]
    assert gate_payload["transition_operator"]["inputs"]["current_state"] == "draft"
    assert gate_payload["transition_operator"]["decision"]["recommended_state"] == gate_payload["transition_gate"]["recommended_state"]
    assert gate_payload["thresholds"]["promote_trust"] == gate_payload["transition_gate"]["thresholds"]["promote_trust"]
    assert gate_payload["observables"]["trust"]["score"] == gate_payload["signals"]["trust_score"]
    assert gate_payload["observables"]["readiness"]["score"] == gate_payload["signals"]["readiness_score"]
    assert gate_payload["transition_gate"]["thresholds"]["promote_trust"] > gate_payload["transition_gate"]["thresholds"]["demote_trust"]
    assert gate_payload["transition_gate"]["current_state"] == "draft"
