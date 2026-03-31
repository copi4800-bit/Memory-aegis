import pytest
import os
import subprocess
import sys
from uuid import uuid4
from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer
from aegis_py.storage.models import Memory

def test_procedural_and_profile(app_env):
    app = app_env
    
    # 1. Ingest procedural memory
    app.put_memory(
        "To deploy: 1. Build, 2. Push, 3. Restart.",
        type="procedural",
        scope_id="P1"
    )
    
    # 2. Render profile
    profile = app.render_profile("P1")
    assert "## Memory Profile: P1" in profile
    assert "### Core Knowledge & Persona" in profile
    assert "procedural" in profile.lower()
    assert "deploy" in profile

@pytest.fixture
def app_env(tmp_path):
    db_file = tmp_path / "aegis_integration.db"
    app = AegisApp(db_path=str(db_file))
    return app

def test_full_ingest_and_search_flow(app_env):
    app = app_env
    
    # 1. Ingest with session tracking
    app.put_memory(
        "Code is 'KRAKEN'. Be brief.",
        type="episodic",
        scope_id="P1",
        session_id="S1"
    )
    
    # 2. Search
    results = app.search("KRAKEN", scope_id="P1")
    assert len(results) > 0
    assert "KRAKEN" in results[0].memory.content
    
    # 3. Verify preferences (extracted during put_memory)
    # At this point, signals are stored but NOT consolidated
    assert app.storage.get_profile("P1", "session") is None
    
    # 4. End session -> Consolidate
    app.end_session("S1", "P1", "session")
    
    # 5. Verify preferences are now persistent
    prefs = app.get_preferences("P1", "session")
    assert prefs is not None
    assert "verbosity" in prefs
    # "Please be brief..." should result in low verbosity
    assert prefs["verbosity"] < 0.5 

def test_maintenance_flow(app_env):
    app = app_env
    
    # Ingest something that will expire if we move time?
    # Actually just check that maintenance runs without error
    app.maintenance()
    assert True


def test_app_entrypoints_preserve_canonical_scope_and_provenance_contract(app_env):
    app = app_env

    stored = app.put_memory(
        "Run conflict scan before release closeout.",
        type="procedural",
        scope_type="project",
        scope_id="aegis-vnext",
        source_kind="manual",
        source_ref="runbook#release",
        subject="workflow.release",
        summary="Release conflict scan",
    )
    assert stored is not None

    persisted = app.storage.get_memory(stored.id)
    assert persisted is not None
    assert persisted.scope_type == "project"
    assert persisted.scope_id == "aegis-vnext"
    assert persisted.source_kind == "manual"
    assert persisted.source_ref == "runbook#release"
    assert persisted.subject == "workflow.release"

    results = app.search("conflict scan", scope_id="aegis-vnext", scope_type="project")
    assert len(results) == 1
    assert results[0].memory.id == stored.id
    assert results[0].source_ref == "runbook#release"
    assert results[0].scope_type == "project"
    assert results[0].scope_id == "aegis-vnext"
    assert "scope_exact_match" in results[0].reasons


def test_canonical_ingest_persists_raw_evidence_and_memory_linkage(app_env):
    app = app_env

    stored = app.put_memory(
        "Release checklist says the sync manifest must be validated before publish.",
        type="procedural",
        scope_type="project",
        scope_id="evidence-runtime",
        source_kind="manual",
        source_ref="checklist#sync",
        subject="workflow.publish",
    )
    assert stored is not None

    persisted = app.storage.get_memory(stored.id)
    evidence_rows = app.storage.list_evidence_events_for_memory(stored.id)
    assert persisted is not None
    assert len(evidence_rows) == 1
    assert persisted.metadata["evidence"]["event_id"] == evidence_rows[0].id
    assert evidence_rows[0].raw_content == stored.content
    assert evidence_rows[0].source_ref == "checklist#sync"

    results = app.search("sync manifest validated", scope_id="evidence-runtime", scope_type="project")
    assert len(results) == 1
    assert results[0].memory.id == stored.id
    assert results[0].source_ref == "checklist#sync"


def test_app_internal_evidence_helpers_report_coverage_without_public_contract_drift(app_env):
    app = app_env

    first = app.put_memory(
        "Internal evidence lookup should stay runtime-only.",
        type="semantic",
        scope_type="project",
        scope_id="EVIDENCE-COVERAGE",
        source_kind="manual",
        source_ref="spec#internal",
    )
    second = app.put_memory(
        "Coverage report should detect missing linkage.",
        type="semantic",
        scope_type="project",
        scope_id="EVIDENCE-COVERAGE",
        source_kind="manual",
        source_ref="spec#coverage",
    )
    assert first is not None and second is not None

    app.storage.execute("UPDATE memories SET metadata_json = ? WHERE id = ?", ("{}", second.id))

    evidence = app.get_memory_evidence(first.id)
    coverage = app.evidence_coverage(scope_type="project", scope_id="EVIDENCE-COVERAGE")
    status = app.status()
    searched = app.search_payload("runtime-only", scope_type="project", scope_id="EVIDENCE-COVERAGE")

    assert len(evidence) == 1
    assert evidence[0]["memory_id"] == first.id
    assert coverage["memory_records"] == 2
    assert coverage["linked_memories"] == 1
    assert coverage["missing_linkage"] == 1
    assert "evidence_coverage" not in status
    assert "evidence" not in searched[0]


def test_app_internal_state_helpers_report_admission_states_without_public_contract_drift(app_env):
    app = app_env

    validated = app.put_memory(
        "The release checklist is approved.",
        type="semantic",
        scope_type="project",
        scope_id="STATEFUL",
        source_kind="manual",
        subject="release.checklist",
    )
    hypothesized = app.put_memory(
        "The release checklist is not approved.",
        type="semantic",
        scope_type="project",
        scope_id="STATEFUL",
        source_kind="manual",
        subject="release.checklist",
    )
    assert validated is not None and hypothesized is not None

    validated_state = app.memory_state(validated.id)
    hypothesized_state = app.memory_state(hypothesized.id)
    summary = app.memory_state_summary(scope_type="project", scope_id="STATEFUL")
    payload = app.search_payload("release checklist", scope_type="project", scope_id="STATEFUL")

    assert validated_state is not None
    assert validated_state["admission_state"] == "validated"
    assert hypothesized_state is not None
    assert hypothesized_state["admission_state"] == "hypothesized"
    assert summary["state_counts"]["validated"] == 1
    assert summary["state_counts"]["hypothesized"] == 1
    assert "admission_state" not in payload[0]


def test_public_search_payload_stays_shape_compatible_while_internal_retrieval_uses_state(app_env):
    app = app_env

    app.put_memory(
        "The audit runway is approved.",
        type="semantic",
        scope_type="project",
        scope_id="STATE-SEARCH",
        source_kind="manual",
        subject="audit.runway",
    )
    app.put_memory(
        "The audit runway is not approved.",
        type="semantic",
        scope_type="project",
        scope_id="STATE-SEARCH",
        source_kind="manual",
        subject="audit.runway",
    )

    payload = app.search_payload("audit runway", scope_type="project", scope_id="STATE-SEARCH")

    assert len(payload) == 2
    assert "admission_state" not in payload[0]
    assert "promotion" not in payload[0]["memory"]


def test_promotion_gate_rejects_low_confidence_candidate_without_changing_public_search_shape(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "promotion-gate.db"))

    first = app.put_memory(
        "The release train departs on Friday.",
        type="semantic",
        scope_type="project",
        scope_id="PROMOTION",
        source_kind="manual",
        subject="release.schedule",
    )
    rejected = app.put_memory(
        "Low-confidence rumor about the release train.",
        type="episodic",
        scope_type="project",
        scope_id="PROMOTION",
        source_kind="manual",
        subject="release.schedule",
        confidence=0.58,
        activation_score=1.0,
    )

    payload = app.search_payload("release train", scope_type="project", scope_id="PROMOTION")
    coverage = app.evidence_coverage(scope_type="project", scope_id="PROMOTION")

    assert first is not None
    assert rejected is None
    assert len(payload) == 1
    assert payload[0]["memory"]["id"] == first.id
    assert "promotion" not in payload[0]
    assert coverage["memory_records"] == 1
    assert coverage["evidence_events"] == 2

    app.close()


def test_mcp_operational_flows_return_consistent_json(app_env):
    server = AegisMCPServer(db_path=app_env.db_path)

    stored = server.memory_store(
        "semantic",
        "Aegis stores local release notes.",
        "release.notes",
        scope_type="project",
        scope_id="P2",
        source_kind="manual",
        source_ref="notes#1",
    )
    assert "Stored semantic memory" in stored

    searched = server.memory_search("release notes", scope_type="project", scope_id="P2")
    payload = __import__("json").loads(searched)
    assert payload[0]["memory"]["scope_id"] == "P2"
    assert payload[0]["provenance"] == "[manual] notes#1"
    assert payload[0]["trust_state"] == "strong"
    assert "trust_reason" in payload[0]

    status = __import__("json").loads(server.memory_status())
    assert status["counts"]["active"] == 1

    cleaned = __import__("json").loads(server.memory_clean("release.notes"))
    assert "conflicts_detected" in cleaned

    exported = __import__("json").loads(server.memory_export("json"))
    assert exported[0]["subject"] == "release.notes"

    server.close()


def test_fast_search_mode_preserves_scope_and_conflict_contract_without_explainer_fields(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "fast-search.db"))

    first = app.put_memory(
        "Friday launch is approved.",
        type="semantic",
        scope_type="project",
        scope_id="FASTSCOPE",
        subject="launch.approval",
        source_kind="manual",
    )
    second = app.put_memory(
        "Friday launch is not approved.",
        type="semantic",
        scope_type="project",
        scope_id="FASTSCOPE",
        subject="launch.approval",
        source_kind="manual",
    )
    assert first is not None
    assert second is not None
    app.conflict_manager.scan_conflicts("launch.approval")

    payload = app.search_payload(
        "Friday launch",
        scope_type="project",
        scope_id="FASTSCOPE",
        include_global=False,
        retrieval_mode="fast",
    )

    assert payload
    assert all(item["result_mode"] == "fast" for item in payload)
    assert all(item["memory"]["scope_id"] == "FASTSCOPE" for item in payload)
    assert any(item["conflict_status"] != "none" for item in payload)
    assert all("trust_state" not in item for item in payload)
    assert all("trust_reason" not in item for item in payload)
    assert all("reasons" not in item for item in payload)
    assert all("retrieval_stage" not in item for item in payload)

    app.close()


def test_context_pack_and_simple_recall_surface_trust_states(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "trust-shaping.db"))

    app.put_memory(
        "The launch window is confirmed for Friday.",
        type="semantic",
        scope_type="session",
        scope_id="default",
        subject="launch.window",
        source_kind="manual",
    )
    app.put_memory(
        "The launch window is not confirmed for Friday.",
        type="semantic",
        scope_type="session",
        scope_id="default",
        subject="launch.window",
        source_kind="manual",
    )
    app.conflict_manager.scan_conflicts("launch.window")

    pack = app.search_context_pack(
        "launch window",
        scope_type="session",
        scope_id="default",
        limit=5,
        include_global=False,
    )
    assert any(result["trust_state"] == "conflicting" for result in pack["results"])
    assert pack["trust_counts"]["conflicting"] >= 1

    recall = app.memory_recall("launch window")
    assert "Conflicting:" in recall

    app.close()


def test_public_surface_describes_python_owned_contract(app_env):
    server = AegisMCPServer(db_path=app_env.db_path)

    payload = __import__("json").loads(server.memory_surface())

    assert payload["backend"] == "python"
    assert payload["engine"]["local_first"] is True
    assert "memory_search" in payload["public_contract"]["operations"]
    assert "memory_conflict_prompt" in payload["public_contract"]["operations"]
    assert "memory_conflict_resolve" in payload["public_contract"]["operations"]
    assert "memory_backup_preview" in payload["public_contract"]["operations"]
    assert payload["public_contract"]["owners"]["aegis_py.app"] == "canonical memory semantics and result shapes"
    assert "mandatory cloud service" in payload["public_contract"]["non_goals"]
    assert "graph_native_source_of_truth" in payload["public_contract"]["non_goals"]
    assert "sqlite_link_source_of_truth" in payload["public_contract"]["guarantees"]
    assert payload["service_boundary"]["deployment_model"] == "local_sidecar_process"
    assert payload["service_boundary"]["preferred_transport"] == "mcp_tool_process"

    server.close()


def test_mcp_server_publishes_service_info_and_startup_probe_via_process_flags(tmp_path):
    db_path = tmp_path / "service-boundary.db"
    env = {
        **os.environ,
        "PYTHONPATH": "/home/hali/.openclaw/extensions/memory-aegis-v7",
        "AEGIS_DB_PATH": str(db_path),
    }
    server_module = "/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py"

    service_info = subprocess.run(
        [sys.executable, server_module, "--service-info", "--workspace-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    service_payload = __import__("json").loads(service_info.stdout)
    assert service_payload["service"]["deployment_model"] == "local_sidecar_process"
    assert service_payload["service"]["preferred_transport"] == "mcp_tool_process"
    assert "--tool <tool-name>" in service_payload["startup_contract"]["tool_invocation_pattern"]

    startup_probe = subprocess.run(
        [sys.executable, server_module, "--startup-probe", "--workspace-dir", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    probe_payload = __import__("json").loads(startup_probe.stdout)
    assert probe_payload["backend"] == "python"
    assert probe_payload["ready"] is True
    assert probe_payload["service_state"] == "READY"
    assert probe_payload["health_state"] in {"HEALTHY", "DEGRADED_SYNC"}


def test_scope_policy_defaults_local_only_and_lists_explicit_sync_eligible(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "scope-policy.db"))

    default_policy = app.get_scope_policy(scope_type="project", scope_id="LOCAL1")
    assert default_policy["sync_policy"] == "local_only"
    assert default_policy["sync_state"] == "local"
    assert default_policy["derived"] is True

    updated = app.set_scope_policy(
        "project",
        "SHARED1",
        sync_policy="sync_eligible",
        sync_state="pending_sync",
    )
    assert updated["sync_policy"] == "sync_eligible"
    assert updated["sync_state"] == "pending_sync"
    assert updated["scope_id"] == "SHARED1"

    listed = app.get_scope_policy(sync_policy="sync_eligible")
    assert listed["backend"] == "python"
    assert listed["default_policy"] == "local_only"
    assert len(listed["policies"]) == 1
    assert listed["policies"][0]["scope_id"] == "SHARED1"

    server = AegisMCPServer(db_path=app.db_path)
    inspected = __import__("json").loads(
        server.memory_scope_policy(scope_type="project", scope_id="SHARED1")
    )
    assert inspected["sync_policy"] == "sync_eligible"
    assert inspected["sync_state"] == "pending_sync"

    server.close()
    app.close()


def test_ingest_derives_subject_and_summary_without_overriding_explicit_values(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "extractor-derived-fields.db"))

    derived = app.put_memory(
        "Aegis release doctor validates sync envelopes before import and records evidence for audit review.",
        type="procedural",
        scope_type="project",
        scope_id="EXTRACT1",
        source_kind="manual",
        source_ref="runbook#extractor",
    )
    assert derived is not None
    persisted = app.storage.get_memory(derived.id)
    assert persisted is not None
    assert persisted.subject == "aegis.release.doctor"
    assert persisted.summary == (
        "Aegis release doctor validates sync envelopes before import and records evidence for audit..."
    )

    explicit = app.put_memory(
        "Sync preview reports revision mismatch for older envelopes.",
        type="semantic",
        scope_type="project",
        scope_id="EXTRACT1",
        source_kind="manual",
        source_ref="runbook#explicit",
        subject="workflow.sync",
        summary="Explicit sync summary",
    )
    assert explicit is not None
    explicit_persisted = app.storage.get_memory(explicit.id)
    assert explicit_persisted is not None
    assert explicit_persisted.subject == "workflow.sync"
    assert explicit_persisted.summary == "Explicit sync summary"

    app.close()


def test_ingest_canonicalizes_subjects_but_preserves_explicit_none(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "normalizer-subjects.db"))

    explicit = app.put_memory(
        "Release approvals need a final reviewer before cutover.",
        type="semantic",
        scope_type="project",
        scope_id="NORM1",
        source_kind="manual",
        source_ref="guide#explicit",
        subject=" Release / Approvals  Final ",
    )
    assert explicit is not None
    explicit_persisted = app.storage.get_memory(explicit.id)
    assert explicit_persisted is not None
    assert explicit_persisted.subject == "release.approvals.final"

    derived = app.put_memory(
        "Mammoth migration markers stabilize drought corridor recall.",
        type="semantic",
        scope_type="project",
        scope_id="NORM1",
        source_kind="manual",
        source_ref="guide#derived",
    )
    assert derived is not None
    derived_persisted = app.storage.get_memory(derived.id)
    assert derived_persisted is not None
    assert derived_persisted.subject == "mammoth.migration.markers"

    unlabeled = app.put_memory(
        "Loose note without subject should stay unlabeled for taxonomy cleanup.",
        type="episodic",
        scope_type="project",
        scope_id="NORM1",
        source_kind="manual",
        source_ref="guide#none",
        subject=None,
    )
    assert unlabeled is not None
    unlabeled_persisted = app.storage.get_memory(unlabeled.id)
    assert unlabeled_persisted is not None
    assert unlabeled_persisted.subject is None

    app.close()


def test_ingest_infers_lane_when_type_is_omitted_but_preserves_explicit_type(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "classifier-lanes.db"))

    working = app.put_memory(
        "Temporary note to self for this session: verify the rollout flag.",
        type=None,
        scope_type="project",
        scope_id="CLASS1",
        session_id="S-CLASS",
        source_kind="message",
    )
    assert working is not None
    working_persisted = app.storage.get_memory(working.id)
    assert working_persisted is not None
    assert working_persisted.type == "working"

    procedural = app.put_memory(
        "How to rotate release keys: 1. Generate. 2. Distribute. 3. Verify.",
        type=None,
        scope_type="project",
        scope_id="CLASS1",
        source_kind="manual",
    )
    assert procedural is not None
    procedural_persisted = app.storage.get_memory(procedural.id)
    assert procedural_persisted is not None
    assert procedural_persisted.type == "procedural"

    semantic = app.put_memory(
        "Release readiness requires two reviewer approvals before cutover.",
        type=None,
        scope_type="project",
        scope_id="CLASS1",
        source_kind="manual",
    )
    assert semantic is not None
    semantic_persisted = app.storage.get_memory(semantic.id)
    assert semantic_persisted is not None
    assert semantic_persisted.type == "semantic"

    explicit = app.put_memory(
        "Remember this release anecdote for the audit log.",
        type="episodic",
        scope_type="project",
        scope_id="CLASS1",
        session_id="S-CLASS",
        source_kind="message",
    )
    assert explicit is not None
    explicit_persisted = app.storage.get_memory(explicit.id)
    assert explicit_persisted is not None
    assert explicit_persisted.type == "episodic"

    app.close()


def test_ingest_assigns_write_time_scores_but_preserves_explicit_values(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "scorer-values.db"))

    strong = app.put_memory(
        "How to rotate signing keys: 1. Generate. 2. Distribute. 3. Verify. Operators must confirm.",
        type=None,
        scope_type="project",
        scope_id="SCORE1",
        source_kind="manual",
    )
    assert strong is not None
    strong_persisted = app.storage.get_memory(strong.id)
    assert strong_persisted is not None
    assert strong_persisted.type == "procedural"
    assert strong_persisted.confidence > 0.9
    assert strong_persisted.activation_score > 1.2

    weak = app.put_memory(
        "Small release note.",
        type=None,
        scope_type="project",
        scope_id="SCORE1",
        source_kind="message",
    )
    assert weak is not None
    weak_persisted = app.storage.get_memory(weak.id)
    assert weak_persisted is not None
    assert weak_persisted.activation_score <= strong_persisted.activation_score

    explicit = app.put_memory(
        "Pinned audit reminder.",
        type="episodic",
        scope_type="project",
        scope_id="SCORE1",
        source_kind="manual",
        confidence=0.61,
        activation_score=1.37,
    )
    assert explicit is not None
    explicit_persisted = app.storage.get_memory(explicit.id)
    assert explicit_persisted is not None
    assert explicit_persisted.confidence == 0.61
    assert explicit_persisted.activation_score == 1.37

    app.close()


def test_context_pack_enforces_stage_budgets_and_reports_stage_counts(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "navigator-stage-budgets.db"))

    seed = app.put_memory(
        "Release anchors require migration markers before cutover.",
        type="semantic",
        scope_type="project",
        scope_id="NAV1",
        subject="release.anchor",
        source_kind="manual",
        source_ref="nav#seed",
    )
    assert seed is not None

    for index in range(4):
        app.put_memory(
            f"Linked release anchor procedure {index} documents the same migration markers.",
            type="procedural",
            scope_type="project",
            scope_id="NAV1",
            subject="release.anchor",
            source_kind="manual",
            source_ref=f"nav#link-{index}",
        )

    pack = app.search_context_pack(
        "migration markers",
        scope_type="project",
        scope_id="NAV1",
        limit=10,
    )
    stage_counts = pack["counts"]["stage_counts"]
    assert pack["counts"]["lexical_hits"] >= 1
    assert stage_counts["link_expansion"] <= 2
    assert stage_counts["multi_hop_link_expansion"] <= 1
    assert stage_counts["entity_expansion"] <= 2
    assert stage_counts["subject_expansion"] <= 2
    assert stage_counts["lexical"] == pack["counts"]["lexical_hits"]
    assert pack["results"][0]["retrieval_stage"] == "lexical"

    app.close()


def test_guardian_scope_contracts_surface_global_fallback_and_boundary_metadata(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "guardian-scope.db"))

    local = app.put_memory(
        "Project release checklist for NAV scope.",
        type="semantic",
        scope_type="project",
        scope_id="GUARD1",
        subject="release.guard",
        source_kind="manual",
    )
    global_memory = app.put_memory(
        "Global release checklist for all projects.",
        type="semantic",
        scope_type="global",
        scope_id="global-default",
        subject="release.guard",
        source_kind="manual",
    )
    assert local is not None and global_memory is not None

    payload = app.search_payload(
        "release checklist",
        scope_id="GUARD1",
        scope_type="project",
        include_global=True,
    )
    global_results = [item for item in payload if item["memory"]["scope_type"] == "global"]
    assert len(global_results) == 1
    assert "global_fallback" in global_results[0]["reasons"]

    pack = app.search_context_pack(
        "release checklist",
        scope_id="GUARD1",
        scope_type="project",
        include_global=True,
    )
    assert pack["boundary"]["requested_scope"]["scope_type"] == "project"
    assert pack["boundary"]["requested_scope"]["scope_id"] == "GUARD1"
    assert pack["boundary"]["exact_scope_locked"] is True
    assert pack["boundary"]["global_fallback_enabled"] is True
    assert pack["boundary"]["cross_scope_expansion_allowed"] is False

    app.close()


def test_guardian_rejects_partial_scope_inputs_but_accepts_valid_pairs(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "guardian-partial-scope.db"))

    server.memory_store(
        "semantic",
        "Guardian scope retrieval stays explicit.",
        "guardian.scope",
        scope_type="project",
        scope_id="GPAIR1",
    )

    valid = __import__("json").loads(
        server.memory_search("guardian scope", scope_type="project", scope_id="GPAIR1")
    )
    assert len(valid) == 1

    defaulted = __import__("json").loads(server.memory_search("guardian scope"))
    assert isinstance(defaulted, list)

    with pytest.raises(ValueError, match="scope_type and scope_id must both be provided for retrieval scopes"):
        server.memory_search("guardian scope", scope_type="project")

    with pytest.raises(ValueError, match="scope_type and scope_id must both be provided for retrieval scopes"):
        server.memory_context_pack("guardian scope", scope_id="GPAIR1")

    server.close()


def test_subject_expansion_seeds_only_from_lexical_hits(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "navigator-lexical-subjects.db"))

    seed = app.put_memory(
        "KRONOS routes require migration markers.",
        type="semantic",
        scope_type="project",
        scope_id="NAVLEX1",
        subject="kronos.routes",
        source_kind="manual",
    )
    entity_neighbor = app.put_memory(
        "KRONOS governs hidden atlas corridors.",
        type="semantic",
        scope_type="project",
        scope_id="NAVLEX1",
        subject="atlas.hidden",
        source_kind="manual",
    )
    hidden_peer = app.put_memory(
        "Atlas hidden route archive should not appear by subject cascade alone.",
        type="semantic",
        scope_type="project",
        scope_id="NAVLEX1",
        subject="atlas.hidden",
        source_kind="manual",
    )
    lexical_peer = app.put_memory(
        "Secondary KRONOS route archive for the same migration markers.",
        type="semantic",
        scope_type="project",
        scope_id="NAVLEX1",
        subject="kronos.routes",
        source_kind="manual",
    )
    assert seed and entity_neighbor and hidden_peer and lexical_peer

    pack = app.search_context_pack(
        "KRONOS routes",
        scope_type="project",
        scope_id="NAVLEX1",
        limit=8,
    )
    result_ids = {result["memory"]["id"] for result in pack["results"]}
    assert lexical_peer.id in result_ids
    assert entity_neighbor.id in result_ids
    assert hidden_peer.id not in result_ids

    app.close()


def test_context_pack_is_lexical_first_and_marks_subject_expansion(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "context-pack.db"))

    app.put_memory(
        "Mammoth routes depend on preserved migration markers.",
        type="semantic",
        scope_type="project",
        scope_id="MAMMOTH1",
        subject="mammoth.routes",
        source_kind="manual",
        source_ref="field-guide#routes",
    )
    app.put_memory(
        "Water memory helps the herd return to drought-safe corridors.",
        type="semantic",
        scope_type="project",
        scope_id="MAMMOTH1",
        subject="mammoth.routes",
        source_kind="manual",
        source_ref="field-guide#water",
    )

    pack = app.search_context_pack(
        "migration markers",
        scope_type="project",
        scope_id="MAMMOTH1",
        limit=5,
    )
    assert pack["backend"] == "python"
    assert pack["strategy"]["name"] == "mammoth_lexical_first"
    assert pack["counts"]["lexical_hits"] >= 1
    assert pack["counts"]["expanded_hits"] >= 1
    assert pack["results"][0]["retrieval_stage"] == "lexical"
    assert any(
        result["retrieval_stage"] in {"link_expansion", "subject_expansion"}
        for result in pack["results"]
    )
    assert any("relationship_expansion" in result["reasons"] for result in pack["results"])

    server = AegisMCPServer(db_path=app.db_path)
    payload = __import__("json").loads(
        server.memory_context_pack("migration markers", scope_type="project", scope_id="MAMMOTH1")
    )
    assert payload["counts"]["expanded_hits"] >= 1

    server.close()
    app.close()


def test_weaver_link_store_neighbors_and_visualization(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver.db"))
    seed = app.put_memory(
        "Elephants use migration landmarks to cross dry seasons.",
        type="semantic",
        scope_type="project",
        scope_id="WEAVER1",
        subject="elephant.routes",
        source_kind="manual",
        source_ref="field#seed",
    )
    neighbor = app.put_memory(
        "Ancient wells become fallback waypoints during drought.",
        type="semantic",
        scope_type="project",
        scope_id="WEAVER1",
        subject="elephant.water",
        source_kind="manual",
        source_ref="field#neighbor",
    )
    assert seed is not None and neighbor is not None

    linked = app.link_memories(seed.id, neighbor.id, link_type="supports", weight=0.8)
    assert linked["link"]["link_type"] == "supports"
    assert linked["link"]["scope_id"] == "WEAVER1"

    neighbors = app.memory_neighbors(seed.id, limit=5)
    assert neighbors["neighbors"][0]["memory"]["id"] == neighbor.id
    assert neighbors["neighbors"][0]["link"]["link_type"] == "supports"

    pack = app.search_context_pack(
        "migration landmarks",
        scope_type="project",
        scope_id="WEAVER1",
        limit=5,
    )
    assert pack["results"][0]["retrieval_stage"] == "lexical"
    link_results = [result for result in pack["results"] if result["retrieval_stage"] == "link_expansion"]
    assert link_results
    assert any("explicit_link_neighbor" in result["reasons"] for result in link_results)
    assert link_results[0]["relation_via_link_type"] == "supports"
    assert link_results[0]["relation_via_memory_id"] == seed.id
    assert link_results[0]["relation_via_link_metadata"]["weight"] == 0.8

    graph = app.visualize(limit=10, include_analysis=True)
    assert graph["graph_boundary"]["source_of_truth"] == "sqlite_memory_links"
    assert graph["graph_boundary"]["authoritative_analysis"] is False
    assert graph["analysis"]["analysis_mode"] == "local_only"
    assert graph["analysis"]["authoritative"] is False
    assert any(link["type"] == "supports" and link["status"] == "explicit_link" for link in graph["links"])

    server = AegisMCPServer(db_path=app.db_path)
    server_link = __import__("json").loads(server.memory_link_neighbors(seed.id, limit=5))
    assert server_link["neighbors"][0]["memory"]["id"] == neighbor.id
    server_pack = __import__("json").loads(
        server.memory_context_pack("migration landmarks", scope_type="project", scope_id="WEAVER1")
    )
    assert "explicit_link_expansion" in server_pack["strategy"]["steps"]
    server_graph = __import__("json").loads(server.memory_visualize(10, include_analysis=True))
    assert server_graph["graph_boundary"]["source_of_truth"] == "sqlite_memory_links"
    assert server_graph["analysis"]["largest_component"] >= 1
    server.close()
    app.close()


def test_weaver_bounded_multi_hop_expansion(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-multihop.db"))
    a = app.put_memory(
        "Alpha route anchor for the herd.",
        type="semantic",
        scope_type="project",
        scope_id="HOPS1",
        subject="herd.alpha",
        source_kind="manual",
        source_ref="hop#a",
    )
    b = app.put_memory(
        "Beta waypoint extends the alpha route.",
        type="semantic",
        scope_type="project",
        scope_id="HOPS1",
        subject="herd.beta",
        source_kind="manual",
        source_ref="hop#b",
    )
    c = app.put_memory(
        "Gamma refuge is the third landmark.",
        type="semantic",
        scope_type="project",
        scope_id="HOPS1",
        subject="herd.gamma",
        source_kind="manual",
        source_ref="hop#c",
    )
    assert a is not None and b is not None and c is not None
    app.link_memories(a.id, b.id, link_type="extends", weight=0.9)
    app.link_memories(b.id, c.id, link_type="extends", weight=0.7)

    pack = app.search_context_pack(
        "Alpha route anchor",
        scope_type="project",
        scope_id="HOPS1",
        limit=5,
    )
    assert "bounded_multi_hop_link_expansion" in pack["strategy"]["steps"]
    multi_hop = [result for result in pack["results"] if result["retrieval_stage"] == "multi_hop_link_expansion"]
    assert multi_hop
    assert multi_hop[0]["relation_via_hops"] == 2
    assert multi_hop[0]["relation_via_link_type"] == "extends"
    assert "link_hops:2" in multi_hop[0]["reasons"]
    assert multi_hop[0]["memory"]["id"] == c.id

    app.close()


def test_weaver_link_reranking_prefers_nearer_and_stronger_links(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-rerank.db"))
    seed = app.put_memory(
        "KRONOS anchor memory.",
        type="semantic",
        scope_type="project",
        scope_id="RERANK1",
        subject="release.anchor",
    )
    weak = app.put_memory(
        "Same subject weak relation memory.",
        type="semantic",
        scope_type="project",
        scope_id="RERANK1",
        subject="release.anchor",
    )
    strong = app.put_memory(
        "Procedure explains the release facts.",
        type="procedural",
        scope_type="project",
        scope_id="RERANK1",
        subject="release.anchor",
    )
    tail = app.put_memory(
        "Farther second-hop release detail.",
        type="semantic",
        scope_type="project",
        scope_id="RERANK1",
        subject="release.tail",
    )
    assert seed and weak and strong and tail

    app.link_memories(seed.id, weak.id, link_type="same_subject", weight=0.6)
    app.link_memories(seed.id, strong.id, link_type="procedural_supports_semantic", weight=0.6)
    app.link_memories(strong.id, tail.id, link_type="extends", weight=0.9)

    pack = app.search_context_pack(
        "KRONOS anchor",
        scope_type="project",
        scope_id="RERANK1",
        limit=6,
    )
    by_id = {result["memory"]["id"]: result for result in pack["results"]}
    assert by_id[strong.id]["score"] > by_id[weak.id]["score"]
    assert by_id[strong.id]["score"] > by_id[tail.id]["score"]
    assert "link_score_reranked" in by_id[strong.id]["reasons"]
    assert by_id[tail.id]["relation_via_hops"] == 2

    app.close()


def test_entity_structure_lite_extracts_entities_and_expands_context(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "entity-lite.db"))
    seed = app.put_memory(
        "KRONOS coordinates release cutover for Project Atlas.",
        type="semantic",
        scope_type="project",
        scope_id="ENTITY1",
        subject="ops.cutover",
    )
    peer = app.put_memory(
        "Atlas rollback notes depend on KRONOS timing windows.",
        type="semantic",
        scope_type="project",
        scope_id="ENTITY1",
        subject="ops.rollback",
    )
    assert seed is not None and peer is not None
    persisted = app.storage.get_memory(seed.id)
    assert persisted is not None
    assert "kronos" in (persisted.metadata or {}).get("entities", [])

    pack = app.search_context_pack(
        "KRONOS coordinates",
        scope_type="project",
        scope_id="ENTITY1",
        limit=6,
    )
    assert "entity_structure_expansion" in pack["strategy"]["steps"]
    entity_results = [result for result in pack["results"] if result["retrieval_stage"] == "entity_expansion"]
    assert entity_results
    assert entity_results[0]["memory"]["id"] == peer.id
    assert "entity_expansion" in entity_results[0]["reasons"]
    assert "entities" in entity_results[0]["relation_via_link_metadata"]

    app.close()


def test_weaver_rejects_cross_scope_links(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-scope.db"))
    left = app.put_memory("Left scope memory", scope_type="project", scope_id="A", subject="left")
    right = app.put_memory("Right scope memory", scope_type="project", scope_id="B", subject="right")
    assert left is not None and right is not None

    with pytest.raises(ValueError, match="Cross-scope"):
        app.link_memories(left.id, right.id, link_type="supports")

    app.close()


def test_weaver_auto_links_same_subject_on_ingest(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-auto.db"))

    first = app.put_memory(
        "First route marker memory.",
        type="semantic",
        scope_type="project",
        scope_id="AUTO1",
        subject="mammoth.route",
    )
    second = app.put_memory(
        "Second route marker memory.",
        type="semantic",
        scope_type="project",
        scope_id="AUTO1",
        subject="mammoth.route",
    )
    other_scope = app.put_memory(
        "Same subject but different scope.",
        type="semantic",
        scope_type="project",
        scope_id="AUTO2",
        subject="mammoth.route",
    )
    no_subject = app.put_memory(
        "Subjectless memory should not auto-link.",
        type="semantic",
        scope_type="project",
        scope_id="AUTO1",
    )
    assert first is not None and second is not None and other_scope is not None and no_subject is not None

    neighbors = app.memory_neighbors(second.id, limit=10)
    assert any(
        item["memory"]["id"] == first.id and item["link"]["link_type"] == "same_subject"
        for item in neighbors["neighbors"]
    )
    assert not any(item["memory"]["id"] == other_scope.id for item in neighbors["neighbors"])
    assert not any(item["memory"]["id"] == no_subject.id for item in neighbors["neighbors"])

    app.close()


def test_rebuild_backfills_same_subject_links(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-rebuild.db"))
    first = app.put_memory(
        "Backfill seed.",
        type="semantic",
        scope_type="project",
        scope_id="RB1",
        subject="rebuilt.topic",
    )
    second = app.put_memory(
        "Backfill neighbor.",
        type="semantic",
        scope_type="project",
        scope_id="RB1",
        subject="rebuilt.topic",
    )
    assert first is not None and second is not None

    app.storage.execute("DELETE FROM memory_links WHERE link_type = ?", ("same_subject",))

    rebuilt = app.rebuild()
    assert rebuilt["same_subject_links_added"] >= 1
    assert rebuilt["same_subject_links_after"] >= 1

    neighbors = app.memory_neighbors(first.id, limit=10)
    assert any(item["memory"]["id"] == second.id for item in neighbors["neighbors"])

    app.close()


def test_rebuild_hardens_missing_derived_fields_before_same_subject_backfill(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "axolotl-derived-rebuild.db"))

    first = Memory(
        id=str(uuid4()),
        type="semantic",
        scope_type="project",
        scope_id="AXO1",
        content="Aegis release doctor validates sync envelopes before import.",
        source_kind="manual",
        subject=None,
        summary=None,
    )
    second = Memory(
        id=str(uuid4()),
        type="semantic",
        scope_type="project",
        scope_id="AXO1",
        content="Aegis release doctor records evidence for audit review.",
        source_kind="manual",
        subject=None,
        summary=None,
    )
    explicit = Memory(
        id=str(uuid4()),
        type="semantic",
        scope_type="project",
        scope_id="AXO1",
        content="Explicit subject should survive rebuild hardening.",
        source_kind="manual",
        subject="workflow.explicit",
        summary=None,
    )
    assert app.storage.put_memory(first) is True
    assert app.storage.put_memory(second) is True
    assert app.storage.put_memory(explicit) is True

    rebuilt = app.rebuild()
    assert rebuilt["derived_fields_hardened"] == 3
    assert rebuilt["evidence_backfilled"] == 0
    assert rebuilt["same_subject_links_added"] >= 1

    first_persisted = app.storage.get_memory(first.id)
    second_persisted = app.storage.get_memory(second.id)
    explicit_persisted = app.storage.get_memory(explicit.id)
    assert first_persisted is not None and second_persisted is not None and explicit_persisted is not None
    assert first_persisted.subject == "aegis.release.doctor"
    assert second_persisted.subject == "aegis.release.doctor"
    assert first_persisted.summary == "Aegis release doctor validates sync envelopes before import."
    assert second_persisted.summary == "Aegis release doctor records evidence for audit review."
    assert explicit_persisted.subject == "workflow.explicit"
    assert explicit_persisted.summary == "Explicit subject should survive rebuild hardening."

    neighbors = app.memory_neighbors(first.id, limit=10)
    assert any(
        item["memory"]["id"] == second.id and item["link"]["link_type"] == "same_subject"
        for item in neighbors["neighbors"]
    )

    app.close()


def test_rebuild_backfills_missing_evidence_for_legacy_memories(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "legacy-evidence-rebuild.db"))

    app.storage.execute("DROP TABLE evidence_events")
    app.storage.execute("PRAGMA user_version = 1")
    app.close()

    app = AegisApp(db_path=str(tmp_path / "legacy-evidence-rebuild.db"))
    legacy = Memory(
        id=str(uuid4()),
        type="semantic",
        scope_type="project",
        scope_id="LEGACY1",
        content="Legacy memory predates evidence linkage.",
        source_kind="manual",
        source_ref="legacy#memory",
        metadata={},
    )
    assert app.storage.put_memory(legacy) is True

    app.storage.execute(
        "DELETE FROM evidence_events WHERE memory_id = ?",
        (legacy.id,),
    )
    app.storage.execute(
        "UPDATE memories SET metadata_json = ? WHERE id = ?",
        ("{}", legacy.id),
    )

    rebuilt = app.rebuild()
    persisted = app.storage.get_memory(legacy.id)
    evidence_rows = app.storage.list_evidence_events_for_memory(legacy.id)

    assert rebuilt["evidence_backfilled"] == 1
    assert persisted is not None
    assert persisted.metadata["evidence"]["event_id"] == evidence_rows[0].id
    assert len(evidence_rows) == 1
    assert evidence_rows[0].raw_content == legacy.content

    app.close()


def test_weaver_auto_links_procedural_and_semantic_same_subject(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-typed-auto.db"))
    semantic = app.put_memory(
        "Release facts: build artifacts are signed.",
        type="semantic",
        scope_type="project",
        scope_id="TYPE1",
        subject="release.process",
    )
    procedural = app.put_memory(
        "Release procedure: build, sign, publish.",
        type="procedural",
        scope_type="project",
        scope_id="TYPE1",
        subject="release.process",
    )
    assert semantic is not None and procedural is not None

    neighbors = app.memory_neighbors(procedural.id, limit=10)
    assert any(
        item["memory"]["id"] == semantic.id
        and item["link"]["link_type"] == "procedural_supports_semantic"
        for item in neighbors["neighbors"]
    )

    app.close()


def test_rebuild_backfills_procedural_semantic_links(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "weaver-typed-rebuild.db"))
    semantic = app.put_memory(
        "Semantic fact about deployment.",
        type="semantic",
        scope_type="project",
        scope_id="TYPE2",
        subject="deploy.flow",
    )
    procedural = app.put_memory(
        "Procedural steps for deployment.",
        type="procedural",
        scope_type="project",
        scope_id="TYPE2",
        subject="deploy.flow",
    )
    assert semantic is not None and procedural is not None

    app.storage.execute(
        "DELETE FROM memory_links WHERE link_type = ?",
        ("procedural_supports_semantic",),
    )

    rebuilt = app.rebuild()
    assert rebuilt["procedural_semantic_links_added"] >= 1
    assert rebuilt["procedural_semantic_links_after"] >= 1

    neighbors = app.memory_neighbors(procedural.id, limit=10)
    assert any(
        item["memory"]["id"] == semantic.id
        and item["link"]["link_type"] == "procedural_supports_semantic"
        for item in neighbors["neighbors"]
    )

    app.close()


def test_python_cli_surface_store_search_and_context_pack(tmp_path):
    db_path = tmp_path / "cli-runtime.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    surface = subprocess.run(
        [*cli, "surface"],
        check=True,
        capture_output=True,
        text=True,
    )
    surface_payload = __import__("json").loads(surface.stdout)
    assert surface_payload["backend"] == "python"
    assert "memory_context_pack" in surface_payload["public_contract"]["operations"]

    stored = subprocess.run(
        [
            *cli,
            "store",
            "--content", "CLI can store agent memory.",
            "--type", "semantic",
            "--scope-type", "project",
            "--scope-id", "CLI1",
            "--subject", "cli.memory",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stored_payload = __import__("json").loads(stored.stdout)
    assert stored_payload["stored"] is True

    searched = subprocess.run(
        [
            *cli,
            "search",
            "--query", "store agent memory",
            "--scope-type", "project",
            "--scope-id", "CLI1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    searched_payload = __import__("json").loads(searched.stdout)
    assert len(searched_payload) == 1
    assert searched_payload[0]["memory"]["scope_id"] == "CLI1"

    context = subprocess.run(
        [
            *cli,
            "context-pack",
            "--query", "store agent memory",
            "--scope-type", "project",
            "--scope-id", "CLI1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    context_payload = __import__("json").loads(context.stdout)
    assert context_payload["strategy"]["name"] == "mammoth_lexical_first"


def test_python_cli_backup_preview_and_scope_policy(tmp_path):
    db_path = tmp_path / "cli-ops.db"
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    subprocess.run(
        [
            *cli,
            "store",
            "--content", "CLI backup test memory.",
            "--type", "semantic",
            "--scope-type", "project",
            "--scope-id", "CLI2",
            "--subject", "cli.backup",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    backup = subprocess.run(
        [
            *cli,
            "backup-upload",
            "--mode", "snapshot",
            "--workspace-dir", str(workspace_dir),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    backup_payload = __import__("json").loads(backup.stdout)
    assert backup_payload["mode"] == "snapshot"

    preview = subprocess.run(
        [
            *cli,
            "backup-preview",
            "--snapshot-path", backup_payload["path"],
            "--scope-type", "project",
            "--scope-id", "CLI2",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    preview_payload = __import__("json").loads(preview.stdout)
    assert preview_payload["dry_run"] is True
    assert preview_payload["scope_filter"]["scope_id"] == "CLI2"

    policy = subprocess.run(
        [
            *cli,
            "scope-policy",
            "--scope-type", "project",
            "--scope-id", "CLI2",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    policy_payload = __import__("json").loads(policy.stdout)
    assert policy_payload["sync_policy"] == "local_only"


def test_python_cli_link_store_and_neighbors(tmp_path):
    db_path = tmp_path / "cli-links.db"
    cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(db_path)]

    left = subprocess.run(
        [*cli, "store", "--content", "CLI seed memory", "--scope-type", "project", "--scope-id", "CLI3", "--subject", "cli.seed"],
        check=True,
        capture_output=True,
        text=True,
    )
    right = subprocess.run(
        [*cli, "store", "--content", "CLI neighbor memory", "--scope-type", "project", "--scope-id", "CLI3", "--subject", "cli.neighbor"],
        check=True,
        capture_output=True,
        text=True,
    )
    left_id = __import__("json").loads(left.stdout)["memory_id"]
    right_id = __import__("json").loads(right.stdout)["memory_id"]

    link = subprocess.run(
        [*cli, "link-store", "--source-id", left_id, "--target-id", right_id, "--link-type", "supports", "--weight", "0.7"],
        check=True,
        capture_output=True,
        text=True,
    )
    link_payload = __import__("json").loads(link.stdout)
    assert link_payload["link"]["link_type"] == "supports"

    neighbors = subprocess.run(
        [*cli, "link-neighbors", "--memory-id", left_id],
        check=True,
        capture_output=True,
        text=True,
    )
    neighbors_payload = __import__("json").loads(neighbors.stdout)
    assert neighbors_payload["neighbors"][0]["memory"]["id"] == right_id


def test_hybrid_sync_protocol_lite_export_preview_import(tmp_path):
    workspace = tmp_path / "sync-workspace"
    workspace.mkdir()

    source = AegisApp(db_path=str(tmp_path / "sync-source.db"))
    source.set_scope_policy("project", "SYNC1", sync_policy="sync_eligible", sync_state="local")
    source.put_memory(
        "Portable sync memory.",
        type="semantic",
        scope_type="project",
        scope_id="SYNC1",
        subject="sync.demo",
    )
    envelope = source.export_sync_envelope(scope_type="project", scope_id="SYNC1", workspace_dir=str(workspace))
    assert envelope["records"] == 1
    assert envelope["scope_revision"] >= 1
    source.close()

    target = AegisApp(db_path=str(tmp_path / "sync-target.db"))
    target.set_scope_policy("project", "SYNC1", sync_policy="sync_eligible", sync_state="local")
    target.put_memory(
        "Target-only local memory.",
        type="semantic",
        scope_type="project",
        scope_id="SYNC1",
        subject="sync.local",
    )
    preview = target.preview_sync_envelope(envelope["path"])
    assert preview["dry_run"] is True
    assert preview["new_records"] == 1
    assert preview["reconcile"]["incoming_new"] == 1
    assert preview["reconcile"]["local_only"] == 1
    assert preview["incoming_scope_revision"]["revision"] >= 1
    assert "local_scope_revision" in preview

    imported = target.import_sync_envelope(envelope["path"])
    assert imported["imported"] is True
    assert imported["inserted_records"] == 1
    assert imported["local_scope_revision_after"]["revision"] >= imported["local_scope_revision_before"]["revision"]
    synced = target.search("Portable sync memory", scope_type="project", scope_id="SYNC1")
    assert len(synced) == 1
    target.close()


def test_python_cli_sync_export_preview_import(tmp_path):
    workspace = tmp_path / "cli-sync-workspace"
    workspace.mkdir()
    source_db = tmp_path / "cli-sync-source.db"
    target_db = tmp_path / "cli-sync-target.db"

    source_cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(source_db)]
    target_cli = [sys.executable, "-m", "aegis_py.cli", "--db-path", str(target_db)]

    source_app = AegisApp(db_path=str(source_db))
    source_app.set_scope_policy("project", "SYNCCLI", sync_policy="sync_eligible", sync_state="local")
    source_app.put_memory(
        "CLI sync envelope memory.",
        type="semantic",
        scope_type="project",
        scope_id="SYNCCLI",
        subject="sync.cli",
    )
    source_app.close()

    target_app = AegisApp(db_path=str(target_db))
    target_app.set_scope_policy("project", "SYNCCLI", sync_policy="sync_eligible", sync_state="local")
    target_app.close()

    exported = subprocess.run(
        [
            *source_cli,
            "sync-export",
            "--scope-type", "project",
            "--scope-id", "SYNCCLI",
            "--workspace-dir", str(workspace),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    exported_payload = __import__("json").loads(exported.stdout)
    assert exported_payload["records"] == 1
    assert exported_payload["scope_revision"] >= 1

    preview = subprocess.run(
        [*target_cli, "sync-preview", "--envelope-path", exported_payload["path"]],
        check=True,
        capture_output=True,
        text=True,
    )
    preview_payload = __import__("json").loads(preview.stdout)
    assert preview_payload["new_records"] == 1
    assert "reconcile" in preview_payload
    assert "incoming_scope_revision" in preview_payload

    imported = subprocess.run(
        [*target_cli, "sync-import", "--envelope-path", exported_payload["path"]],
        check=True,
        capture_output=True,
        text=True,
    )
    imported_payload = __import__("json").loads(imported.stdout)
    assert imported_payload["records"] == 1
    assert "inserted_records" in imported_payload
    assert "local_scope_revision_after" in imported_payload


def test_mcp_empty_search_and_unknown_tool_return_json_shapes(app_env):
    server = AegisMCPServer(db_path=app_env.db_path)

    empty_payload = __import__("json").loads(
        server.memory_search("missing-term", scope_type="project", scope_id="P404")
    )
    assert empty_payload == []

    error_payload = __import__("json").loads(server.run_tool("unknown_tool", {}))
    assert error_payload["error"] == "tool_not_found"
    assert error_payload["tool"] == "unknown_tool"

    server.close()


def test_mcp_direct_tool_alias_accepts_memory_stats(app_env):
    server = AegisMCPServer(db_path=app_env.db_path)

    stored = server.memory_store(
        "semantic",
        "Aegis stats alias should match the public memory_stats name.",
        "runtime.stats",
        scope_type="project",
        scope_id="STATS1",
    )
    assert "Stored semantic memory" in stored

    status_payload = __import__("json").loads(server.run_tool("memory_stats", {}))
    assert status_payload["counts"]["active"] == 1
    assert status_payload["health_state"] == "HEALTHY"

    server.close()


def test_runtime_surfaces_honor_env_backed_local_db_path(tmp_path, monkeypatch):
    db_path = tmp_path / "env-backed-aegis.db"
    monkeypatch.setenv("AEGIS_DB_PATH", str(db_path))

    app = AegisApp()
    server = AegisMCPServer()

    stored = server.memory_store(
        "semantic",
        "Environment-backed DB path should bootstrap local runtime surfaces.",
        "runtime.env",
        scope_type="project",
        scope_id="ENV1",
    )
    assert "Stored semantic memory" in stored

    assert app.db_path == str(db_path)
    assert server.app.db_path == str(db_path)

    server.close()
    app.close()


def test_python_runtime_smoke_flow_covers_store_search_status_clean_and_profile(tmp_path):
    db_path = tmp_path / "python-runtime-smoke.db"
    server = AegisMCPServer(db_path=str(db_path))

    stored = server.memory_store(
        "semantic",
        "The release checklist requires a Python-first validation pass.",
        "release.checklist",
        scope_type="project",
        scope_id="PYONLY",
        source_kind="manual",
        source_ref="specs/005",
    )
    assert "Stored semantic memory" in stored

    searched = __import__("json").loads(
        server.memory_search("Python-first validation", scope_type="project", scope_id="PYONLY")
    )
    assert len(searched) == 1
    assert searched[0]["memory"]["scope_id"] == "PYONLY"
    assert searched[0]["memory"]["source_ref"] == "specs/005"
    assert "scope_exact_match" in searched[0]["reasons"]

    status = __import__("json").loads(server.memory_status())
    assert status["counts"]["active"] == 1
    assert status["db_path"] == str(db_path)

    cleaned = __import__("json").loads(server.memory_clean("release.checklist"))
    assert "conflicts_detected" in cleaned

    profile = server.memory_profile("PYONLY", "project")
    assert "## Memory Profile: PYONLY" in profile
    assert "release checklist" in profile.lower()

    server.close()


def test_python_runtime_memory_get_reads_citation_and_workspace_file(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    note_path = workspace_dir / "MEMORY.md"
    note_path.write_text("line one\nline two\nline three\n", encoding="utf-8")

    server = AegisMCPServer(db_path=str(tmp_path / "memory-get.db"))
    stored = server.memory_store(
        "semantic",
        "Python runtime can read memory citations directly.",
        "runtime.read",
        scope_type="project",
        scope_id="GET1",
        source_ref="docs/runtime#read",
    )
    memory_id = stored.split()[-1].rstrip(".")

    citation = __import__("json").loads(
        server.memory_get(f"aegis://semantic/{memory_id}", workspace_dir=str(workspace_dir))
    )
    assert citation["memory_id"] == memory_id
    assert "read memory citations" in citation["text"].lower()

    fragment = __import__("json").loads(
        server.memory_get("MEMORY.md", from_line=1, lines=1, workspace_dir=str(workspace_dir))
    )
    assert fragment["text"] == "line two"
    assert fragment["path"] == "MEMORY.md"

    server.close()


def test_python_runtime_backup_export_and_restore_flow(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "backup-runtime.db"
    server = AegisMCPServer(db_path=str(db_path))

    server.memory_store(
        "semantic",
        "Backup restore keeps Python-owned memories available.",
        "runtime.backup",
        scope_type="project",
        scope_id="BACKUP1",
    )

    exported = __import__("json").loads(server.memory_backup_upload("export", workspace_dir=str(workspace_dir)))
    assert exported["mode"] == "export"

    snapshot = __import__("json").loads(server.memory_backup_upload("snapshot", workspace_dir=str(workspace_dir)))
    assert snapshot["mode"] == "snapshot"

    server.memory_store(
        "semantic",
        "This memory should disappear after snapshot restore.",
        "runtime.backup.extra",
        scope_type="project",
        scope_id="BACKUP1",
    )

    restored = __import__("json").loads(server.memory_backup_download(snapshot["path"]))
    assert restored["restored"] is True

    after_restore = __import__("json").loads(
        server.memory_search("disappear after snapshot restore", scope_type="project", scope_id="BACKUP1")
    )
    assert after_restore == []

    from_export = __import__("json").loads(server.memory_backup_download(exported["path"]))
    assert from_export["restored"] is True

    after_export_restore = __import__("json").loads(
        server.memory_search("keeps Python-owned memories", scope_type="project", scope_id="BACKUP1")
    )
    assert len(after_export_restore) == 1

    server.close()


def test_backup_manifest_listing_and_restore_preview_do_not_mutate_live_db(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "backup-preview.db"
    server = AegisMCPServer(db_path=str(db_path))

    server.memory_store(
        "semantic",
        "Previewable backups should carry manifest metadata.",
        "backup.manifest",
        scope_type="project",
        scope_id="BKP1",
    )

    snapshot = __import__("json").loads(server.memory_backup_upload("snapshot", workspace_dir=str(workspace_dir)))
    export = __import__("json").loads(server.memory_backup_upload("export", workspace_dir=str(workspace_dir)))

    assert snapshot["manifest_path"].endswith(".manifest.json")
    assert export["manifest_path"].endswith(".manifest.json")

    listed = __import__("json").loads(server.memory_backup_list(str(workspace_dir)))
    assert listed["backend"] == "python"
    assert len(listed["backups"]) >= 2
    assert listed["backups"][0]["artifact_path"]
    assert listed["backups"][0]["counts"]["active"] >= 1

    server.memory_store(
        "semantic",
        "This extra memory should survive dry-run preview untouched.",
        "backup.preview.extra",
        scope_type="project",
        scope_id="BKP1",
    )

    before = __import__("json").loads(
        server.memory_search("survive dry-run preview", scope_type="project", scope_id="BKP1")
    )
    preview = __import__("json").loads(server.memory_backup_preview(snapshot["path"]))
    after = __import__("json").loads(
        server.memory_search("survive dry-run preview", scope_type="project", scope_id="BKP1")
    )

    assert preview["dry_run"] is True
    assert preview["mode"] == "snapshot"
    assert preview["manifest"]["artifact_path"] == snapshot["path"]
    assert len(before) == 1
    assert len(after) == 1

    server.close()


def test_scoped_backup_preview_and_restore_replace_only_requested_scope(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "scoped-restore.db"
    server = AegisMCPServer(db_path=str(db_path))

    server.memory_store(
        "semantic",
        "Alpha baseline memory survives scoped restore.",
        "restore.alpha",
        scope_type="project",
        scope_id="ALPHA",
    )
    server.memory_store(
        "semantic",
        "Beta baseline memory must remain untouched.",
        "restore.beta",
        scope_type="project",
        scope_id="BETA",
    )

    snapshot = __import__("json").loads(server.memory_backup_upload("snapshot", workspace_dir=str(workspace_dir)))
    export = __import__("json").loads(server.memory_backup_upload("export", workspace_dir=str(workspace_dir)))

    server.memory_store(
        "semantic",
        "Alpha mutation should be removed by scoped restore.",
        "restore.alpha",
        scope_type="project",
        scope_id="ALPHA",
    )
    server.memory_store(
        "semantic",
        "Beta mutation should survive scoped restore.",
        "restore.beta",
        scope_type="project",
        scope_id="BETA",
    )

    scoped_preview = __import__("json").loads(
        server.memory_backup_preview(snapshot["path"], scope_type="project", scope_id="ALPHA")
    )
    assert scoped_preview["scope_filter"] == {"scope_type": "project", "scope_id": "ALPHA"}
    assert scoped_preview["preview"]["restore_strategy"] == "replace_scope"
    assert scoped_preview["preview"]["records"] == 1
    assert scoped_preview["current_scope_counts"]["active"] == 2

    scoped_restore = __import__("json").loads(
        server.memory_backup_download(snapshot["path"], scope_type="project", scope_id="ALPHA")
    )
    assert scoped_restore["restored"] is True
    assert scoped_restore["scope_filter"] == {"scope_type": "project", "scope_id": "ALPHA"}
    assert scoped_restore["restored_records"] == 1

    alpha_after_snapshot = __import__("json").loads(
        server.memory_search("Alpha mutation", scope_type="project", scope_id="ALPHA")
    )
    beta_after_snapshot = __import__("json").loads(
        server.memory_search("Beta mutation", scope_type="project", scope_id="BETA")
    )
    assert alpha_after_snapshot == []
    assert len(beta_after_snapshot) == 1

    server.memory_store(
        "semantic",
        "Alpha second mutation should be removed by export scoped restore.",
        "restore.alpha",
        scope_type="project",
        scope_id="ALPHA",
    )

    export_restore = __import__("json").loads(
        server.memory_backup_download(export["path"], scope_type="project", scope_id="ALPHA")
    )
    assert export_restore["restored"] is True
    assert export_restore["restored_records"] == 1

    alpha_after_export = __import__("json").loads(
        server.memory_search("Alpha second mutation", scope_type="project", scope_id="ALPHA")
    )
    beta_after_export = __import__("json").loads(
        server.memory_search("Beta mutation", scope_type="project", scope_id="BETA")
    )
    assert alpha_after_export == []
    assert len(beta_after_export) == 1

    server.close()


def test_python_runtime_ops_and_inspection_surfaces(tmp_path):
    db_path = tmp_path / "ops-runtime.db"
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    server = AegisMCPServer(db_path=str(db_path))

    server.memory_store(
        "semantic",
        "Deployment approvals require reviewer sign-off.",
        "ops.review",
        scope_type="project",
        scope_id="OPS1",
    )
    server.memory_store(
        "semantic",
        "Deployment approvals do not require reviewer sign-off.",
        "ops.review",
        scope_type="project",
        scope_id="OPS1",
    )
    server.memory_store(
        "episodic",
        "Loose note without subject for taxonomy cleanup.",
        None,
        scope_type="project",
        scope_id="OPS1",
    )

    doctor = __import__("json").loads(server.memory_doctor(str(workspace_dir)))
    assert doctor["backend"] == "python"
    assert doctor["database"]["exists"] is True

    taxonomy = __import__("json").loads(server.memory_taxonomy_clean())
    assert taxonomy["backend"] == "python"
    assert taxonomy["migrated"] >= 1

    scan = __import__("json").loads(server.memory_scan())
    assert scan["backend"] == "python"
    assert scan["subjects_scanned"] >= 1
    assert scan["resolution_prompt_count"] >= 1

    prompts = __import__("json").loads(
        server.memory_conflict_prompt(scope_type="project", scope_id="OPS1")
    )
    assert prompts["backend"] == "python"
    assert prompts["count"] >= 1
    first_prompt = prompts["prompts"][0]
    assert first_prompt["classification"] == "user_resolution_required"
    assert first_prompt["recommended_action"] in {"keep_newer", "keep_older"}

    resolved = __import__("json").loads(
        server.memory_conflict_resolve(
            first_prompt["conflict_id"],
            action="keep_newer",
            rationale="Prefer the more recent operational statement.",
        )
    )
    assert resolved["backend"] == "python"
    assert resolved["resolution"] == "resolved_by_user_keep_newer"

    rebuild = __import__("json").loads(server.memory_rebuild())
    assert rebuild["backend"] == "python"
    assert rebuild["rebuilt"] is True

    visualize = __import__("json").loads(server.memory_visualize(50))
    assert visualize["backend"] == "python"
    assert len(visualize["nodes"]) >= 1

    server.close()
