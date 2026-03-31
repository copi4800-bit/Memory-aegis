from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from aegis_py.app import AegisApp


def _iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def test_compact_storage_prunes_cold_historical_rows(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "growth-control.db"))
    active = app.put_memory(
        "Active memory should survive compaction.",
        type="semantic",
        scope_type="project",
        scope_id="GC",
        source_kind="manual",
        source_ref="growth://active",
        subject="growth.active",
    )
    archived = app.put_memory(
        "Archived memory should be physically pruned later.",
        type="semantic",
        scope_type="project",
        scope_id="GC",
        source_kind="manual",
        source_ref="growth://archived",
        subject="growth.archived",
    )
    superseded = app.put_memory(
        "Superseded memory should be physically pruned later.",
        type="semantic",
        scope_type="project",
        scope_id="GC",
        source_kind="manual",
        source_ref="growth://superseded",
        subject="growth.superseded",
    )
    assert active is not None and archived is not None and superseded is not None

    app.storage.execute(
        "UPDATE memories SET status = 'archived', archived_at = ?, updated_at = ? WHERE id = ?",
        (_iso(90), _iso(90), archived.id),
    )
    app.storage.execute(
        "UPDATE memories SET status = 'superseded', archived_at = ?, updated_at = ? WHERE id = ?",
        (_iso(45), _iso(45), superseded.id),
    )

    app.storage.record_evidence_artifact(
        artifact_kind="growth_test",
        scope_type="project",
        scope_id="GC",
        memory_id=archived.id,
        payload={"marker": "old-artifact"},
    )
    app.storage.execute(
        "UPDATE evidence_artifacts SET created_at = ? WHERE memory_id = ?",
        (_iso(90), archived.id),
    )
    app.storage.execute(
        """
        INSERT INTO governance_events (
            id, event_kind, scope_type, scope_id, memory_id, evidence_event_id, payload_json, created_at
        ) VALUES (?, 'growth_test', 'project', 'GC', ?, NULL, '{}', ?)
        """,
        (f"gov_{uuid.uuid4().hex[:12]}", archived.id, _iso(90)),
    )
    app.storage.execute(
        "INSERT INTO node_identities (node_id, is_local, name, created_at) VALUES ('growth-node', 0, 'growth-node', ?)",
        (_iso(45),),
    )
    app.storage.execute(
        """
        INSERT INTO replication_audit_log (
            id, payload_id, origin_node_id, entity_type, entity_id, action, applied_at, status, details_json
        ) VALUES (?, ?, ?, 'memory', ?, 'upsert', ?, 'applied', '{}')
        """,
        (
            f"rep_{uuid.uuid4().hex[:12]}",
            f"payload_{uuid.uuid4().hex[:8]}",
            "growth-node",
            archived.id,
            _iso(45),
        ),
    )
    app.storage.execute(
        """
        INSERT INTO autonomous_audit_log (
            id, action_type, entity_type, entity_id, explanation, confidence_score, applied_at, status, details_json, rolled_back_at
        ) VALUES (?, 'growth_test', 'memory', ?, 'old failed action', 0.2, ?, 'failed', '{}', NULL)
        """,
        (f"audit_{uuid.uuid4().hex[:12]}", archived.id, _iso(45)),
    )

    before = app.storage_footprint()
    result = app.compact_storage(
        archived_memory_days=30,
        superseded_memory_days=14,
        evidence_days=30,
        governance_days=30,
        replication_days=14,
        background_days=14,
        vacuum=False,
    )
    after = app.storage_footprint()

    assert app.storage.get_memory(active.id) is not None
    assert app.storage.get_memory(archived.id) is None
    assert app.storage.get_memory(superseded.id) is None
    assert result["deleted"]["archived_memories"] >= 1
    assert result["deleted"]["superseded_memories"] >= 1
    assert result["deleted"]["evidence_artifacts"] >= 1
    assert result["deleted"]["governance_events"] >= 1
    assert result["deleted"]["replication_audit_log"] >= 1
    assert result["deleted"]["autonomous_audit_log"] >= 1
    assert after["rows"]["memories"] < before["rows"]["memories"]
    app.close()
