from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer
from aegis_py.spotlight_surface import build_spotlight_payload


def test_pterodactyl_graph_overview_surfaces_in_spotlight(runtime_harness):
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    linked = Memory(
        id="phase104_linked",
        type="semantic",
        content="Friday release board stays on the archive wall.",
        subject="release.board",
        confidence=0.94,
        source_kind="manual",
        source_ref="test://phase104-linked",
        scope_type="agent",
        scope_id="phase104_scope",
    )
    seed = Memory(
        id="phase104_seed",
        type="procedural",
        content="Review the pager checklist before the release board handoff.",
        subject="release.board",
        confidence=0.95,
        source_kind="manual",
        source_ref="test://phase104-seed",
        scope_type="agent",
        scope_id="phase104_scope",
    )
    runtime_harness.store(linked)
    runtime_harness.store(seed)
    runtime_harness.storage.upsert_memory_link(
        source_id="phase104_seed",
        target_id="phase104_linked",
        link_type="supports",
        weight=0.91,
        metadata={"rule": "phase104-test"},
    )
    runtime_harness.sync_fts()

    query = SearchQuery(
        query="pager checklist",
        scope_type="agent",
        scope_id="phase104_scope",
        include_global=False,
        min_score=-10.0,
    )
    results = runtime_harness.pipeline.search(query)
    link_result = next(item for item in results if item.memory.id == "phase104_linked")
    payload = build_spotlight_payload(link_result)

    assert payload["retrieval_predators"]["pterodactyl_graph_overview"] == "supports"
    assert payload["retrieval_predators"]["pterodactyl_route"]["link_type"] == "supports"
    assert payload["retrieval_predators"]["pterodactyl_route"]["hops"] == 1


def test_oviraptor_taxonomy_surfaces_in_core_showcase(tmp_path):
    db_path = tmp_path / "phase104_showcase.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        first = server.app.put_memory(
            "Store the deployment checklist in the release board cabinet.",
            type="procedural",
            scope_type="agent",
            scope_id="phase104_scope",
            source_kind="manual",
            source_ref="test://phase104-a",
            subject="Release.Board",
            confidence=0.95,
            metadata={"is_winner": True},
        )
        second = server.app.put_memory(
            "The release board cabinet is checked every Friday.",
            type="semantic",
            scope_type="agent",
            scope_id="phase104_scope",
            source_kind="manual",
            source_ref="test://phase104-b",
            subject="release.board",
            confidence=0.93,
        )
        assert first is not None
        assert second is not None
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = server.app.core_showcase(
            "release board",
            scope_type="agent",
            scope_id="phase104_scope",
            include_global=False,
        )

        assert payload["result"]["taxonomy_summary"]["oviraptor_taxonomy_order"] > 0.0
        assert payload["result"]["taxonomy_summary"]["subject_count"] >= 1
        assert "[Oviraptor Taxonomy]" in payload["showcase_text"]
        assert "[Pterodactyl Flight]" in payload["showcase_text"]
    finally:
        server.close()
