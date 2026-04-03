from aegis_py.app import AegisApp


def test_oviraptor_profile_surfaces_in_diagnostic_and_policy(tmp_path):
    app = AegisApp(str(tmp_path / "phase112.db"))
    try:
        existing = app.put_memory(
            "The archive board is checked nightly.",
            type="semantic",
            scope_type="agent",
            scope_id="phase112_scope",
            source_kind="manual",
            source_ref="test://phase112-existing",
            subject="release.board",
            confidence=0.95,
        )
        assert existing is not None

        diagnostic = app.diagnose_ingest_attempt(
            "The archive board cabinet is sealed at midnight.",
            type="semantic",
            scope_type="agent",
            scope_id="phase112_scope",
            source_kind="manual",
            source_ref="test://phase112-new",
            subject="release.board.cabinet",
            confidence=0.95,
            activation_score=1.0,
        )

        assert diagnostic["oviraptor_profile"]["closest_subject"] == "release.board"
        assert diagnostic["oviraptor_profile"]["taxonomy_guard"] in {"watchful", "drift_risk"}
        assert diagnostic["target_state"] == "hypothesized"
        assert "oviraptor_subject_drift_guard" in diagnostic["reasons"] or "oviraptor_subject_watchful" in diagnostic["reasons"]
    finally:
        app.close()
