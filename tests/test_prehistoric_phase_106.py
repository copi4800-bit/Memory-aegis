from aegis_py.app import AegisApp
from aegis_py.mcp.server import AegisMCPServer
from aegis_py.spotlight_surface import build_spotlight_payload


def test_meganeura_guidance_surfaces_in_ingest_diagnostic(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase106_ingest.db"))
    try:
        diagnostic = app.diagnose_ingest_attempt(
            (
                "At 18:30 on Friday, deploy the backup plan using checklist 4 under the blue window. "
                "Confirm the fallback route with the red binder, mark step 7 complete, and page the night "
                "operator before 18:45 if the vault sensor stays amber."
            ),
            type="procedural",
            scope_type="agent",
            scope_id="phase106_scope",
            source_kind="manual",
            source_ref="test://phase106-ingest",
            subject="deploy.window",
            confidence=0.95,
            activation_score=1.1,
        )
        prehistoric = diagnostic["prehistoric_write"]
        assert prehistoric["meganeura_capture_span"] > 0.58
        assert prehistoric["meganeura_band"] in {"focused", "broad"}
        assert "operational" in prehistoric["meganeura_guidance"].lower() or "detail" in prehistoric["meganeura_guidance"].lower()
    finally:
        app.close()


def test_paraceratherium_and_utahraptor_deepen_spotlight(runtime_harness):
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.storage.models import Memory

    memory = Memory(
        id="phase106_retrieval",
        type="semantic",
        content="The maintenance window moved to Tuesday and the release gate uses the red board.",
        subject="maintenance.window",
        confidence=0.97,
        source_kind="manual",
        source_ref="test://phase106-retrieval",
        scope_type="agent",
        scope_id="phase106_scope",
        metadata={"is_winner": True},
    )
    runtime_harness.store(memory)
    runtime_harness.sync_fts()

    query = SearchQuery(
        query="maintenance window red board",
        scope_type="agent",
        scope_id="phase106_scope",
        include_global=False,
        min_score=-10.0,
    )
    results = runtime_harness.pipeline.search(query)
    payload = build_spotlight_payload(results[0])

    assert payload["paraceratherium_trace"]["policy_step_count"] >= 1
    assert payload["paraceratherium_trace"]["governance_story"]
    assert payload["retrieval_predators"]["utahraptor_lexical_pursuit"] is not None
    assert payload["retrieval_predators"]["utahraptor_band"] in {"glancing", "tracking", "locked"}


def test_core_showcase_renders_deeper_paraceratherium_and_utahraptor(tmp_path):
    db_path = tmp_path / "phase106_showcase.db"
    server = AegisMCPServer(db_path=str(db_path))
    try:
        stored = server.app.put_memory(
            "The maintenance window moved to Tuesday and the release gate uses the red board.",
            type="semantic",
            scope_type="agent",
            scope_id="phase106_scope",
            source_kind="manual",
            source_ref="test://phase106-showcase",
            subject="maintenance.window",
            confidence=0.97,
            metadata={"is_winner": True},
        )
        assert stored is not None
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = server.app.core_showcase(
            "maintenance window red board",
            scope_type="agent",
            scope_id="phase106_scope",
            include_global=False,
        )

        assert payload["result"]["paraceratherium_trace"]["policy_step_count"] >= 1
        assert payload["result"]["retrieval_predators"]["utahraptor_band"] in {"glancing", "tracking", "locked"}
        assert "[Paraceratherium Trace]" in payload["showcase_text"]
        assert "utahraptor_band=" in payload["showcase_text"]
    finally:
        server.close()
