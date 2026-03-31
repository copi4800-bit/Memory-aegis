from __future__ import annotations

from dataclasses import dataclass, field

from .contract import build_provenance, derive_trust_shape, summarize_reason
from ..storage.models import Memory


@dataclass
class SearchResult:
    memory: Memory
    score: float
    reasons: list[str] = field(default_factory=list)
    source_kind: str = ""
    source_ref: str | None = None
    scope_type: str = ""
    scope_id: str = ""
    conflict_status: str = "none"
    admission_state: str = "validated"
    retrieval_stage: str = "lexical"
    relation_via_subject: str | None = None
    relation_via_link_type: str | None = None
    relation_via_memory_id: str | None = None
    relation_via_link_metadata: dict[str, object] | None = None
    relation_via_hops: int | None = None
    v8_core_signals: dict[str, object] | None = None
    # Danh sách Why-not (Chuẩn 6.md)
    suppressed_candidates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def reason(self) -> str:
        return summarize_reason(
            memory_type=self.memory.type,
            activation_score=self.memory.activation_score,
            conflict_status=self.conflict_status,
        )

    @property
    def provenance(self) -> str:
        return build_provenance(self.source_kind, self.source_ref)

    @property
    def trust_state(self) -> str:
        score_profile = self.memory.metadata.get("score_profile", {}) if isinstance(self.memory.metadata, dict) else {}
        state, _ = derive_trust_shape(
            score=self.score,
            conflict_status=self.conflict_status,
            retrieval_stage=self.retrieval_stage,
            activation_score=self.memory.activation_score,
            confidence=self.memory.confidence,
            admission_state=self.admission_state,
            score_profile=score_profile,
        )
        return state

    @property
    def trust_reason(self) -> str:
        score_profile = self.memory.metadata.get("score_profile", {}) if isinstance(self.memory.metadata, dict) else {}
        _, reason = derive_trust_shape(
            score=self.score,
            conflict_status=self.conflict_status,
            retrieval_stage=self.retrieval_stage,
            activation_score=self.memory.activation_score,
            confidence=self.memory.confidence,
            admission_state=self.admission_state,
            score_profile=score_profile,
        )
        return reason


@dataclass
class SearchQuery:
    query: str
    scope_id: str
    scope_type: str = "session"
    limit: int = 10
    min_score: float = 0.0
    include_global: bool = True
    semantic: bool = False
    semantic_model: str | None = None
    fallback_to_or: bool = False
