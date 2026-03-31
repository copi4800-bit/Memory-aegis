from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..retrieval.contract import build_provenance, summarize_reason


VALID_MEMORY_TYPES = {"working", "episodic", "semantic", "procedural"}
VALID_MEMORY_STATUSES = {"active", "archived", "expired", "conflict_candidate", "superseded"}


@dataclass
class Memory:
    id: str | None
    type: str
    scope_type: str
    scope_id: str
    content: str
    source_kind: str
    summary: str | None = None
    subject: str | None = None
    source_ref: str | None = None
    session_id: str | None = None
    status: str = "active"
    confidence: float = 1.0
    activation_score: float = 1.0
    access_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_accessed_at: datetime | None = None
    expires_at: datetime | None = None
    archived_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in VALID_MEMORY_TYPES:
            raise ValueError(f"Invalid memory type: {self.type}")
        if self.status not in VALID_MEMORY_STATUSES:
            raise ValueError(f"Invalid memory status: {self.status}")
        if not self.scope_type or not self.scope_id:
            raise ValueError("scope_type and scope_id are required")
        if not self.source_kind:
            raise ValueError("source_kind is required")


@dataclass
class SearchResult:
    id: str
    type: str
    content: str
    summary: str | None
    subject: str | None
    score: float
    reasons: list[str]
    source_kind: str
    source_ref: str | None
    scope_type: str
    scope_id: str
    conflict_status: str

    @property
    def reason(self) -> str:
        return summarize_reason(
            memory_type=self.type,
            activation_score=1.0,
            conflict_status=self.conflict_status,
        )

    @property
    def provenance(self) -> str:
        return build_provenance(self.source_kind, self.source_ref)


@dataclass
class MemoryLink:
    id: str
    source_id: str
    target_id: str
    link_type: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
