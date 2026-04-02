from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aegis_py.storage.models import Memory


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_dormant_semantic_memory_is_archived_after_90_days(runtime_harness):
    memory = runtime_harness.put(
        Memory(
            id="mem_dormant_semantic",
            type="semantic",
            scope_type="agent",
            scope_id="retention_probe",
            content="Dormant office preference note that should eventually cool off.",
            source_kind="manual",
            subject="office.preference",
            confidence=0.78,
            activation_score=0.39,
            metadata={"memory_state": "validated", "admission_state": "validated"},
        )
    )
    aged_at = _iso_days_ago(95)
    runtime_harness.storage.execute(
        """
        UPDATE memories
        SET updated_at = ?, last_accessed_at = ?, created_at = ?
        WHERE id = ?
        """,
        (aged_at, aged_at, aged_at, memory.id),
    )

    runtime_harness.storage.apply_retention_policy()
    archived = runtime_harness.storage.get_memory(memory.id)

    assert archived is not None
    assert archived.status == "archived"
    assert archived.metadata["retention_stage"] == "archive_candidate"


def test_winner_semantic_memory_survives_dormancy_guard(runtime_harness):
    memory = runtime_harness.put(
        Memory(
            id="mem_winner_semantic",
            type="semantic",
            scope_type="agent",
            scope_id="retention_probe",
            content="Current office address winner memory.",
            source_kind="manual",
            subject="office.address",
            confidence=1.0,
            activation_score=0.39,
            metadata={
                "memory_state": "validated",
                "admission_state": "validated",
                "is_winner": True,
            },
        )
    )
    aged_at = _iso_days_ago(95)
    runtime_harness.storage.execute(
        """
        UPDATE memories
        SET updated_at = ?, last_accessed_at = ?, created_at = ?
        WHERE id = ?
        """,
        (aged_at, aged_at, aged_at, memory.id),
    )

    runtime_harness.storage.apply_retention_policy()
    survivor = runtime_harness.storage.get_memory(memory.id)

    assert survivor is not None
    assert survivor.status == "active"
    assert survivor.metadata["retention_stage"] == "cold"
