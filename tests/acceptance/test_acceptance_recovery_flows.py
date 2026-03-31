from aegis_py.app import AegisApp


def test_acceptance_backup_preview_and_restore_on_separate_db(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"

    source = AegisApp(db_path=str(source_db))
    stored = source.put_memory(
        "Release notes must be reviewed before publish.",
        type="semantic",
        scope_type="project",
        scope_id="RECOVERY",
        source_kind="manual",
        source_ref="runbook#release-notes",
        subject="release.notes",
    )
    assert stored is not None

    backup_payload = source.create_backup(workspace_dir=str(workspace_dir))
    preview_payload = source.preview_restore(backup_payload["path"])
    assert backup_payload["mode"] == "snapshot"
    assert backup_payload["path"].endswith(".db")
    assert preview_payload["dry_run"] is True
    source.close()

    target = AegisApp(db_path=str(target_db))
    restored = target.restore_backup(backup_payload["path"])
    hits = target.search_payload("release notes", scope_type="project", scope_id="RECOVERY")
    assert restored["restored"] is True
    assert len(hits) == 1
    assert hits[0]["memory"]["subject"] == "release.notes"
    target.close()
