from aegis_py.app import AegisApp
from aegis_py.hygiene.axolotl import RepairReport
from aegis_py.hygiene.engine import HygieneEngine
from aegis_py.storage.models import Memory, StyleProfile


def test_hygiene_engine_uses_diplocaulus_and_deinosuchus_to_control_maintenance(tmp_path, monkeypatch):
    app = AegisApp(str(tmp_path / "phase114_maintenance.db"))
    try:
        engine = HygieneEngine(app.storage)
        called: list[str] = []

        monkeypatch.setattr(
            engine.axolotl,
            "validate_integrity",
            lambda: RepairReport(
                schema_repaired=0,
                fts_rebuilt=True,
                orphan_links_removed=0,
                diplocaulus_regeneration_score=0.61,
            ),
        )
        monkeypatch.setattr(engine.decay_beast, "apply_typed_decay", lambda: called.append("decay"))
        monkeypatch.setattr(engine.decay_beast, "crystallize_hot_memories", lambda: called.append("crystallize"))
        monkeypatch.setattr(engine.decay_beast, "retire_pressure_candidates", lambda threshold=0.82: called.append("smilodon"))
        monkeypatch.setattr(app.storage, "apply_retention_policy", lambda: called.append("retention"))
        monkeypatch.setattr(app.storage, "archive_expired", lambda *args, **kwargs: called.append("archive"))
        monkeypatch.setattr(engine.bowerbird, "normalize_subjects", lambda: called.append("taxonomy"))
        monkeypatch.setattr(engine, "_detect_and_resolve_conflicts", lambda: called.append("conflicts"))
        monkeypatch.setattr(engine, "_consolidate_all_subjects", lambda: called.append("consolidate"))

        class _Health:
            deinosuchus_compaction_pressure = 0.72

        monkeypatch.setattr(engine.nutcracker, "check_db_health", lambda: _Health())
        monkeypatch.setattr(engine.nutcracker, "vacuum_db", lambda: called.append("vacuum"))

        engine.run_maintenance()

        assert "taxonomy" in called
        assert "conflicts" in called
        assert "consolidate" in called
        assert "vacuum" in called
        assert "smilodon" in called
    finally:
        app.close()


def test_smilodon_retires_high_pressure_memory(tmp_path):
    app = AegisApp(str(tmp_path / "phase114_smilodon.db"))
    try:
        memory_id = "phase114_smilo"
        app.storage.put_memory(
            Memory(
                id=memory_id,
                type="working",
                scope_type="agent",
                scope_id="phase114_scope",
                content="A stale working note that should retire.",
                source_kind="manual",
                source_ref="test://phase114-smilo",
                subject="stale.note",
                confidence=0.25,
                activation_score=0.12,
                access_count=0,
                metadata={},
            )
        )
        app.storage.execute(
            """
            UPDATE memories
            SET created_at = datetime('now', '-30 day'),
                updated_at = datetime('now', '-30 day'),
                last_accessed_at = datetime('now', '-30 day')
            WHERE id = ?
            """,
            (memory_id,),
        )

        retired = app.hygiene_engine.decay_beast.retire_pressure_candidates(threshold=0.7)
        row = app.storage.fetch_one("SELECT status, archived_at FROM memories WHERE id = ?", (memory_id,))

        assert retired == 1
        assert row["status"] == "archived"
        assert row["archived_at"] is not None
    finally:
        app.close()


def test_remaining_pipeline_beasts_now_shape_judged_recall(tmp_path):
    app = AegisApp(str(tmp_path / "phase114_recall.db"))
    try:
        app.storage.upsert_profile(
            StyleProfile(
                id="phase114_profile",
                scope_id="phase114_scope",
                scope_type="agent",
                preferences_json={
                    "user_honorific": "anh",
                    "assistant_honorific": "em",
                    "preferred_format": "markdown",
                    "tone": "precise",
                    "verbosity": 0.86,
                },
            )
        )
        target = app.put_memory(
            content="The deployment owner is Harbor Team and the release checklist lives beside the harbor board.",
            type="semantic",
            scope_type="agent",
            scope_id="phase114_scope",
            source_kind="manual",
            source_ref="test://phase114-target",
            subject="deploy.owner",
            confidence=0.98,
            metadata={
                "is_winner": True,
                "glyptodon_consolidation_shell": 0.84,
            },
        )
        peer = app.put_memory(
            content="Harbor Team keeps the release board checklist aligned with deployment ownership.",
            type="procedural",
            scope_type="agent",
            scope_id="phase114_scope",
            source_kind="manual",
            source_ref="test://phase114-peer",
            subject="deploy.owner",
            confidence=0.92,
        )
        archived = app.put_memory(
            content="Old deployment note for archive pressure.",
            type="semantic",
            scope_type="agent",
            scope_id="phase114_scope",
            source_kind="manual",
            source_ref="test://phase114-archived",
            subject="deploy.owner",
            confidence=0.6,
        )
        assert target is not None and peer is not None and archived is not None
        app.storage.execute("UPDATE memories SET status = 'archived' WHERE id = ?", (archived.id,))
        app.storage.upsert_memory_link(
            source_id=target.id,
            target_id=peer.id,
            link_type="supports",
            weight=0.93,
            metadata={"rule": "phase114-topology"},
        )
        app.storage.execute("DELETE FROM memories_fts")
        app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        query = type(
            "Query",
            (),
            {
                "query": "deployment owner harbor board checklist",
                "scope_type": "agent",
                "scope_id": "phase114_scope",
                "limit": 10,
                "include_global": False,
                "min_score": -10.0,
                "intent": "normal_recall",
                "scoring_mode": "v10_primary",
            },
        )()
        results = app.search_pipeline.search(query)
        assert results
        chosen = next(item for item in results if item.memory.id == target.id)

        factors = chosen.v10_trace.factors
        reasons = chosen.v10_decision.decision_reason
        assert factors.get("glyptodon_judged_pressure", 0.0) > 0.0
        assert factors.get("megarachne_judged_pressure", 0.0) > 0.0
        assert factors.get("titanoboa_judged_pressure", 0.0) > 0.0
        assert factors.get("dire_wolf_judged_pressure", 0.0) > 0.0
        assert "deinosuchus_judged_pressure" in reasons
    finally:
        app.close()
