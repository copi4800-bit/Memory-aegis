from aegis_py.mcp.server import AegisMCPServer
from aegis_py.spotlight_surface import build_spotlight_payload


def test_paraceratherium_and_basilosaurus_gain_narrative_bands(runtime_harness):
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    memory = Memory(
        id="phase108_retrieval",
        type="semantic",
        content="SQLite with FTS5 keeps the release schedule database backend searchable every Friday at 18:00.",
        subject="storage.backend",
        confidence=0.97,
        source_kind="manual",
        source_ref="test://phase108-retrieval",
        scope_type="agent",
        scope_id="phase108_scope",
        metadata={"is_winner": True},
    )
    runtime_harness.store(memory)
    runtime_harness.sync_fts()

    query = SearchQuery(
        query="database backend",
        scope_type="agent",
        scope_id="phase108_scope",
        include_global=False,
        min_score=-10.0,
    )
    results = runtime_harness.pipeline.search(query)
    payload = build_spotlight_payload(results[0])

    assert payload["paraceratherium_trace"]["decision_narrative"]
    assert payload["retrieval_predators"]["basilosaurus_band"] in {"audible", "resonant"}
    assert payload["retrieval_predators"]["basilosaurus_term_count"] >= 1


def test_core_showcase_renders_pterodactyl_flight_story_and_paraceratherium_narrative(tmp_path):
    db_path = tmp_path / "phase108_showcase.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        linked = server.app.put_memory(
            "Friday release board stays on the archive wall.",
            type="semantic",
            scope_type="agent",
            scope_id="phase108_scope",
            source_kind="manual",
            source_ref="test://phase108-linked",
            subject="release.board",
            confidence=0.94,
        )
        seed = server.app.put_memory(
            "Review the pager checklist before the release board handoff.",
            type="procedural",
            scope_type="agent",
            scope_id="phase108_scope",
            source_kind="manual",
            source_ref="test://phase108-seed",
            subject="release.board",
            confidence=0.95,
            metadata={"is_winner": True},
        )
        assert linked is not None
        assert seed is not None
        server.app.storage.upsert_memory_link(
            source_id=seed.id,
            target_id=linked.id,
            link_type="supports",
            weight=0.91,
            metadata={"rule": "phase108-test"},
        )
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = server.app.core_showcase(
            "pager checklist",
            scope_type="agent",
            scope_id="phase108_scope",
            include_global=False,
        )

        assert payload["result"]["paraceratherium_trace"]["decision_narrative"]
        assert payload["result"]["retrieval_predators"]["pterodactyl_flight_story"]
        assert "[Paraceratherium Narrative]" in payload["showcase_text"]
        assert "Graph flight entered through" in payload["showcase_text"]
    finally:
        server.close()
