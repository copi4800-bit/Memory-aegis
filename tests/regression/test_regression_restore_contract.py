from aegis_py.app import AegisApp


def test_regression_restore_contract_rehydrates_expected_records_on_separate_db(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    source_db = tmp_path / "source.db"
    target_db = tmp_path / "target.db"

    source = AegisApp(db_path=str(source_db))
    source.put_memory(
        "Restore contract memory one.",
        type="semantic",
        scope_type="project",
        scope_id="RESTORE",
        subject="restore.one",
    )
    source.put_memory(
        "Restore contract memory two.",
        type="semantic",
        scope_type="project",
        scope_id="RESTORE",
        subject="restore.two",
    )
    snapshot = source.create_backup(workspace_dir=str(workspace_dir))
    source.close()

    target = AegisApp(db_path=str(target_db))
    before_counts = target._memory_counts()
    restored = target.restore_backup(snapshot["path"])
    after_counts = target._memory_counts()
    hits = target.search_payload("Restore contract memory", scope_type="project", scope_id="RESTORE")

    assert before_counts.get("active", 0) == 0
    assert restored["restored"] is True
    assert after_counts.get("active", 0) == 2
    assert len(hits) == 2
    assert {item["memory"]["subject"] for item in hits} == {"restore.one", "restore.two"}
    target.close()
