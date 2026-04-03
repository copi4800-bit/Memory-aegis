from datetime import datetime, timedelta, timezone
import json

from aegis_py.app import AegisApp
from aegis_py.hygiene.consolidator import ConsolidatorBeast
from aegis_py.mcp.server import AegisMCPServer
from aegis_py.storage.models import Memory


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_diplocaulus_regeneration_surfaces_in_rebuild(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase102_rebuild.db"))
    try:
        app.put_memory(
            "Rebuild anchor memory.",
            type="semantic",
            scope_type="agent",
            scope_id="phase102_scope",
            source_kind="manual",
            source_ref="test://phase102-rebuild",
            subject="rebuild.anchor",
            confidence=0.9,
        )
        result = app.rebuild()

        assert result["fts_rebuilt"] is True
        assert result["diplocaulus_regeneration_score"] > 0.5
    finally:
        app.close()


def test_smilodon_retirement_guidance_surfaces_in_doctor_summary(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "phase102_doctor.db"))
    try:
        memory_id = "phase102_smilodon"
        app.storage.put_memory(
            Memory(
                id=memory_id,
                type="working",
                scope_type="agent",
                scope_id="phase102_scope",
                content="Temporary note that should cool off.",
                source_kind="manual",
                source_ref="test://phase102-doctor",
                subject="temp.note",
                confidence=0.42,
                activation_score=0.2,
                access_count=0,
                metadata={},
            )
        )
        aged_at = _iso_days_ago(14)
        app.storage.execute(
            """
            UPDATE memories
            SET created_at = ?, updated_at = ?, last_accessed_at = ?, activation_score = ?, access_count = ?
            WHERE id = ?
            """,
                (aged_at, aged_at, aged_at, 0.2, 0, memory_id),
            )

        payload = app.doctor()
        summary = app.doctor_summary()

        assert payload["storage"]["smilodon_peak_retirement_pressure"] > 0.7
        assert "Retirement guidance:" in summary
    finally:
        app.close()


def test_glyptodon_consolidation_surfaces_in_core_showcase(tmp_path):
    server = AegisMCPServer(db_path=str(tmp_path / "phase102_showcase.db"))
    try:
        older = server.app.put_memory(
            "The office address is 100 First Street.",
            type="semantic",
            scope_type="agent",
            scope_id="phase102_scope",
            source_kind="manual",
            source_ref="test://phase102-old",
            subject="office.address",
            confidence=0.9,
        )
        newer = server.app.put_memory(
            "Correction: the office address is 200 Second Street.",
            type="semantic",
            scope_type="agent",
            scope_id="phase102_scope",
            source_kind="manual",
            source_ref="test://phase102-new",
            subject="office.address",
            confidence=1.0,
            metadata={"is_winner": True, "is_correction": True},
        )
        old_created = _iso_days_ago(10)
        new_created = _iso_days_ago(1)
        server.app.storage.execute(
            "UPDATE memories SET created_at = ?, updated_at = ? WHERE id = ?",
            (old_created, old_created, older.id),
        )
        server.app.storage.execute(
            "UPDATE memories SET created_at = ?, updated_at = ? WHERE id = ?",
            (new_created, new_created, newer.id),
        )
        server.app.storage.execute(
            """
            INSERT INTO conflicts (
                id, memory_a_id, memory_b_id, subject_key, score, reason, resolution, status, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "phase102_conflict",
                older.id,
                newer.id,
                "office.address",
                0.95,
                "Correction candidate",
                None,
                "open",
                datetime.now(timezone.utc).isoformat(),
                None,
            ),
        )
        ConsolidatorBeast(server.app.storage).resolve_corrections()
        server.app.storage.execute("DELETE FROM memories_fts")
        server.app.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

        payload = json.loads(
            server.run_tool(
                "memory_core_showcase",
                {"query": "office address", "scope_type": "agent", "scope_id": "phase102_scope"},
            )
        )

        assert payload["result"]["consolidation_summary"]["glyptodon_consolidation_shell"] > 0.5
        assert "[Glyptodon Consolidation]" in payload["showcase_text"]
    finally:
        server.close()
