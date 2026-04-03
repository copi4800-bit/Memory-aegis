from aegis_py.app import AegisApp


def test_prehistoric_judged_recall_pressure_surfaces_in_trace(tmp_path):
    app = AegisApp(str(tmp_path / "phase110.db"))
    try:
        seed = app.put_memory(
            content="Review the pager checklist before the release board handoff.",
            type="procedural",
            scope_type="agent",
            scope_id="phase110_scope",
            source_kind="manual",
            source_ref="test://phase110-seed",
            subject="release.board",
            confidence=0.96,
            metadata={"is_winner": True},
        )
        linked = app.put_memory(
            content="Friday release board stays on the archive wall.",
            type="semantic",
            scope_type="agent",
            scope_id="phase110_scope",
            source_kind="manual",
            source_ref="test://phase110-linked",
            subject="release.board",
            confidence=0.95,
        )
        semantic = app.put_memory(
            content="SQLite with FTS5 keeps the release schedule database backend searchable every Friday at 18:00.",
            type="semantic",
            scope_type="agent",
            scope_id="phase110_scope",
            source_kind="manual",
            source_ref="test://phase110-semantic",
            subject="storage.backend",
            confidence=0.97,
            metadata={"is_winner": True},
        )
        assert seed is not None
        assert linked is not None
        assert semantic is not None
        app.storage.upsert_memory_link(
            source_id=seed.id,
            target_id=linked.id,
            link_type="supports",
            weight=0.91,
            metadata={"rule": "phase110-test"},
        )
        app.storage.execute("DELETE FROM memories_fts")
        app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        retrieval = app.search_pipeline.search(
            type("Query", (), {
                "query": "database backend pager checklist",
                "scope_type": "agent",
                "scope_id": "phase110_scope",
                "limit": 10,
                "include_global": False,
                "min_score": -10.0,
                "intent": "normal_recall",
                "scoring_mode": "v10_primary",
            })()
        )

        assert retrieval
        semantic_result = next(item for item in retrieval if item.memory.id == semantic.id)
        assert semantic_result.v10_trace.factors.get("prehistoric_judged_recall_pressure", 0.0) > 0.0
        assert any(
            marker in semantic_result.v10_decision.decision_reason
            for marker in {"utahraptor_judged_pressure", "basilosaurus_judged_pressure", "paraceratherium_judged_pressure"}
        )

        linked_result = next(item for item in retrieval if item.memory.id == linked.id)
        assert linked_result.v10_trace.factors.get("pterodactyl_judged_pressure", 0.0) > 0.0
    finally:
        app.close()
