from aegis_py.app import AegisApp


def test_regression_scope_policy_persists_across_reopen_and_allows_sync_export(tmp_path):
    workspace_dir = tmp_path / "sync-workspace"
    workspace_dir.mkdir()
    source_db = tmp_path / "source.db"

    app = AegisApp(db_path=str(source_db))
    app.set_scope_policy("project", "SYNC-REG", sync_policy="sync_eligible", sync_state="local")
    stored = app.put_memory(
        "Persistent sync policy memory.",
        type="semantic",
        scope_type="project",
        scope_id="SYNC-REG",
        subject="sync.regression",
    )
    assert stored is not None
    app.close()

    reopened = AegisApp(db_path=str(source_db))
    policy = reopened.get_scope_policy(scope_type="project", scope_id="SYNC-REG")
    export_payload = reopened.export_sync_envelope(
        scope_type="project",
        scope_id="SYNC-REG",
        workspace_dir=str(workspace_dir),
    )

    assert policy["sync_policy"] == "sync_eligible"
    assert export_payload["records"] == 1
    assert export_payload["scope_id"] == "SYNC-REG"
    reopened.close()
