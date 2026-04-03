from __future__ import annotations

import json

from aegis_py.mcp.server import AegisMCPServer
from aegis_py.surface import build_public_surface


def test_public_surface_splits_ordinary_and_operator_lanes():
    payload = build_public_surface(runtime_version="test")
    consumer = payload["consumer_contract"]

    assert "ordinary_lane" in consumer
    assert "operator_lane" in consumer
    assert "memory_remember" in consumer["ordinary_lane"]["operations"]
    assert "memory_governance" in consumer["operator_lane"]["operations"]
    assert consumer["operator_lane"]["default_hidden"] is True


def test_workflow_shell_tool_returns_correction_first_loop(tmp_path):
    db_path = tmp_path / "workflow_shell_tool.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        old_stored = server.app.put_memory("The release owner is Linh.", type="semantic", scope_type="agent", scope_id="workflow_scope", source_kind="manual", source_ref="test://workflow-old", subject="release.owner", confidence=0.9)
        server.app.put_memory("Correction: the release owner is Bao.", type="semantic", scope_type="agent", scope_id="workflow_scope", source_kind="manual", source_ref="test://workflow-new", subject="release.owner", confidence=1.0, metadata={"is_winner": True, "is_correction": True})
        if old_stored is not None:
            server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
            server.app.storage.record_memory_state_transition(memory_id=old_stored.id, from_state="validated", to_state="invalidated", reason="corrected_by_newer_info", actor="test", details={"winner_hint": "release.owner"})
            server.app.storage.record_governance_event(event_kind="truth_superseded_test", scope_type="agent", scope_id="workflow_scope", memory_id=old_stored.id, payload={"winner_id": "winner", "reason": "newer_correction"})
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute("INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories")

        raw = server.run_tool("memory_workflow_shell", {"query": "release owner", "scope_type": "agent", "scope_id": "workflow_scope", "intent": "correction_lookup"})
        payload = json.loads(raw)

        assert payload["ready"] is True
        assert payload["result"]["workflow_steps"]
        assert payload["result"]["ordinary_lane"]["operations"]
        assert "memory_governance" in payload["result"]["operator_escape_hatches"]
        assert payload["result"]["verification"]["suppressed_count"] >= 1
        assert "[TruthKeep Workflow Shell]" in payload["workflow_text"]
        assert "[Ordinary Path]" in payload["workflow_text"]
        assert "[Truth Transition Timeline]" in payload["workflow_text"]
        assert "[Operator Escape Hatches]" in payload["workflow_text"]
    finally:
        server.close()
