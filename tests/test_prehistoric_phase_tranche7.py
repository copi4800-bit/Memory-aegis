import json

from aegis_py.mcp.server import AegisMCPServer
from aegis_py.preferences.manager import PreferenceManager
from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import StyleProfile


def test_argentinosaurus_scope_geometry_surfaces_on_query():
    query = SearchQuery(
        query="backup policy",
        scope_type="agent",
        scope_id="prehistoric_tranche7",
        include_global=True,
    )

    geometry = query.argentinosaurus_scope_geometry

    assert geometry["explicit_scope"] is True
    assert geometry["include_global"] is True
    assert geometry["argentinosaurus_scope_geometry"] > 0.7


def test_dire_wolf_identity_persistence_surfaces_from_profile(runtime_harness):
    runtime_harness.storage.upsert_profile(
        StyleProfile(
            id="prof_dire_wolf",
            scope_id="prehistoric_tranche7",
            scope_type="agent",
            preferences_json={
                "user_honorific": "anh",
                "assistant_honorific": "em",
                "preferred_format": "markdown",
                "verbosity": 0.82,
            },
        )
    )
    manager = PreferenceManager(runtime_harness.storage)
    report = manager.build_identity_report("prehistoric_tranche7", "agent")

    assert report["stable_honorifics"] >= 3
    assert report["dire_wolf_identity_persistence"] > 0.7


def test_megatherium_boundary_gate_blocks_missing_required_args(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "prehistoric_tranche7.db"))
    try:
        payload = json.loads(server.run_tool("memory_spotlight", {"scope_type": "agent", "scope_id": "x"}))

        assert payload["error"] == "missing_required_args"
        assert "query" in payload["missing"]
        assert payload["megatherium_boundary"]["megatherium_boundary_admissibility"] < 0.8
    finally:
        server.close()

