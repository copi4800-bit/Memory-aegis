from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

class MemoryState(Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    CONSOLIDATED = "consolidated"
    ARCHIVED = "archived"
    INVALIDATED = "invalidated"

@dataclass
class TrustSignals:
    """Mathematical trust components for Delta_trust."""
    evidence_strength: float = 0.0
    support_strength: float = 0.0
    stability_score: float = 0.0
    regret_score: float = 0.0
    trust_score: float = 0.0
    source_quality: float = 0.5
    verification_status: str = "unverified"
    lineage_clarity: float = 0.0

@dataclass
class ConflictSignals:
    """Contradiction signals for Delta_conflict."""
    open_conflict_count: int = 0
    conflict_severity: float = 0.0
    slot_collision: float = 0.0
    unresolved_contradiction: float = 0.0

@dataclass
class CorrectionSignals:
    """Truth alignment signals for Delta_corr."""
    is_slot_winner: bool = False
    is_superseded: bool = False
    correction_freshness: float = 0.0
    supersession_depth: int = 0
    slot_priority: float = 1.0

@dataclass
class LifecycleSignals:
    """Survival and decay signals for Delta_life."""
    usage_count: int = 0
    validated_reuse_count: int = 0
    last_meaningful_use_at: Optional[datetime] = None
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    decay_rate: float = 0.01
    readiness_base: float = 1.0
    staleness_index: float = 0.0
    archive_pressure: float = 0.0
    memory_state: MemoryState = MemoryState.DRAFT
    # Enhanced lifecycle fields
    promotion_threshold_met: bool = False
    demotion_pressure: float = 0.0

@dataclass
class JudgmentTrace:
    """Explanation trace for 'Why This Result v2'."""
    base_score: float = 0.0
    judge_delta: float = 0.0
    life_delta: float = 0.0
    hard_constraints_delta: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)
    decisive_factor: str = "relevance"

@dataclass
class MemoryRecordV9:
    """The unified Aegis v9 Memory Record following Residual Judgment Engine spec."""
    id: str
    content: str
    canonical_subject: str
    fact_slot: Optional[str] = None
    memory_type: str = "semantic"
    
    # Semantic/Fact properties
    fact_kind: str = "multivalued" # singleton | multivalued
    singleton_fact: bool = False
    
    trust: TrustSignals = field(default_factory=TrustSignals)
    conflict: ConflictSignals = field(default_factory=ConflictSignals)
    correction: CorrectionSignals = field(default_factory=CorrectionSignals)
    lifecycle: LifecycleSignals = field(default_factory=LifecycleSignals)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    governance_tags: List[str] = field(default_factory=list)
