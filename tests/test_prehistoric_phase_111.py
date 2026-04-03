from aegis_py.app import AegisApp


def test_meganeura_and_dimetrodon_influence_policy_gate(tmp_path):
    app = AegisApp(str(tmp_path / "phase111_gate.db"))
    try:
        diagnostic = app.diagnose_ingest_attempt(
            "alpha beta",
            type="procedural",
            scope_type="agent",
            scope_id="phase111_scope",
            source_kind="manual",
            source_ref="test://phase111-gate",
            subject="release.board",
            confidence=0.92,
            activation_score=1.0,
        )

        assert diagnostic["target_state"] == "hypothesized"
        assert "meganeura_capture_narrow" in diagnostic["reasons"]
        assert "dimetrodon_feature_blended" in diagnostic["reasons"]
    finally:
        app.close()


def test_argentinosaurus_judged_pressure_surfaces_in_trace(tmp_path):
    app = AegisApp(str(tmp_path / "phase111_recall.db"))
    try:
        stored = app.put_memory(
            "The release board remains in the north cabinet for this agent scope.",
            type="semantic",
            scope_type="agent",
            scope_id="phase111_scope",
            source_kind="manual",
            source_ref="test://phase111-recall",
            subject="release.board",
            confidence=0.97,
            metadata={"is_winner": True},
        )
        assert stored is not None
        app.storage.execute("DELETE FROM memories_fts")
        app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        results = app.search_pipeline.search(
            type("Query", (), {
                "query": "release board north cabinet",
                "scope_type": "agent",
                "scope_id": "phase111_scope",
                "limit": 10,
                "include_global": False,
                "min_score": -10.0,
                "intent": "normal_recall",
                "scoring_mode": "v10_primary",
            })()
        )

        assert results
        top = results[0]
        assert top.v10_trace.factors.get("argentinosaurus_judged_pressure", 0.0) > 0.0
        assert "argentinosaurus_judged_pressure" in top.v10_decision.decision_reason
    finally:
        app.close()
