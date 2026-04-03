import json

from aegis_py.mcp.server import AegisMCPServer
from aegis_py.storage.models import Memory


def test_storage_footprint_surfaces_deinosuchus_and_titanoboa(runtime_harness):
    runtime_harness.put(
        Memory(
            id="phase100_archived",
            type="semantic",
            scope_type="agent",
            scope_id="phase100_scope",
            content="Old archived note.",
            source_kind="manual",
            subject="archive.old",
            confidence=0.8,
            activation_score=0.2,
            status="archived",
            metadata={},
        )
    )
    runtime_harness.put(
        Memory(
            id="phase100_superseded",
            type="semantic",
            scope_type="agent",
            scope_id="phase100_scope",
            content="Old superseded note.",
            source_kind="manual",
            subject="archive.old",
            confidence=0.8,
            activation_score=0.2,
            status="superseded",
            metadata={},
        )
    )
    for index in range(3):
        runtime_harness.put(
            Memory(
                id=f"phase100_cluster_{index}",
                type="semantic",
                scope_type="agent",
                scope_id="phase100_scope",
                content=f"Cluster note {index}",
                source_kind="manual",
                subject="cluster.subject",
                confidence=0.9,
                activation_score=1.0,
                metadata={},
            )
        )

    footprint = runtime_harness.storage.storage_footprint()
    assert "prehistoric_storage" not in footprint

    from aegis_py.app import AegisApp

    app = AegisApp(db_path=runtime_harness.storage.db_path)
    try:
        enriched = app.storage_footprint(scope_type="agent", scope_id="phase100_scope")
    finally:
        app.close()

    prehistoric = enriched["prehistoric_storage"]
    assert prehistoric["deinosuchus_compaction_pressure"] > 0.4
    assert prehistoric["titanoboa_index_locality"]["densest_cluster"] >= 3
    assert prehistoric["titanoboa_index_locality"]["titanoboa_index_locality"] > 0.5


def test_core_showcase_surfaces_argentinosaurus_and_prehistoric_storage(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "phase100_showcase.db"))
    try:
        old_stored = server.app.put_memory(
            "The backup window is Monday.",
            type="semantic",
            scope_type="agent",
            scope_id="phase100_showcase",
            source_kind="manual",
            source_ref="test://phase100-old",
            subject="backup_window",
            confidence=0.9,
        )
        current_stored = server.app.put_memory(
            "Correction: the backup window moved to Tuesday.",
            type="semantic",
            scope_type="agent",
            scope_id="phase100_showcase",
            source_kind="manual",
            source_ref="test://phase100-new",
            subject="backup_window",
            confidence=1.0,
            metadata={"is_winner": True, "is_correction": True},
        )
        assert old_stored is not None
        assert current_stored is not None
        server.app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
        for index in range(3):
            server.app.put_memory(
                f"Cluster backup note {index}",
                type="semantic",
                scope_type="agent",
                scope_id="phase100_showcase",
                source_kind="manual",
                source_ref=f"test://phase100-cluster-{index}",
                subject="backup_window",
                confidence=0.82,
            )
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = json.loads(
            server.run_tool(
                "memory_core_showcase",
                {
                    "query": "backup window",
                    "scope_type": "agent",
                    "scope_id": "phase100_showcase",
                    "intent": "correction_lookup",
                },
            )
        )

        result = payload["result"]
        assert result["scope_summary"]["argentinosaurus_scope_geometry"] > 0.55
        assert result["storage_summary"]["deinosuchus_compaction_pressure"] >= 0.28
        assert result["storage_summary"]["titanoboa_index_locality"]["densest_cluster"] >= 3
        assert "[Argentinosaurus Scope]" in payload["showcase_text"]
        assert "[Prehistoric Storage]" in payload["showcase_text"]
    finally:
        server.close()
