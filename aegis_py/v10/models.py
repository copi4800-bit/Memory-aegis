from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from ..v9.models import MemoryRecordV9, JudgmentTrace

class GovernanceStatus(Enum):
    CANDIDATE = "candidate"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"
    REVOKED = "revoked"

class TruthRole(Enum):
    WINNER = "winner"
    CONTENDER = "contender"
    LOSER = "loser"
    NONE = "none"

class RetrievableMode(Enum):
    NORMAL = "normal"
    AUDIT = "audit"
    CONFLICT_PROBE = "conflict_probe"
    REVIEW_ONLY = "review_only"
    NONE = "none"

@dataclass
class DecisionObject:
    """The structured output of the Aegis v10 Governance Layer."""
    memory_id: str
    admissible: bool = False
    retrievable_mode: RetrievableMode = RetrievableMode.NONE
    governance_status: GovernanceStatus = GovernanceStatus.CANDIDATE
    truth_role: TruthRole = TruthRole.NONE
    
    decision_reason: List[str] = field(default_factory=list)
    required_action: str = "none" # review | merge | resolve_conflict | archive | revalidate | promote | demote
    
    # Audit Traces
    score_trace: Optional[JudgmentTrace] = None
    policy_trace: List[str] = field(default_factory=list)
    evidence_trace: List[str] = field(default_factory=list)
    risk_trace: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class MemoryRecordV10(MemoryRecordV9):
    """Rich Memory Record for v10 Governed Runtime."""
    governance: DecisionObject = field(default_factory=lambda: None) # Will be populated by engine
    fact_predicate: Optional[str] = None
    fact_object: Optional[str] = None
    provenance_authority: float = 1.0
    
    # Graphs
    supersession_chain: List[str] = field(default_factory=list)
    conflict_cluster_id: Optional[str] = None
