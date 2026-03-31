from aegis_py.app import AegisApp


def test_acceptance_scope_isolation_prevents_cross_scope_recall_and_sync_leakage(tmp_path):
    workspace_dir = tmp_path / "scope-sync-workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "scope-isolation.db"

    app = AegisApp(db_path=str(db_path))
    local = app.put_memory(
        "Local-only project memory.",
        type="semantic",
        scope_type="project",
        scope_id="LOCAL",
        subject="scope.local",
        source_kind="manual",
    )
    shared = app.put_memory(
        "Shared project memory.",
        type="semantic",
        scope_type="project",
        scope_id="SHARED",
        subject="scope.shared",
        source_kind="manual",
    )
    assert local is not None and shared is not None

    app.set_scope_policy("project", "SHARED", sync_policy="sync_eligible", sync_state="local")

    local_hits = app.search_payload("project memory", scope_type="project", scope_id="LOCAL")
    shared_hits = app.search_payload("project memory", scope_type="project", scope_id="SHARED")
    export_payload = app.export_sync_envelope(
        scope_type="project",
        scope_id="SHARED",
        workspace_dir=str(workspace_dir),
    )

    assert len(local_hits) == 1
    assert local_hits[0]["memory"]["subject"] == "scope.local"
    assert len(shared_hits) == 1
    assert shared_hits[0]["memory"]["subject"] == "scope.shared"
    assert export_payload["records"] == 1

    app.close()
