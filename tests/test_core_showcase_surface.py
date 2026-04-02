from __future__ import annotations

import json

from aegis_py.mcp.server import AegisMCPServer


def test_core_showcase_tool_returns_full_core_story(tmp_path):
    db_path = tmp_path / "core_showcase_tool.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        old_stored = server.app.put_memory(
            "The deployment window is Monday.",
            type="semantic",
            scope_type="agent",
            scope_id="showcase_scope",
            source_kind="manual",
            source_ref="test://showcase-old",
            subject="deployment_window",
            confidence=0.9,
        )
        current_stored = server.app.put_memory(
            "Correction: the deployment window moved to Tuesday.",
            type="semantic",
            scope_type="agent",
            scope_id="showcase_scope",
            source_kind="manual",
            source_ref="test://showcase-new",
            subject="deployment_window",
            confidence=1.0,
            metadata={"is_winner": True, "is_correction": True},
        )
        assert old_stored is not None
        assert current_stored is not None
        server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        raw = server.run_tool(
            "memory_core_showcase",
            {
                "query": "deployment window",
                "scope_type": "agent",
                "scope_id": "showcase_scope",
                "include_global": False,
                "intent": "correction_lookup",
            },
        )
        payload = json.loads(raw)

        assert payload["result_count"] == 1
        assert payload["result"]["verdict"]["label"] == "Strong Current Truth"
        assert payload["result"]["executive_summary"]
        assert payload["result"]["truth_state"]["truth_role"] == "winner"
        assert payload["result"]["evidence_summary"]["count"] >= 1
        assert "signal_summary" in payload["result"]
        assert "graph_summary" in payload["result"]
        assert "[Aegis Core Verdict]" in payload["showcase_text"]
        assert "[Executive Summary]" in payload["showcase_text"]
        assert "[Governance Timeline]" in payload["showcase_text"]
        assert "[Core Signals]" in payload["showcase_text"]
        assert "[Scope Health]" in payload["showcase_text"]
    finally:
        server.close()
