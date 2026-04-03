from __future__ import annotations

import json

from aegis_py.mcp.server import AegisMCPServer


def test_dashboard_shell_tool_returns_unified_destination(tmp_path):
    db_path = tmp_path / "dashboard_shell_tool.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        old_stored = server.app.put_memory("The release owner is Linh.", type="semantic", scope_type="agent", scope_id="dashboard_scope", source_kind="manual", source_ref="test://dashboard-old", subject="release.owner", confidence=0.9)
        server.app.put_memory("Correction: the release owner is Bao.", type="semantic", scope_type="agent", scope_id="dashboard_scope", source_kind="manual", source_ref="test://dashboard-new", subject="release.owner", confidence=1.0, metadata={"is_winner": True, "is_correction": True})
        if old_stored is not None:
            server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
            server.app.storage.record_memory_state_transition(memory_id=old_stored.id, from_state="validated", to_state="invalidated", reason="corrected_by_newer_info", actor="test", details={"winner_hint": "release.owner"})
            server.app.storage.record_governance_event(event_kind="truth_superseded_test", scope_type="agent", scope_id="dashboard_scope", memory_id=old_stored.id, payload={"winner_id": "winner", "reason": "newer_correction"})
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute("INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories")

        raw = server.run_tool("memory_dashboard_shell", {"query": "release owner", "scope_type": "agent", "scope_id": "dashboard_scope", "intent": "correction_lookup"})
        payload = json.loads(raw)

        assert payload["ready"] is True
        assert payload["result"]["sections"]
        assert "[TruthKeep Dashboard Shell]" in payload["dashboard_text"]
        assert "[Ordinary Mode]" in payload["dashboard_text"]
        assert "[Truth Transition Timeline]" in payload["dashboard_text"]
        assert "[Operator Mode]" in payload["dashboard_text"]
        assert "[Deep Inspection]" in payload["dashboard_text"]
    finally:
        server.close()
