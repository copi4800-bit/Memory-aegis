import json

from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer
from aegis_py.storage.models import Memory, StyleProfile


def test_megarachne_topology_surfaces_in_core_showcase(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "phase101_showcase.db"))
    try:
        winner = server.app.put_memory(
            "The rollout owner is Tuesday Ops.",
            type="semantic",
            scope_type="agent",
            scope_id="phase101_scope",
            source_kind="manual",
            source_ref="test://phase101-winner",
            subject="rollout_owner",
            confidence=1.0,
            metadata={"is_winner": True},
        )
        peer = server.app.put_memory(
            "Tuesday Ops owns the rollout checklist.",
            type="procedural",
            scope_type="agent",
            scope_id="phase101_scope",
            source_kind="manual",
            source_ref="test://phase101-peer",
            subject="rollout_owner",
            confidence=0.9,
        )
        assert winner is not None
        assert peer is not None
        server.app.storage.upsert_memory_link(
            source_id=winner.id,
            target_id=peer.id,
            link_type="supports",
            weight=0.88,
            metadata={"source": "test://phase101-link"},
        )
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = json.loads(
            server.run_tool(
                "memory_core_showcase",
                {"query": "rollout owner", "scope_type": "agent", "scope_id": "phase101_scope"},
            )
        )

        assert payload["result"]["topology_summary"]["megarachne_topology_strength"] > 0.5
        assert "[Megarachne Topology]" in payload["showcase_text"]
    finally:
        server.close()


def test_dire_wolf_identity_guidance_surfaces_in_render_profile(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase101_profile.db"))
    try:
        app.storage.upsert_profile(
            StyleProfile(
                id="phase101_profile",
                scope_id="phase101_scope",
                scope_type="agent",
                preferences_json={
                    "user_honorific": "anh",
                    "assistant_honorific": "em",
                    "preferred_format": "markdown",
                    "tone": "precise",
                    "verbosity": 0.84,
                },
            )
        )
        rendered = app.render_profile(scope_id="phase101_scope", scope_type="agent")

        assert "### Dire Wolf Identity" in rendered
        assert "Pack Stability:" in rendered
        assert "Stable Honorific Signals:" in rendered
        assert "Identity-Guided Format Hint: prefer markdown" in rendered
    finally:
        app.close()


def test_megatherium_boundary_report_surfaces_contract_diagnostics(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "phase101_boundary.db"))
    try:
        payload = json.loads(
            server.run_tool(
                "memory_spotlight",
                {"scope_type": "agent", "query_extra": "unexpected"},
            )
        )

        boundary = payload["megatherium_boundary"]
        assert payload["error"] == "missing_required_args"
        assert "query" in boundary["required_args"]
        assert "scope_type" in boundary["provided_args"]
        assert "query_extra" in boundary["unexpected_args"]
        assert boundary["scope_pair_valid"] is False
    finally:
        server.close()
