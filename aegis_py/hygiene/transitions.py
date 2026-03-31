from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def coerce_metadata(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    return dict(raw)


def append_lifecycle_event(
    db: Any,
    memory_id: str,
    event: str,
    *,
    details: dict[str, Any] | None = None,
    at: str | None = None,
) -> bool:
    row = db.fetch_one("SELECT metadata_json FROM memories WHERE id = ?", (memory_id,))
    if row is None:
        return False
    metadata = coerce_metadata(row["metadata_json"])
    lifecycle_events = metadata.setdefault("lifecycle_events", [])
    lifecycle_events.append({"event": event, "at": at or now_iso(), **(details or {})})
    db.execute(
        "UPDATE memories SET metadata_json = ?, updated_at = ? WHERE id = ?",
        (json.dumps(metadata, ensure_ascii=True), at or now_iso(), memory_id),
    )
    return True


def transition_memory(
    db: Any,
    memory_id: str,
    *,
    status: str,
    event: str,
    archived_at: str | None = None,
    expires_at: str | None = None,
    details: dict[str, Any] | None = None,
    at: str | None = None,
) -> bool:
    row = db.fetch_one("SELECT metadata_json FROM memories WHERE id = ?", (memory_id,))
    if row is None:
        return False
    timestamp = at or now_iso()
    metadata = coerce_metadata(row["metadata_json"])
    lifecycle_events = metadata.setdefault("lifecycle_events", [])
    lifecycle_events.append({"event": event, "at": timestamp, **(details or {})})
    db.execute(
        """
        UPDATE memories
        SET status = ?,
            archived_at = COALESCE(?, archived_at),
            expires_at = COALESCE(?, expires_at),
            updated_at = ?,
            metadata_json = ?
        WHERE id = ?
        """,
        (
            status,
            archived_at,
            expires_at,
            timestamp,
            json.dumps(metadata, ensure_ascii=True),
            memory_id,
        ),
    )
    return True
