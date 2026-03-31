from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


ADMISSION_STATES = {
    "draft",
    "validated",
    "hypothesized",
    "invalidated",
    "consolidated",
    "archived",
}

RETRIEVABLE_MEMORY_STATUSES = ("active", "crystallized")
RETRIEVABLE_MEMORY_STATUS_SQL = ", ".join(f"'{status}'" for status in RETRIEVABLE_MEMORY_STATUSES)


@dataclass
class Memory:
    id: str
    type: str
    scope_type: str
    scope_id: str
    content: str
    source_kind: str
    summary: str | None = None
    subject: str | None = None
    source_ref: str | None = None
    origin_node_id: str | None = None
    session_id: str | None = None
    status: str = "active"
    confidence: float = 1.0
    activation_score: float = 1.0
    access_count: int = 0
    created_at: datetime = field(default_factory=_now_utc)
    updated_at: datetime = field(default_factory=_now_utc)
    last_accessed_at: datetime | None = None
    expires_at: datetime | None = None
    archived_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def metadata_json(self) -> dict[str, Any]:
        return self.metadata

    @property
    def admission_state(self) -> str | None:
        value = self.metadata.get("admission_state")
        if isinstance(value, str):
            return value
        return None

    @property
    def memory_state(self) -> str | None:
        value = self.metadata.get("memory_state")
        if isinstance(value, str):
            return value
        return None

    def model_dump(self, *, by_alias: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if by_alias:
            payload["metadata_json"] = payload.pop("metadata")
        return payload


@dataclass
class EvidenceEvent:
    id: str
    scope_type: str
    scope_id: str
    raw_content: str
    source_kind: str
    session_id: str | None = None
    source_ref: str | None = None
    memory_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now_utc)

    @property
    def metadata_json(self) -> dict[str, Any]:
        return self.metadata

    def model_dump(self, *, by_alias: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if by_alias:
            payload["metadata_json"] = payload.pop("metadata")
        return payload


@dataclass
class MemoryLink:
    id: str
    source_id: str
    target_id: str
    link_type: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now_utc)

    @property
    def metadata_json(self) -> dict[str, Any]:
        return self.metadata

    def model_dump(self, *, by_alias: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if by_alias:
            payload["metadata_json"] = payload.pop("metadata")
        return payload


@dataclass
class Conflict:
    id: str
    memory_a_id: str
    memory_b_id: str
    subject_key: str | None = None
    score: float = 0.0
    reason: str | None = None
    resolution: str | None = None
    status: str = "open"
    created_at: datetime = field(default_factory=_now_utc)
    resolved_at: datetime | None = None

    def model_dump(self, *, by_alias: bool = False) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StyleSignal:
    id: str
    session_id: str | None = None
    scope_id: str | None = None
    scope_type: str | None = None
    signal_key: str | None = None
    signal_value: Any = None
    agent_id: str | None = None
    signal: str | None = None
    weight: float = 1.0
    created_at: datetime = field(default_factory=_now_utc)

    def model_dump(self, *, by_alias: bool = False) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StyleProfile:
    id: str
    scope_id: str
    scope_type: str
    preferences_json: dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=_now_utc)

    def model_dump(self, *, by_alias: bool = False) -> dict[str, Any]:
        return asdict(self)
