from aegis_py.app import AegisApp


def test_regression_background_rollback_restores_pre_apply_neighbor_state(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "rollback-integrity.db"))
    first = app.put_memory(
        "Release checklist depends on gate review.",
        type="semantic",
        scope_type="project",
        scope_id="ROLLBACK",
        subject="release.checklist",
    )
    second = app.put_memory(
        "Gate review protects release checklist quality.",
        type="semantic",
        scope_type="project",
        scope_id="ROLLBACK",
        subject="release.checklist",
    )
    assert first is not None and second is not None

    app.plan_background_intelligence(scope_type="project", scope_id="ROLLBACK")
    run = next(
        item
        for item in app.storage.list_background_intelligence_runs(
            scope_type="project",
            scope_id="ROLLBACK",
            status="planned",
        )
        if item["worker_kind"] == "graph_repair"
    )

    applied = app.apply_background_intelligence_run(run["id"], max_mutations=10)
    after_apply = app.storage.list_memory_neighbors(memory_id=first.id, limit=10)
    rolled_back = app.rollback_background_intelligence_run(run["id"])
    after_rollback = app.storage.list_memory_neighbors(memory_id=first.id, limit=10)
    updated_run = app.storage.get_background_intelligence_run(run["id"])

    assert applied["applied"] is True
    assert any(item["memory"]["id"] == second.id for item in after_apply)
    assert rolled_back["rolled_back"] is True
    assert rolled_back["audit_ids"] == applied["audit_ids"]
    assert not any(item["memory"]["id"] == second.id for item in after_rollback)
    assert updated_run is not None
    assert updated_run["status"] == "discarded"
    assert updated_run["proposal"]["rollback_result"]["run_id"] == run["id"]
    app.close()
