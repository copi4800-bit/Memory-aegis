from aegis_py.app import AegisApp
from aegis_py.conflict.core import ConflictManager
from aegis_py.memory.ingest import IngestEngine
from aegis_py.memory.scorer import WriteTimeScorer
from aegis_py.storage.manager import StorageManager
import json


def test_v7_ingest_records_governance_and_state_transition(tmp_path):
    storage = StorageManager(str(tmp_path / "v7-governance.db"))
    engine = IngestEngine(storage)

    memory = engine.ingest(
        "Aegis v7 keeps immutable evidence for admitted facts.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        subject="aegis.v7.evidence",
    )

    assert memory is not None
    state = storage.get_memory_state(memory.id)
    assert state is not None
    assert state["memory_state"] == "validated"

    transitions = storage.list_memory_state_transitions(memory.id)
    assert len(transitions) == 1
    assert transitions[0]["from_state"] == "draft"
    assert transitions[0]["to_state"] == "validated"
    assert transitions[0]["reason"] == "ingest_policy_gate"

    events = storage.list_governance_events(scope_type="project", scope_id="V7")
    assert any(event["event_kind"] == "memory_admitted" for event in events)
    persisted = storage.get_memory(memory.id)
    assert persisted is not None
    assert "score_profile" in persisted.metadata
    assert "source_reliability" in persisted.metadata["score_profile"]
    assert "evidence_completeness" in persisted.metadata["score_profile"]
    assert "ambiguity_noise" in persisted.metadata["score_profile"]
    payload = AegisApp(db_path=str(tmp_path / "v7-governance.db")).search_payload(
        "immutable evidence",
        scope_id="V7",
        scope_type="project",
        limit=5,
    )
    assert payload[0]["memory"]["score_profile"]["source_reliability"] >= 0.0
    assert payload[0]["memory"]["score_profile"]["evidence_completeness"] >= 0.0


def test_v7_write_time_profile_exposes_formal_features():
    scorer = WriteTimeScorer()

    profile = scorer.build_profile(
        content="Open the release checklist, verify 3 operator signatures, and archive the report with the incident ID.",
        memory_type="procedural",
        source_kind="manual",
    )

    assert set(("directness", "specificity", "source_reliability", "evidence_completeness", "ambiguity_noise")).issubset(profile)
    assert profile["evidence_completeness"] >= 0.7
    assert profile["ambiguity_noise"] <= 0.3


def test_v7_write_time_inference_penalizes_ambiguous_noisy_claims():
    scorer = WriteTimeScorer()

    direct_confidence, direct_activation = scorer.infer(
        content="Always restart the gateway with systemctl restart openclaw-gateway.service after updating 2 memory indices.",
        memory_type="procedural",
        source_kind="manual",
    )
    noisy_confidence, noisy_activation = scorer.infer(
        content="Maybe restart something later, perhaps after some updates.",
        memory_type="procedural",
        source_kind="message",
    )

    assert direct_confidence > noisy_confidence
    assert direct_activation > noisy_activation


def test_v7_rejected_candidate_still_writes_governance_evidence(tmp_path):
    storage = StorageManager(str(tmp_path / "v7-rejected.db"))
    engine = IngestEngine(storage)

    memory = engine.ingest(
        "Low confidence rumor should stay draft only.",
        type="episodic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        confidence=0.59,
        activation_score=1.0,
    )

    assert memory is None
    coverage = storage.summarize_evidence_coverage(scope_type="project", scope_id="V7")
    assert coverage["memory_records"] == 0
    assert coverage["evidence_events"] == 1

    events = storage.list_governance_events(scope_type="project", scope_id="V7")
    assert any(event["event_kind"] == "validation_blocked" for event in events)


def test_v7_status_transition_updates_memory_state_and_audit(tmp_path):
    storage = StorageManager(str(tmp_path / "v7-archive.db"))
    engine = IngestEngine(storage)

    memory = engine.ingest(
        "Stable operational note that will be archived.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        subject="ops.archive",
    )
    assert memory is not None

    storage._transition_memory(memory.id, status="archived", event="archive_for_history")

    state = storage.get_memory_state(memory.id)
    assert state is not None
    assert state["memory_state"] == "archived"

    transitions = storage.list_memory_state_transitions(memory.id)
    assert any(item["to_state"] == "archived" for item in transitions)


def test_v8_transition_gate_can_promote_draft_memory(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8-promote.db"))
    memory = app.put_memory(
        "Release trains require validated operator evidence.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="spec://v8/promote",
        subject="release.trains",
    )
    assert memory is not None

    app.storage.create_evidence_event(
        scope_type="project",
        scope_id="V8",
        memory_id=memory.id,
        source_kind="manual",
        source_ref="spec://v8/promote/evidence",
        raw_content="Operator evidence confirms release train policy.",
        metadata={"capture_stage": "test_support"},
    )
    persisted = app.storage.get_memory(memory.id)
    assert persisted is not None
    metadata = dict(persisted.metadata)
    metadata["memory_state"] = "draft"
    metadata["admission_state"] = "draft"
    app.storage.execute(
        "UPDATE memories SET metadata_json = ?, access_count = ?, activation_score = ? WHERE id = ?",
        (json.dumps(metadata, ensure_ascii=True), 10, 2.5, memory.id),
    )

    result = app.apply_v8_transition_gate(memory.id)

    assert result["applied"] is True
    assert result["transition_operator"]["decision"]["recommended_action"] == "promote"
    assert result["from_state"] == "draft"
    assert result["to_state"] == "validated"
    state = app.memory_state(memory.id)
    assert state is not None
    assert state["memory_state"] == "validated"
    transitions = app.storage.list_memory_state_transitions(memory.id)
    assert any(item["reason"] == "v8_core_transition_gate" and item["to_state"] == "validated" for item in transitions)


def test_v8_transition_gate_can_demote_validated_memory_under_conflict(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8-demote.db"))
    first = app.put_memory(
        "The release gate is enabled for project v8.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="spec://v8/demote/a",
        subject="release.gate",
    )
    second = app.put_memory(
        "The release gate is not enabled for project v8.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="spec://v8/demote/b",
        subject="release.gate",
    )
    third = app.put_memory(
        "The release gate remains disabled for project v8 under rollback conditions.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="spec://v8/demote/c",
        subject="release.gate",
    )
    assert first is not None and second is not None and third is not None

    ConflictManager(app.storage).scan_conflicts("release.gate")
    app.storage.execute("DELETE FROM memory_links WHERE source_id = ? OR target_id = ?", (first.id, first.id))
    app.storage.execute("DELETE FROM evidence_events WHERE memory_id = ?", (first.id,))
    app.storage.execute(
        "UPDATE memories SET access_count = ?, activation_score = ?, confidence = ? WHERE id = ?",
        (0, 1.0, 0.2, first.id),
    )

    result = app.apply_v8_transition_gate(first.id)

    assert result["applied"] is True
    assert result["transition_operator"]["decision"]["recommended_action"] == "demote"
    assert result["from_state"] == "validated"
    assert result["to_state"] == "hypothesized"
    state = app.memory_state(first.id)
    assert state is not None
    assert state["memory_state"] == "hypothesized"
    signals = app.v8_transition_gate(first.id)
    assert signals["signals"]["conflict_signal"] >= signals["transition_gate"]["thresholds"]["demote_conflict_min"]


def test_v8_transition_review_background_run_can_plan_apply_and_rollback(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v8-transition-background.db"))
    memory = app.put_memory(
        "Release policy requires validated operator evidence.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="spec://v8/background/promote",
        subject="release.policy",
    )
    assert memory is not None

    app.storage.create_evidence_event(
        scope_type="project",
        scope_id="V8",
        memory_id=memory.id,
        source_kind="manual",
        source_ref="spec://v8/background/promote/evidence",
        raw_content="Operator evidence confirms the release policy.",
        metadata={"capture_stage": "test_support"},
    )
    persisted = app.storage.get_memory(memory.id)
    assert persisted is not None
    metadata = dict(persisted.metadata)
    metadata["memory_state"] = "draft"
    metadata["admission_state"] = "draft"
    app.storage.execute(
        "UPDATE memories SET metadata_json = ?, access_count = ?, activation_score = ? WHERE id = ?",
        (json.dumps(metadata, ensure_ascii=True), 10, 2.5, memory.id),
    )

    report = app.plan_background_intelligence(scope_type="project", scope_id="V8")
    transition_run = next(
        item
        for item in app.storage.list_background_intelligence_runs(scope_type="project", scope_id="V8", status="planned")
        if item["worker_kind"] == "v8_transition_review" and item["proposal"]["memory_id"] == memory.id
    )

    assert report["proposal_count"] >= 1
    assert transition_run["proposal"]["recommended_state"] == "validated"
    shadowed = app.shadow_background_intelligence_run(transition_run["id"])
    assert shadowed["shadowed"] is True
    assert shadowed["predicted_mutations"] == 1

    applied = app.apply_background_intelligence_run(transition_run["id"], max_mutations=5)
    assert applied["applied"] is True
    state = app.memory_state(memory.id)
    assert state is not None
    assert state["memory_state"] == "validated"

    artifacts = app.evidence_artifacts(scope_type="project", scope_id="V8")
    assert any(item["artifact_kind"] == "mutation_comparison" for item in artifacts["artifacts"])

    rolled_back = app.rollback_background_intelligence_run(transition_run["id"])
    assert rolled_back["rolled_back"] is True
    reverted = app.memory_state(memory.id)
    assert reverted is not None
    assert reverted["memory_state"] == "draft"


def test_v7_background_planning_runs_on_working_copies(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-background.db"))
    app.put_memory(
        "Release gate is enabled for this project.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="release.gate",
    )
    app.put_memory(
        "Release gate is not enabled for this project.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="release.gate",
    )

    report = app.plan_background_intelligence(scope_type="project", scope_id="V7")

    assert report["proposal_count"] >= 1
    assert all(proposal["apply_mode"] == "shadow_only" for proposal in report["proposals"])
    rows = app.storage.fetch_all("SELECT status, mode FROM background_intelligence_runs")
    assert len(rows) == report["proposal_count"]
    assert all(row["status"] == "planned" for row in rows)
    assert all(row["mode"] == "working_copy" for row in rows)


def test_v7_vector_store_supports_semantic_recall(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-vectors.db"))
    app.put_memory(
        "SQLite FTS5 powers local relational storage for Aegis.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="storage.sqlite",
    )

    vector_view = app.inspect_vector_store(
        query="database storage",
        scope_type="project",
        scope_id="V7",
        limit=5,
    )
    assert len(vector_view["matches"]) >= 1

    results = app.search(
        "database storage",
        scope_id="V7",
        scope_type="project",
        semantic=True,
        limit=5,
    )
    assert len(results) >= 1
    assert any(
        result.retrieval_stage == "vector" or "vector_store_match" in result.reasons
        for result in results
    )


def test_v7_background_apply_loop_can_apply_graph_repair(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-apply.db"))
    first = app.put_memory(
        "Release checklist depends on gate review.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="release.checklist",
    )
    second = app.put_memory(
        "Gate review protects release checklist quality.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="release.checklist",
    )
    assert first is not None and second is not None

    report = app.plan_background_intelligence(scope_type="project", scope_id="V7")
    graph_runs = app.storage.list_background_intelligence_runs(
        scope_type="project",
        scope_id="V7",
        status="planned",
    )
    graph_run = next(run for run in graph_runs if run["worker_kind"] == "graph_repair")

    applied = app.apply_background_intelligence_run(graph_run["id"])
    assert applied["applied"] is True
    assert applied["links_added"] >= 1

    neighbors = app.storage.list_memory_neighbors(memory_id=first.id, limit=10)
    assert any(item["memory"]["id"] == second.id for item in neighbors)
    updated_run = app.storage.get_background_intelligence_run(graph_run["id"])
    assert updated_run is not None
    assert updated_run["status"] == "applied"


def test_v7_background_shadow_and_blast_radius_controls(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-shadow.db"))
    for index in range(4):
        app.put_memory(
            f"Release train checklist item {index}",
            type="semantic",
            scope_type="project",
            scope_id="V7",
            subject="release.train",
        )

    app.plan_background_intelligence(scope_type="project", scope_id="V7")
    runs = app.storage.list_background_intelligence_runs(scope_type="project", scope_id="V7", status="planned")
    condensation = next(run for run in runs if run["worker_kind"] == "condensation")

    shadowed = app.shadow_background_intelligence_run(condensation["id"])
    assert shadowed["shadowed"] is True
    assert shadowed["predicted_mutations"] >= 1

    blocked = app.background_intelligence.apply_run(condensation["id"], max_mutations=1)
    assert blocked["applied"] is False
    assert blocked["reason"] == "blast_radius_exceeded"
    governance = app.inspect_governance(scope_type="project", scope_id="V7")
    assert any(event["event_kind"] == "background_run_blocked" for event in governance["events"])


def test_v7_background_rollback_restores_graph_repairs(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-rollback.db"))
    first = app.put_memory(
        "Checklist rollback seed.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="rollback.subject",
    )
    second = app.put_memory(
        "Checklist rollback neighbor.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        subject="rollback.subject",
    )
    assert first is not None and second is not None

    app.plan_background_intelligence(scope_type="project", scope_id="V7")
    run = next(
        item
        for item in app.storage.list_background_intelligence_runs(scope_type="project", scope_id="V7", status="planned")
        if item["worker_kind"] == "graph_repair"
    )
    applied = app.apply_background_intelligence_run(run["id"])
    assert applied["applied"] is True
    assert any(item["memory"]["id"] == second.id for item in app.storage.list_memory_neighbors(memory_id=first.id, limit=10))

    rolled_back = app.rollback_background_intelligence_run(run["id"])
    assert rolled_back["rolled_back"] is True
    assert not any(item["memory"]["id"] == second.id for item in app.storage.list_memory_neighbors(memory_id=first.id, limit=10))
    linked = app.link_memories(first.id, second.id, link_type="supports", weight=0.7)
    assert linked["link"]["metadata"]["canonical_edge_type"] == "RESULTS_IN"


def test_v7_condensation_creates_lineage_summary_and_artifact(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-condense.db"))
    for content in (
        "User usually drinks tea in the morning.",
        "User picks tea for breakfast time.",
        "Tea is the normal morning preference.",
    ):
        app.put_memory(
            content,
            type="semantic",
            scope_type="project",
            scope_id="V7",
            subject="drink.preference",
        )

    app.plan_background_intelligence(scope_type="project", scope_id="V7")
    run = next(
        item
        for item in app.storage.list_background_intelligence_runs(scope_type="project", scope_id="V7", status="planned")
        if item["worker_kind"] == "condensation"
    )
    applied = app.apply_background_intelligence_run(run["id"], max_mutations=10)
    assert applied["applied"] is True

    summaries = app.storage.fetch_all(
        """
        SELECT id, metadata_json
        FROM memories
        WHERE scope_type = ? AND scope_id = ? AND source_kind = 'system'
        """,
        ("project", "V7"),
    )
    assert len(summaries) >= 1
    metadata = app.storage._coerce_metadata(summaries[0]["metadata_json"])
    assert metadata["lineage"]["preserves_raw_evidence"] is True
    assert len(metadata["derived_from"]) >= 2
    assert "summary_object" in metadata
    assert "contexts" in metadata["summary_object"]

    artifacts = app.evidence_artifacts(scope_type="project", scope_id="V7")
    condensation = next(item for item in artifacts["artifacts"] if item["artifact_kind"] == "condensation_summary")
    assert "summary_object" in condensation["payload"]
    assert condensation["payload"]["summary_object"]["summary_type"] in {"preference_summary", "condensed_summary"}
    assert any(item["artifact_kind"] == "mutation_comparison" for item in artifacts["artifacts"])


def test_v7_condensation_rollback_removes_summary_memory(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "v7-condense-rollback.db"))
    for content in (
        "Morning tea is common.",
        "Tea is common in the morning.",
        "Tea usually happens before work.",
    ):
        app.put_memory(
            content,
            type="semantic",
            scope_type="project",
            scope_id="V7",
            subject="drink.preference",
        )

    app.plan_background_intelligence(scope_type="project", scope_id="V7")
    run = next(
        item
        for item in app.storage.list_background_intelligence_runs(scope_type="project", scope_id="V7", status="planned")
        if item["worker_kind"] == "condensation"
    )
    applied = app.apply_background_intelligence_run(run["id"], max_mutations=10)
    assert applied["applied"] is True
    system_memories_before = app.storage.fetch_all(
        "SELECT id FROM memories WHERE scope_type = ? AND scope_id = ? AND source_kind = 'system'",
        ("project", "V7"),
    )
    assert len(system_memories_before) >= 1

    rolled_back = app.rollback_background_intelligence_run(run["id"])
    assert rolled_back["rolled_back"] is True
    system_memories_after = app.storage.fetch_all(
        "SELECT id FROM memories WHERE scope_type = ? AND scope_id = ? AND source_kind = 'system'",
        ("project", "V7"),
    )
    assert system_memories_after == []


def test_v7_contextual_conflict_adjudication_prefers_coexistence(tmp_path):
    storage = StorageManager(str(tmp_path / "v7-context.db"))
    engine = IngestEngine(storage)
    conflicts = ConflictManager(storage)

    first = engine.ingest(
        "User prefers tea in the morning.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        subject="drink.preference",
    )
    second = engine.ingest(
        "User prefers coffee when stressed at work.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        subject="drink.preference",
    )
    assert first is not None and second is not None

    conflicts.scan_conflicts("drink.preference")
    prompts = conflicts.list_resolution_prompts(subject="drink.preference", scope_type="project", scope_id="V7")
    if prompts:
        payload = prompts[0]
    else:
        conflict = storage.fetch_one("SELECT id FROM conflicts WHERE subject_key = ?", ("drink.preference",))
        payload = conflicts._build_conflict_payload(conflict["id"])
    assert payload is not None
    assert payload["classification"] == "contextual_coexistence"
    assert payload["decision"] == "coexist"
    assert payload["decision_policy"] == "contextual_preference_coexistence"
    resolved = conflicts.resolve_with_user_decision(payload["conflict_id"], action="keep_both_scope_split")
    assert resolved["resolution"] == "resolved_by_user_scope_split"
    coexistence = storage.fetch_all(
        "SELECT metadata_json FROM memories WHERE source_kind = 'system' AND source_ref = ?",
        (f"conflict://{payload['conflict_id']}",),
    )
    assert len(coexistence) == 1
    metadata = storage._coerce_metadata(coexistence[0]["metadata_json"])
    assert metadata["coexistence_summary"]["policy"] == "contextual_preference_coexistence"
    artifacts = storage.list_evidence_artifacts(scope_type="project", scope_id="V7")
    assert any(item["artifact_kind"] == "coexistence_summary" for item in artifacts)


def test_v7_conflict_scan_writes_evidence_artifacts(tmp_path):
    storage = StorageManager(str(tmp_path / "v7-artifacts.db"))
    engine = IngestEngine(storage)
    conflicts = ConflictManager(storage)

    engine.ingest(
        "The release gate is enabled.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        subject="release.gate",
    )
    engine.ingest(
        "The release gate is not enabled.",
        type="semantic",
        scope_type="project",
        scope_id="V7",
        source_kind="manual",
        subject="release.gate",
    )
    conflicts.scan_conflicts("release.gate")

    artifacts = storage.list_evidence_artifacts(scope_type="project", scope_id="V7")
    assert any(item["artifact_kind"] == "conflict_comparison" for item in artifacts)
