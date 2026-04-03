from datetime import datetime, timedelta, timezone
import json

from aegis_py.hygiene.axolotl import AxolotlBeast
from aegis_py.hygiene.consolidator import ConsolidatorBeast
from aegis_py.hygiene.decay import DecayBeast
from aegis_py.storage.models import Memory


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_diplocaulus_regeneration_score_surfaces_from_integrity_report(runtime_harness):
    axolotl = AxolotlBeast(runtime_harness.storage)

    report = axolotl.validate_integrity()

    assert report.fts_rebuilt is True
    assert report.diplocaulus_regeneration_score > 0.5


def test_smilodon_retirement_pressure_ranks_old_cold_memories(runtime_harness):
    memory = runtime_harness.put(
        Memory(
            id="smilodon_candidate",
            type="working",
            scope_type="agent",
            scope_id="prehistoric_tranche5",
            content="Temporary note that should expire soon.",
            source_kind="manual",
            subject="temp.note",
            confidence=0.42,
            activation_score=0.25,
            access_count=0,
            metadata={"memory_state": "validated", "admission_state": "validated"},
        )
    )
    aged_at = _iso_days_ago(14)
    runtime_harness.storage.execute(
        """
        UPDATE memories
        SET created_at = ?, updated_at = ?, last_accessed_at = ?
        WHERE id = ?
        """,
        (aged_at, aged_at, aged_at, memory.id),
    )

    decay = DecayBeast(runtime_harness.storage)
    candidates = decay.evaluate_retirement_candidates()
    top = next(item for item in candidates if item["memory_id"] == "smilodon_candidate")

    assert top["smilodon_retirement_pressure"] > 0.7


def test_glyptodon_consolidation_shell_surfaces_on_correction_resolution(runtime_harness):
    older = runtime_harness.put(
        Memory(
            id="glyptodon_old",
            type="semantic",
            scope_type="agent",
            scope_id="prehistoric_tranche5",
            content="The office address is 100 First Street.",
            source_kind="manual",
            subject="office.address",
            confidence=0.9,
            activation_score=0.9,
            metadata={},
        )
    )
    newer = runtime_harness.put(
        Memory(
            id="glyptodon_new",
            type="semantic",
            scope_type="agent",
            scope_id="prehistoric_tranche5",
            content="Correction: the office address is 200 Second Street.",
            source_kind="manual",
            subject="office.address",
            confidence=1.0,
            activation_score=1.0,
            metadata={},
        )
    )
    old_created = _iso_days_ago(10)
    new_created = _iso_days_ago(1)
    runtime_harness.storage.execute(
        "UPDATE memories SET created_at = ?, updated_at = ? WHERE id = ?",
        (old_created, old_created, older.id),
    )
    runtime_harness.storage.execute(
        "UPDATE memories SET created_at = ?, updated_at = ? WHERE id = ?",
        (new_created, new_created, newer.id),
    )
    runtime_harness.storage.execute(
        """
        INSERT INTO conflicts (
            id, memory_a_id, memory_b_id, subject_key, score, reason, resolution, status, created_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "glyptodon_conflict",
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

    consolidator = ConsolidatorBeast(runtime_harness.storage)
    resolved = consolidator.resolve_corrections()
    newer_row = runtime_harness.storage.fetch_one("SELECT metadata_json, status FROM memories WHERE id = ?", (newer.id,))
    older_row = runtime_harness.storage.fetch_one("SELECT status FROM memories WHERE id = ?", (older.id,))
    metadata = json.loads(newer_row["metadata_json"])

    assert resolved >= 1
    assert older_row["status"] == "superseded"
    assert newer_row["status"] == "active"
    assert metadata["glyptodon_consolidation_shell"] > 0.5
    assert older.id in metadata["corrected_from"]

