from aegis_py.app import AegisApp


def test_diagnose_ingest_attempt_reports_policy_block(tmp_path):
    app = AegisApp(str(tmp_path / "admission_diag_block.db"))
    try:
        diagnostic = app.diagnose_ingest_attempt(
            "Repeated ingest payload 0 for admission pressure.",
            type="semantic",
            scope_type="agent",
            scope_id="diag_scope",
            source_kind="manual",
            source_ref="test://diag-block",
            subject="ingest.pressure",
            confidence=0.4,
            activation_score=1.0,
        )

        assert diagnostic["outcome"] == "policy_block"
        assert diagnostic["target_state"] == "draft"
        assert "blocked_low_confidence" in diagnostic["reasons"]
    finally:
        app.close()


def test_diagnose_ingest_attempt_reports_exact_dedup(tmp_path):
    app = AegisApp(str(tmp_path / "admission_diag_dedup.db"))
    try:
        stored = app.put_memory(
            "The build color is blue.",
            type="semantic",
            scope_type="agent",
            scope_id="diag_scope",
            source_kind="manual",
            source_ref="test://diag-dedup/original",
            subject="build.color",
            confidence=0.95,
            activation_score=1.0,
        )

        diagnostic = app.diagnose_ingest_attempt(
            "The build color is blue.",
            type="semantic",
            scope_type="agent",
            scope_id="diag_scope",
            source_kind="manual",
            source_ref="test://diag-dedup/repeat",
            subject="build.color",
            confidence=0.95,
            activation_score=1.0,
        )

        assert stored is not None
        assert diagnostic["outcome"] == "exact_dedup"
        assert diagnostic["reason_code"] == "exact_content_scope_match"
        assert diagnostic["exact_duplicate_id"] == stored.id
    finally:
        app.close()
