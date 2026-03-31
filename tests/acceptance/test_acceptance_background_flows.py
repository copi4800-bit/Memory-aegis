from aegis_py.app import AegisApp


def test_acceptance_background_apply_and_rollback_round_trip(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "acceptance-background.db"))
    first = app.put_memory(
        "Release checklist depends on gate review.",
        type="semantic",
        scope_type="project",
        scope_id="BG-ACCEPT",
        subject="release.checklist",
    )
    second = app.put_memory(
        "Gate review protects release checklist quality.",
        type="semantic",
        scope_type="project",
        scope_id="BG-ACCEPT",
        subject="release.checklist",
    )
    assert first is not None and second is not None

    plan = app.plan_background_intelligence(scope_type="project", scope_id="BG-ACCEPT")
    runs = app.storage.list_background_intelligence_runs(
        scope_type="project",
        scope_id="BG-ACCEPT",
        status="planned",
    )
    graph_run = next(run for run in runs if run["worker_kind"] == "graph_repair")

    applied = app.apply_background_intelligence_run(graph_run["id"], max_mutations=10)
    neighbors_after_apply = app.storage.list_memory_neighbors(memory_id=first.id, limit=10)
    rolled_back = app.rollback_background_intelligence_run(graph_run["id"])
    neighbors_after_rollback = app.storage.list_memory_neighbors(memory_id=first.id, limit=10)

    assert plan["proposal_count"] >= 1
    assert applied["applied"] is True
    assert any(item["memory"]["id"] == second.id for item in neighbors_after_apply)
    assert rolled_back["rolled_back"] is True
    assert not any(item["memory"]["id"] == second.id for item in neighbors_after_rollback)
    app.close()
