from __future__ import annotations
from typing import Any, Dict, List, Optional
from .models import DecisionObject, GovernanceStatus, TruthRole, RetrievableMode, MemoryRecordV10
from .policy import MemoryConstitution
from .review import ReviewQueueV10
from .events import EventLogger, GovernanceEvent
from ..v9.scorer import ResidualScorer
from ..v9.models import JudgmentTrace

class GovernanceEngineV10:
    """Aegis v10 Decision Engine for Memory Governance."""
    
    def __init__(self, storage: Any, scorer: Optional[ResidualScorer] = None):
        self.storage = storage
        self.scorer = scorer or ResidualScorer()
        self.constitution = MemoryConstitution()
        self.review_queue = ReviewQueueV10(storage)
        self.logger = EventLogger(storage)

    def govern(self, memory: Any, query_signals: Dict[str, float], intent: str = "normal_recall") -> DecisionObject:
        """
        Main entry point for memory governance.
        Transforms soft scores into hard decisions via the Constitution.
        """
        # 1. Compute soft signals from v9 scorer
        trace = self.scorer.score(memory, query_signals, intent=intent)
        score = trace.factors.get("final_score", 0.0)
        entropy = trace.factors.get("entropy", 0.0)
        
        decision = DecisionObject(
            memory_id=memory.id,
            score_trace=trace
        )
        
        # 2. Basic State Proposals
        self.apply_basic_rules(decision, memory, score, intent)
        
        # 3. Constitutional Enforcement (Precedence Gating)
        # Simulate budget pressure based on usage metadata if available
        budget_pressure = 0.2 # Default low
        context = {"intent": intent, "score": score, "budget_pressure": budget_pressure}
        self.constitution.enforce(decision, memory, context)
        
        # 4. Review Escalation (Rule 9)
        if entropy > 0.7 or decision.governance_status == GovernanceStatus.PENDING_REVIEW:
            self.review_queue.enqueue(decision, memory, reason=f"High entropy: {entropy:.2f}" if entropy > 0.7 else "Policy escalation")

        # 5. Log Governance Event (Audit Trail)
        self._log_governance_action(decision, memory)
        
        return decision

    def apply_basic_rules(self, d: DecisionObject, m: Any, score: float, intent: str):
        """Applies high-level constitutional rules to determine admissibility."""
        
        # Rule: Hard Exclusion for Superseded
        if getattr(m.correction, "is_superseded", False):
            d.admissible = False
            d.governance_status = GovernanceStatus.SUPERSEDED
            d.truth_role = TruthRole.LOSER
            d.retrievable_mode = RetrievableMode.AUDIT
            d.decision_reason.append("hard_rule_superseded_exclusion")
            return

        # Rule: Basic Admissibility Threshold (V10: 0.5 score gate)
        if score > 0.5:
            d.admissible = True
            d.governance_status = GovernanceStatus.ACTIVE
            d.retrievable_mode = RetrievableMode.NORMAL
            d.decision_reason.append("score_threshold_met")
        else:
            d.admissible = False
            d.governance_status = GovernanceStatus.PENDING_REVIEW
            d.retrievable_mode = RetrievableMode.REVIEW_ONLY
            d.decision_reason.append("low_score_gate")

        # Rule: Truth Ownership (Winner detection)
        if getattr(m.correction, "is_slot_winner", False):
            d.truth_role = TruthRole.WINNER
            d.decision_reason.append("is_confirmed_slot_winner")
        else:
            d.truth_role = TruthRole.CONTENDER

    def _log_governance_action(self, d: DecisionObject, m: Any):
        """Emits a governance event for the audit trail."""
        event = GovernanceEvent(
            memory_id=m.id,
            action=d.governance_status.value,
            triggering_rule=d.policy_trace[-1] if d.policy_trace else "basic_rules",
            reason_text=", ".join(d.decision_reason),
            metadata={
                "scope_type": getattr(m, "scope_type", "agent"),
                "scope_id": getattr(m, "scope_id", "default"),
                "score": d.score_trace.factors.get("final_score", 0.0) if d.score_trace else 0.0,
                "entropy": d.score_trace.factors.get("entropy", 0.0) if d.score_trace else 0.0,
                "truth_role": d.truth_role.value
            }
        )
        self.logger.log(event)
