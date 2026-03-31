from aegis_py.app import AegisApp


def test_regression_backup_preview_keeps_scope_counts_and_revisions_stable(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "preview-stability.db"

    app = AegisApp(db_path=str(db_path))
    app.put_memory(
        "Preview stability memory.",
        type="semantic",
        scope_type="project",
        scope_id="PREVIEW",
        subject="preview.stability",
    )
    backup = app.create_backup(workspace_dir=str(workspace_dir))

    before_counts = app._memory_counts(scope_filter={"scope_type": "project", "scope_id": "PREVIEW"})
    before_revision = app.storage.get_scope_revision("project", "PREVIEW")

    preview = app.preview_restore(
        backup["path"],
        scope_type="project",
        scope_id="PREVIEW",
    )

    after_counts = app._memory_counts(scope_filter={"scope_type": "project", "scope_id": "PREVIEW"})
    after_revision = app.storage.get_scope_revision("project", "PREVIEW")

    assert preview["dry_run"] is True
    assert before_counts == after_counts
    assert before_revision == after_revision
    app.close()
