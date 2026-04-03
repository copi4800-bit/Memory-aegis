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
    v10_core_signals: dict[str, object] | None = None
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
        
        # v10 Governance context
        v10_dec = getattr(self, "v10_decision", None)
        truth_role = v10_dec.truth_role.value if v10_dec else None
        gov_status = v10_dec.governance_status.value if v10_dec else None
        
        state, _ = derive_trust_shape(
            score=self.score,
            conflict_status=self.conflict_status,
            retrieval_stage=self.retrieval_stage,
            activation_score=self.memory.activation_score,
            confidence=self.memory.confidence,
            admission_state=self.admission_state,
            score_profile=score_profile,
            truth_role=truth_role,
            governance_status=gov_status,
        )
        return state

    @property
    def trust_reason(self) -> str:
        score_profile = self.memory.metadata.get("score_profile", {}) if isinstance(self.memory.metadata, dict) else {}
        
        # v10 Governance context
        v10_dec = getattr(self, "v10_decision", None)
        truth_role = v10_dec.truth_role.value if v10_dec else None
        gov_status = v10_dec.governance_status.value if v10_dec else None

        _, reason = derive_trust_shape(
            score=self.score,
            conflict_status=self.conflict_status,
            retrieval_stage=self.retrieval_stage,
            activation_score=self.memory.activation_score,
            confidence=self.memory.confidence,
            admission_state=self.admission_state,
            score_profile=score_profile,
            truth_role=truth_role,
            governance_status=gov_status,
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

    @property
    def argentinosaurus_scope_geometry(self) -> dict[str, object]:
        include_global = bool(self.include_global)
        explicit_scope = bool(self.scope_type and self.scope_id)
        breadth = 0.38 + (0.22 if explicit_scope else 0.0) + (0.18 if include_global else 0.0)
        return {
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "include_global": include_global,
            "explicit_scope": explicit_scope,
            "argentinosaurus_scope_geometry": round(min(0.99, breadth), 3),
        }
