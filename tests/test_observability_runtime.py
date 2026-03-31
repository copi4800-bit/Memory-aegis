from aegis_py.app import AegisApp
from aegis_py.observability import build_runtime_event, reset_global_runtime_observability
from aegis_py.replication.identity import IdentityManager
from aegis_py.replication.sync import Mutation, ReplicationPayload, SyncManager
from aegis_py.storage.db import DatabaseManager
from datetime import datetime, timezone
import uuid


def setup_function():
    reset_global_runtime_observability()


def test_runtime_event_contract_is_stable():
    event = build_runtime_event(
        tool="search",
        result="success",
        scope_type="project",
        scope_id="OBS",
        session_id="session-1",
        latency_ms=12.3456,
        error_code=None,
        details={"result_count": 2},
    )

    assert event["tool"] == "search"
    assert event["result"] == "success"
    assert event["scope_type"] == "project"
    assert event["scope_id"] == "OBS"
    assert event["session_id"] == "session-1"
    assert event["latency_ms"] == 12.346
    assert event["error_code"] is None
    assert event["details"]["result_count"] == 2
    assert event["backend"] == "python"
    assert "ts" in event


def test_observability_snapshot_tracks_memory_flows(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "observability-memory.db"))

    stored = app.put_memory(
        "Observability should show memory writes and reads.",
        type="semantic",
        scope_type="project",
        scope_id="OBS",
        session_id="sess-1",
        subject="observability.runtime",
    )
    results = app.search(
        "memory writes",
        scope_id="OBS",
        scope_type="project",
        limit=5,
        fallback_to_or=True,
    )
    snapshot = app.observability_snapshot()

    assert stored is not None
    assert len(results) >= 1
    assert snapshot["health_state"] in {"HEALTHY", "DEGRADED_SYNC", "BROKEN"}
    assert snapshot["tools"]["put_memory"]["counts"]["success"] >= 1
    assert snapshot["tools"]["search"]["counts"]["success"] >= 1
    assert snapshot["tools"]["put_memory"]["latency_ms"]["max"] >= 0.0
    assert snapshot["recent"][-1]["tool"] == "search"
    assert snapshot["recent"][-1]["details"]["result_count"] >= 1
    app.close()


def test_observability_tracks_consumer_helpers(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "observability-consumer.db"))

    remembered = app.memory_remember("My favorite drink is jasmine tea.")
    recalled = app.memory_recall("favorite drink")
    corrected = app.memory_correct("My favorite drink is jasmine green tea.")
    forgotten = app.memory_forget("favorite drink")
    missed = app.memory_recall("favorite drink")
    snapshot = app.observability_snapshot()

    assert "remembered" in remembered.lower()
    assert "Here is what I remember:" in recalled
    assert "updated my records" in corrected
    assert "forgotten" in forgotten.lower()
    assert "don't recall anything" in missed
    assert snapshot["tools"]["memory_remember"]["counts"]["success"] >= 1
    assert snapshot["tools"]["memory_recall"]["counts"]["success"] >= 1
    assert snapshot["tools"]["memory_recall"]["counts"]["empty"] >= 1
    assert snapshot["tools"]["memory_correct"]["counts"]["success"] >= 1
    assert snapshot["tools"]["memory_forget"]["counts"]["success"] >= 1
    assert any(event["tool"] == "memory_forget" for event in snapshot["recent"])
    app.close()


def test_observability_instruments_background_and_recovery_flows(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "observability-recovery.db"))
    first = app.put_memory(
        "Release checklist depends on gate review.",
        type="semantic",
        scope_type="project",
        scope_id="OBS",
        subject="release.checklist",
    )
    second = app.put_memory(
        "Gate review protects release checklist quality.",
        type="semantic",
        scope_type="project",
        scope_id="OBS",
        subject="release.checklist",
    )

    assert first is not None and second is not None

    planned = app.plan_background_intelligence(scope_type="project", scope_id="OBS")
    run = next(
        item
        for item in app.storage.list_background_intelligence_runs(
            scope_type="project",
            scope_id="OBS",
            status="planned",
        )
        if item["worker_kind"] == "graph_repair"
    )
    applied = app.apply_background_intelligence_run(run["id"], max_mutations=10)
    rolled_back = app.rollback_background_intelligence_run(run["id"])

    backup = app.create_backup(workspace_dir=str(tmp_path))
    preview = app.preview_restore(backup["path"])
    restored = app.restore_backup(backup["path"])
    snapshot = app.observability_snapshot()

    assert planned["proposal_count"] >= 1
    assert applied["applied"] is True
    assert rolled_back["rolled_back"] is True
    assert preview["preview"]["records"] >= 1
    assert restored["mode"] in {"snapshot", "logical_export"}
    assert snapshot["tools"]["background_plan"]["counts"]["success"] >= 1
    assert snapshot["tools"]["background_apply"]["counts"]["success"] >= 1
    assert snapshot["tools"]["background_rollback"]["counts"]["success"] >= 1
    assert snapshot["tools"]["backup_create"]["counts"]["success"] >= 1
    assert snapshot["tools"]["restore_preview"]["counts"]["success"] >= 1
    assert snapshot["tools"]["restore_backup"]["counts"]["success"] >= 1
    assert snapshot["recent"][-1]["tool"] == "restore_backup"
    app.close()


def test_observability_instruments_sync_surface_and_replication(tmp_path):
    source = AegisApp(db_path=str(tmp_path / "observability-sync-source.db"))
    target = AegisApp(db_path=str(tmp_path / "observability-sync-target.db"))

    source.set_scope_policy(scope_type="project", scope_id="SYNCOBS", sync_policy="sync_eligible")
    target.set_scope_policy(scope_type="project", scope_id="SYNCOBS", sync_policy="sync_eligible")
    stored = source.put_memory(
        "Sync observability should stay visible.",
        type="semantic",
        scope_type="project",
        scope_id="SYNCOBS",
        subject="sync.observability",
    )
    assert stored is not None

    exported = source.export_sync_envelope(scope_type="project", scope_id="SYNCOBS", workspace_dir=str(tmp_path))
    previewed = target.preview_sync_envelope(exported["path"])
    imported = target.import_sync_envelope(exported["path"])
    snapshot = target.observability_snapshot()

    assert previewed["incoming_records"] >= 1
    assert imported["imported"] is True
    assert snapshot["tools"]["sync_export"]["counts"]["success"] >= 1
    assert snapshot["tools"]["sync_preview"]["counts"]["success"] >= 1
    assert snapshot["tools"]["sync_import"]["counts"]["success"] >= 1

    repl_db = DatabaseManager(":memory:")
    repl_db.initialize()
    identity = IdentityManager(repl_db)
    sync_manager = SyncManager(repl_db, identity)
    memory_id = str(uuid.uuid4())
    payload = ReplicationPayload(
        payload_id=str(uuid.uuid4()),
        origin_node_id=str(uuid.uuid4()),
        scope_type="global",
        scope_id="global",
        mutations=[
            Mutation(
                action="upsert",
                entity_type="memory",
                entity_id=memory_id,
                data={"id": memory_id, "content": "replicated memory", "status": "active"},
                timestamp=datetime.now(timezone.utc),
            )
        ],
    )
    stats = sync_manager.apply_payload(payload)
    merged = target.observability_snapshot()

    assert stats["applied"] == 1
    assert merged["tools"]["sync_payload_lag"]["counts"]["success"] >= 1
    assert merged["tools"]["sync_payload_apply"]["counts"]["success"] >= 1
    assert any(event["tool"] == "sync_payload_apply" for event in merged["recent"])

    repl_db.close()
    source.close()
    target.close()
