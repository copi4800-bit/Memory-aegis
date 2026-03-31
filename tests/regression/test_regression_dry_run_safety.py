from aegis_py.app import AegisApp


def test_regression_preview_restore_does_not_mutate_durable_state(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "preview-stability.db"

    app = AegisApp(db_path=str(db_path))
    first = app.put_memory(
        "Primary recovery memory.",
        type="semantic",
        scope_type="project",
        scope_id="DRYRUN",
        subject="dryrun.primary",
    )
    second = app.put_memory(
        "This extra memory should survive dry-run preview untouched.",
        type="semantic",
        scope_type="project",
        scope_id="DRYRUN",
        subject="dryrun.secondary",
    )
    assert first is not None and second is not None

    snapshot = app.create_backup(workspace_dir=str(workspace_dir))
    before_counts = app._memory_counts()
    before_hits = app.search_payload("survive dry-run preview", scope_type="project", scope_id="DRYRUN")

    preview = app.preview_restore(snapshot["path"])

    after_counts = app._memory_counts()
    after_hits = app.search_payload("survive dry-run preview", scope_type="project", scope_id="DRYRUN")

    assert preview["dry_run"] is True
    assert before_counts == after_counts
    assert before_hits == after_hits
    app.close()
