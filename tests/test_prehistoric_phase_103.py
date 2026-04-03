import json

from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer


def test_meganeura_write_summary_surfaces_in_ingest_diagnostic(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase103_ingest.db"))
    try:
        diagnostic = app.diagnose_ingest_attempt(
            (
                "At 18:30 on Friday, deploy the backup plan using checklist 4 under the blue window. "
                "Confirm the fallback route with the red binder, mark step 7 complete, and page the night "
                "operator before 18:45 if the vault sensor stays amber."
            ),
            type="procedural",
            scope_type="agent",
            scope_id="phase103_scope",
            source_kind="manual",
            source_ref="test://phase103-ingest",
            subject="deploy.window",
            confidence=0.95,
            activation_score=1.1,
        )

        assert diagnostic["prehistoric_write"]["meganeura_capture_span"] > 0.58
        assert diagnostic["prehistoric_write"]["meganeura_band"] in {"focused", "broad"}
    finally:
        app.close()


def test_spotlight_surfaces_utahraptor_and_basilosaurus(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "phase103_spotlight.db"))
    try:
        stored = server.app.put_memory(
            "SQLite with FTS5 keeps our release schedule database backend searchable every Friday at 18:00.",
            type="semantic",
            scope_type="agent",
            scope_id="phase103_scope",
            source_kind="manual",
            source_ref="test://phase103-retrieval",
            subject="storage.backend",
            confidence=0.96,
            metadata={"is_winner": True},
        )
        assert stored is not None
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = json.loads(
            server.run_tool(
                "memory_spotlight",
                {
                    "query": "database backend",
                    "scope_type": "agent",
                    "scope_id": "phase103_scope",
                    "include_global": False,
                },
            )
        )

        predators = payload["results"][0]["retrieval_predators"]
        assert predators["utahraptor_lexical_pursuit"] is not None
        assert predators["basilosaurus_semantic_echo"] is not None
        assert "[Retrieval Predators]" in payload["spotlight_text"]
    finally:
        server.close()
