from aegis_py.app import AegisApp
from aegis_py.retrieval.compressed_prefilter import CompressedCandidatePrefilter
from aegis_py.retrieval.engine import _run_compressed_candidate_stage


def test_compressed_candidate_tier_surfaces_bounded_candidate_without_bypassing_governance(tmp_path):
    app = AegisApp(str(tmp_path / "phase116.db"))
    try:
        winner = app.put_memory(
            content="Harbor operations owns the deployment roster and maintains the release checklist.",
            type="semantic",
            scope_type="agent",
            scope_id="phase116_scope",
            source_kind="manual",
            source_ref="test://phase116-winner",
            subject="deploy.roster",
            confidence=0.98,
            metadata={"is_winner": True},
        )
        candidate = app.put_memory(
            content="Deployment roster handoff ledger lives with harbor operations.",
            type="semantic",
            scope_type="agent",
            scope_id="phase116_scope",
            source_kind="manual",
            source_ref="test://phase116-candidate",
            subject="deploy.roster",
            confidence=0.91,
        )
        assert winner is not None
        assert candidate is not None
        app.storage.execute("DELETE FROM memories_fts")
        app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        query = type(
            "Query",
            (),
            {
                "query": "deployment roster harbor checklist steward",
                "scope_type": "agent",
                "scope_id": "phase116_scope",
                "limit": 10,
                "include_global": False,
                "min_score": -10.0,
                "intent": "normal_recall",
                "scoring_mode": "v10_primary",
            },
        )()

        prefilter = CompressedCandidatePrefilter()
        compressed = _run_compressed_candidate_stage(
            app.storage,
            query=query.query,
            query_signature=prefilter.build_signature(query.query, semantic_terms=[]),
            scope_type="agent",
            scope_id="phase116_scope",
            limit=10,
            exclude_ids=set(),
            include_global=False,
            prefilter=prefilter,
        )
        surfaced = next(item for item in compressed if item["id"] == candidate.id)
        assert surfaced["compressed_prefilter_score"] > 0.0
        assert surfaced["compressed_prefilter_tier"] in {"warm", "cold", "hot"}

        results = app.search_pipeline.search(query)

        assert results
        top = results[0]
        assert top.memory.id == winner.id
        assert top.v10_decision.truth_role.value == "winner"
    finally:
        app.close()
