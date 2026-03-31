from aegis_py.app import AegisApp


def test_acceptance_sync_export_preview_import_round_trip(tmp_path):
    workspace_dir = tmp_path / "sync-workspace"
    workspace_dir.mkdir()
    source_db = tmp_path / "sync-source.db"
    target_db = tmp_path / "sync-target.db"

    source = AegisApp(db_path=str(source_db))
    source.set_scope_policy("project", "SYNC-ACCEPT", sync_policy="sync_eligible", sync_state="local")
    stored = source.put_memory(
        "Portable sync memory for acceptance coverage.",
        type="semantic",
        scope_type="project",
        scope_id="SYNC-ACCEPT",
        source_kind="manual",
        subject="sync.acceptance",
    )
    assert stored is not None
    export_payload = source.export_sync_envelope(
        scope_type="project",
        scope_id="SYNC-ACCEPT",
        workspace_dir=str(workspace_dir),
    )
    source.close()

    target = AegisApp(db_path=str(target_db))
    target.set_scope_policy("project", "SYNC-ACCEPT", sync_policy="sync_eligible", sync_state="local")
    preview_payload = target.preview_sync_envelope(export_payload["path"])
    import_payload = target.import_sync_envelope(export_payload["path"])
    hits = target.search_payload("Portable sync memory", scope_type="project", scope_id="SYNC-ACCEPT")

    assert export_payload["records"] == 1
    assert preview_payload["dry_run"] is True
    assert preview_payload["new_records"] == 1
    assert import_payload["records"] == 1
    assert len(hits) == 1
    assert hits[0]["memory"]["subject"] == "sync.acceptance"
    target.close()
