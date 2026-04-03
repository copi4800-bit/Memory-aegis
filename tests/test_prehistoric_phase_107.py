from aegis_py.app import AegisApp
from aegis_py.hygiene.bowerbird import BowerbirdBeast


def test_chalicotherium_and_ammonite_influence_policy_gate(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase107_gate.db"))
    try:
        diagnostic = app.diagnose_ingest_attempt(
            "alpha beta gamma",
            type="procedural",
            scope_type="agent",
            scope_id="phase107_scope",
            source_kind="manual",
            source_ref="test://phase107-gate",
            subject="!!!",
            confidence=0.92,
            activation_score=1.0,
        )

        assert diagnostic["target_state"] == "hypothesized"
        assert "chalicotherium_lane_uncertain" in diagnostic["reasons"]
        assert "ammonite_subject_drift_risk" in diagnostic["reasons"]
    finally:
        app.close()


def test_oviraptor_taxonomy_report_surfaces_merge_guidance(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase107_taxonomy.db"))
    try:
        first = app.put_memory(
            "The archive board is checked nightly.",
            type="semantic",
            scope_type="agent",
            scope_id="phase107_scope",
            source_kind="manual",
            source_ref="test://phase107-a",
            subject="release.board",
            confidence=0.95,
        )
        second = app.put_memory(
            "The archive board cabinet is sealed at midnight.",
            type="semantic",
            scope_type="agent",
            scope_id="phase107_scope",
            source_kind="manual",
            source_ref="test://phase107-b",
            subject="release.board.cabinet",
            confidence=0.95,
        )
        assert first is not None
        assert second is not None

        report = BowerbirdBeast(app.storage).build_taxonomy_report()
        assert report["drift_candidates"] >= 1
        assert report["merge_recommendations"]
        assert report["taxonomy_health_band"] in {"ordered", "watchful", "messy"}
    finally:
        app.close()


def test_core_showcase_surfaces_oviraptor_merge_guidance(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase107_showcase.db"))
    try:
        first = app.put_memory(
            "The archive board is checked nightly.",
            type="semantic",
            scope_type="agent",
            scope_id="phase107_scope",
            source_kind="manual",
            source_ref="test://phase107-show-a",
            subject="release.board",
            confidence=0.95,
            metadata={"is_winner": True},
        )
        second = app.put_memory(
            "The archive board cabinet is sealed at midnight.",
            type="semantic",
            scope_type="agent",
            scope_id="phase107_scope",
            source_kind="manual",
            source_ref="test://phase107-show-b",
            subject="release.board.cabinet",
            confidence=0.94,
        )
        assert first is not None
        assert second is not None
        app.storage.execute("DELETE FROM memories_fts")
        app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = app.core_showcase(
            "archive board",
            scope_type="agent",
            scope_id="phase107_scope",
            include_global=False,
        )

        assert payload["result"]["taxonomy_summary"]["merge_recommendations"]
        assert "[Oviraptor Merge Guidance]" in payload["showcase_text"]
    finally:
        app.close()
