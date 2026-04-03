from aegis_py.memory.consumer import (
    prepare_consumer_correction_metadata,
    prepare_consumer_remember_metadata,
    resolve_consumer_remember_outcome,
)


def test_prepare_consumer_remember_metadata_marks_slot_collision():
    metadata = prepare_consumer_remember_metadata(
        content="Address is District 7",
        subject="user.address",
        scope_id="default",
        scope_type="agent",
        metadata={},
        fetch_active_contents=lambda subject, scope_id, scope_type: ["Address is District 1"],
    )

    assert metadata["conflict_candidate"] is True
    assert metadata["requires_review"] is True
    assert metadata["is_winner"] is False


def test_prepare_consumer_remember_metadata_keeps_default_winner_without_collision():
    metadata = prepare_consumer_remember_metadata(
        content="Favorite color is blue",
        subject="user.favorite_color",
        scope_id="default",
        scope_type="agent",
        metadata=None,
        fetch_active_contents=lambda subject, scope_id, scope_type: [],
    )

    assert metadata["is_winner"] is True
    assert "conflict_candidate" not in metadata


def test_prepare_consumer_correction_metadata_prefers_subject_lookup():
    metadata = prepare_consumer_correction_metadata(
        subject="user.favorite_color",
        old_content_hint=None,
        scope_id="default",
        scope_type="agent",
        fetch_active_ids_by_subject=lambda subject, scope_id, scope_type: ["old_1", "old_2"],
        search_ids_by_hint=lambda hint, scope_id, scope_type: ["search_old"],
    )

    assert metadata["is_correction"] is True
    assert metadata["is_winner"] is True
    assert metadata["corrected_from"] == ["old_1", "old_2"]


def test_prepare_consumer_correction_metadata_falls_back_to_search_hint():
    metadata = prepare_consumer_correction_metadata(
        subject=None,
        old_content_hint="old color",
        scope_id="default",
        scope_type="agent",
        fetch_active_ids_by_subject=lambda subject, scope_id, scope_type: [],
        search_ids_by_hint=lambda hint, scope_id, scope_type: ["search_old"],
    )

    assert metadata["corrected_from"] == ["search_old"]


def test_resolve_consumer_remember_outcome_prefers_stored_memory_id():
    outcome = resolve_consumer_remember_outcome(
        stored_memory_id="mem_123",
        content="Favorite color is blue",
        subject="user.favorite_color",
        scope_id="default",
        scope_type="agent",
        fetch_exact_duplicate_ids=lambda content, scope_id, scope_type: ["dup_1"],
        fetch_active_ids_by_subject=lambda subject, scope_id, scope_type: ["slot_1"],
    )

    assert outcome == "mem_123"


def test_resolve_consumer_remember_outcome_falls_back_to_duplicate_then_slot():
    duplicate_outcome = resolve_consumer_remember_outcome(
        stored_memory_id=None,
        content="Favorite color is blue",
        subject="user.favorite_color",
        scope_id="default",
        scope_type="agent",
        fetch_exact_duplicate_ids=lambda content, scope_id, scope_type: ["dup_1"],
        fetch_active_ids_by_subject=lambda subject, scope_id, scope_type: ["slot_1"],
    )
    slot_outcome = resolve_consumer_remember_outcome(
        stored_memory_id=None,
        content="Favorite color is blue",
        subject="user.favorite_color",
        scope_id="default",
        scope_type="agent",
        fetch_exact_duplicate_ids=lambda content, scope_id, scope_type: [],
        fetch_active_ids_by_subject=lambda subject, scope_id, scope_type: ["slot_1"],
    )

    assert duplicate_outcome == "dup_1"
    assert slot_outcome == "slot_1"


def test_resolve_consumer_remember_outcome_returns_policy_rejection_when_empty():
    outcome = resolve_consumer_remember_outcome(
        stored_memory_id=None,
        content="Favorite color is blue",
        subject="user.favorite_color",
        scope_id="default",
        scope_type="agent",
        fetch_exact_duplicate_ids=lambda content, scope_id, scope_type: [],
        fetch_active_ids_by_subject=lambda subject, scope_id, scope_type: [],
    )

    assert outcome == "rejected_by_policy"
