from __future__ import annotations

from typing import Any, Callable


def prepare_consumer_remember_metadata(
    *,
    content: str,
    subject: str | None,
    scope_id: str,
    scope_type: str,
    metadata: dict[str, Any] | None,
    fetch_active_contents: Callable[[str, str, str], list[str]],
) -> dict[str, Any]:
    """Builds consumer-facing remember metadata without exposing write-path heuristics to the facade."""
    prepared = dict(metadata or {})

    if "is_winner" not in prepared:
        prepared["is_winner"] = True

    if subject and not prepared.get("is_correction"):
        active_contents = fetch_active_contents(subject, scope_id, scope_type)
        if active_contents and any(existing_content != content for existing_content in active_contents):
            prepared["conflict_candidate"] = True
            prepared["requires_review"] = True
            prepared["is_winner"] = False

    return prepared


def prepare_consumer_correction_metadata(
    *,
    subject: str | None,
    old_content_hint: str | None,
    scope_id: str,
    scope_type: str,
    fetch_active_ids_by_subject: Callable[[str, str, str], list[str]],
    search_ids_by_hint: Callable[[str, str, str], list[str]],
) -> dict[str, Any]:
    """Builds correction metadata for consumer write flows."""
    old_ids: list[str] = []
    if subject:
        old_ids = fetch_active_ids_by_subject(subject, scope_id, scope_type)
    elif old_content_hint:
        old_ids = search_ids_by_hint(old_content_hint, scope_id, scope_type)

    return {
        "is_correction": True,
        "is_winner": True,
        "corrected_from": old_ids,
    }


def resolve_consumer_remember_outcome(
    *,
    stored_memory_id: str | None,
    content: str,
    subject: str | None,
    scope_id: str,
    scope_type: str,
    fetch_exact_duplicate_ids: Callable[[str, str, str], list[str]],
    fetch_active_ids_by_subject: Callable[[str, str, str], list[str]],
) -> str:
    """Resolves the consumer-facing remember outcome after the ingest engine returns."""
    if stored_memory_id:
        return stored_memory_id

    duplicate_ids = fetch_exact_duplicate_ids(content, scope_id, scope_type)
    if duplicate_ids:
        return duplicate_ids[0]

    if subject:
        slot_ids = fetch_active_ids_by_subject(subject, scope_id, scope_type)
        if slot_ids:
            return slot_ids[0]

    return "rejected_by_policy"
