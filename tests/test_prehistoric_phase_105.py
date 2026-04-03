from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer


def test_ingest_diagnostic_surfaces_dimetrodon_chalicotherium_ammonite(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase105_ingest.db"))
    try:
        diagnostic = app.diagnose_ingest_attempt(
            "Workflow: deploy the release archive after checklist 1, checklist 2, and checklist 3 using the board key.",
            type="procedural",
            scope_type="agent",
            scope_id="phase105_scope",
            source_kind="manual",
            source_ref="test://phase105-ingest",
            subject="Release Archive Board",
            confidence=0.95,
            activation_score=1.12,
        )

        prehistoric = diagnostic["prehistoric_write"]
        assert prehistoric["dimetrodon_feature_separation"] > 0.62
        assert prehistoric["dimetrodon_band"] in {"separated", "surgical"}
        assert prehistoric["chalicotherium_ecology_fit"] > 0.62
        assert prehistoric["chalicotherium_band"] in {"fitting", "native"}
        assert prehistoric["ammonite_spiral_stability"] > 0.68
        assert prehistoric["ammonite_band"] in {"settling", "stable"}
    finally:
        app.close()


def test_core_showcase_surfaces_write_intelligence(tmp_path):
    db_path = tmp_path / "phase105_showcase.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        stored = server.app.put_memory(
            "Workflow: deploy the release archive after checklist 1, checklist 2, and checklist 3 using the board key.",
            type="procedural",
            scope_type="agent",
            scope_id="phase105_scope",
            source_kind="manual",
            source_ref="test://phase105-showcase",
            subject="Release Archive Board",
            confidence=0.95,
            metadata={"is_winner": True},
        )
        assert stored is not None
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = server.app.core_showcase(
            "release archive board",
            scope_type="agent",
            scope_id="phase105_scope",
            include_global=False,
        )

        write_intelligence = payload["result"]["write_intelligence"]
        assert write_intelligence["dimetrodon"]["dimetrodon_feature_separation"] > 0.62
        assert write_intelligence["chalicotherium"]["predicted_lane"] == "procedural"
        assert write_intelligence["ammonite"]["canonical_subject"] == "release.archive.board"
        assert "[Dimetrodon Extraction]" in payload["showcase_text"]
        assert "[Chalicotherium Lane]" in payload["showcase_text"]
        assert "[Ammonite Subject]" in payload["showcase_text"]
    finally:
        server.close()
