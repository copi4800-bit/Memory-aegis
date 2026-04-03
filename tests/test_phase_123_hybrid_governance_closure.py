from aegis_py.app import AegisApp
from aegis_py.retrieval.hybrid_governance import classify_query_route, fuse_hybrid_signals


def test_hybrid_route_classifier_prefers_exact_relational_and_semantic_modes():
    assert classify_query_route("release.owner v2").route == "exact"
    assert classify_query_route("owner related via support link").route == "relational"
    assert classify_query_route("explain the overall context and meaning behind this rollout").route == "semantic"


def test_hybrid_fusion_math_stays_bounded_and_emits_weighted_score():
    profile = classify_query_route("release.owner v2")
    fusion = fuse_hybrid_signals(
        route_profile=profile,
        signals={
            "lexical": 0.92,
            "semantic": 0.34,
            "graph": 0.08,
            "compressed": 0.21,
            "scope": 1.0,
            "activation": 0.77,
        },
        governance_alignment=0.88,
    )
    assert fusion.route == "exact"
    assert 0.0 <= fusion.fused_score <= 1.0
    assert 0.0 <= fusion.agreement <= 1.0
    assert fusion.weights["lexical"] > fusion.weights["graph"]


def test_search_pipeline_applies_hybrid_governance_pressure_and_surfaces_it():
    app = AegisApp(":memory:")
    try:
        stored = app.put_memory(
            "The release owner is Bao and the release board confirms Bao as the owner.",
            type="semantic",
            scope_type="agent",
            scope_id="phase123_scope",
            source_kind="manual",
            source_ref="test://phase123",
            subject="release.owner",
            confidence=0.99,
            metadata={"is_winner": True},
        )
        assert stored is not None
        app.storage.execute("DELETE FROM memories_fts")
        app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )
        query = type(
            "Query",
            (),
            {
                "query": "release owner",
                "scope_type": "agent",
                "scope_id": "phase123_scope",
                "limit": 5,
                "include_global": False,
                "min_score": -10.0,
                "intent": "normal_recall",
                "scoring_mode": "v10_primary",
            },
        )()

        results = app.search_pipeline.search(query)
        assert results
        chosen = results[0]
        hybrid = getattr(chosen, "hybrid_fusion", {}) or {}
        factors = chosen.v10_trace.factors

        assert hybrid.get("route") in {"exact", "balanced", "relational"}
        assert float(hybrid.get("fused_score", 0.0)) > 0.0
        assert "hybrid_route:" in " ".join(chosen.reasons)
        assert "hybrid_governance_fused_score" in factors
        assert "hybrid_governance_pressure" in factors
        assert "hybrid_governance_pressure" in chosen.v10_decision.decision_reason
    finally:
        app.close()
