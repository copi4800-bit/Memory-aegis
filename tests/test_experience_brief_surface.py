from __future__ import annotations

import json

from aegis_py.mcp.server import AegisMCPServer


def test_experience_brief_tool_returns_product_facing_story(tmp_path):
    db_path = tmp_path / "experience_brief_tool.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        old_stored = server.app.put_memory(
            "The release owner is Linh.",
            type="semantic",
            scope_type="agent",
            scope_id="experience_scope",
            source_kind="manual",
            source_ref="test://experience-old",
            subject="release.owner",
            confidence=0.9,
        )
        server.app.put_memory(
            "Correction: the release owner is Bao.",
            type="semantic",
            scope_type="agent",
            scope_id="experience_scope",
            source_kind="manual",
            source_ref="test://experience-new",
            subject="release.owner",
            confidence=1.0,
            metadata={"is_winner": True, "is_correction": True},
        )
        if old_stored is not None:
            server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        raw = server.run_tool(
            "memory_experience_brief",
            {
                "query": "release owner",
                "scope_type": "agent",
                "scope_id": "experience_scope",
                "include_global": False,
                "intent": "correction_lookup",
            },
        )
        payload = json.loads(raw)

        assert payload["available"] is True
        assert payload["result"]["hero"]["label"] == "Strong Current Truth"
        assert payload["result"]["compressed_snapshot"]["passed"] is True
        assert payload["result"]["profile_snapshot"]
        assert payload["result"]["doctor_snapshot"]
        assert payload["result"]["next_actions"]
        assert "[TruthKeep Experience Brief]" in payload["brief_text"]
        assert "[Compressed Tier]" in payload["brief_text"]
        assert "[Next Actions]" in payload["brief_text"]
    finally:
        server.close()
