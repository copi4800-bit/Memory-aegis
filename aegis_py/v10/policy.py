from __future__ import annotations
from typing import Any, Dict, List, Optional
from .models import DecisionObject, GovernanceStatus, TruthRole, RetrievableMode

class MemoryConstitution:
    """The hierarchical law system for Aegis v10 memory governance."""
    
    # Precedence Levels
    LEVELS = {
        "C0": "SYSTEM_SAFETY",
        "C1": "USER_OVERRIDE",
        "C2": "CANONICAL_TRUTH",
        "C3": "GOVERNANCE_RISK",
        "C4": "SOFT_JUDGMENT"
    }

    def enforce(self, d: DecisionObject, m: Any, context: Dict[str, Any]) -> DecisionObject:
        """Applies the constitution in order of precedence (C0 -> C4)."""
        
        # --- C0: System Safety (Rule 4, 7) ---
        if self._violates_safety(m):
            d.admissible = False
            d.governance_status = GovernanceStatus.REVOKED
            d.retrievable_mode = RetrievableMode.NONE
            d.policy_trace.append("C0_SAFETY_VIOLATION")
            return d
            
        # --- C1: User Explicit Override (Rule 1) ---
        if context.get("intent") in ["user_override_active", "preference_lookup"]:
            if m.metadata.get("is_correction") or m.metadata.get("is_winner"):
                d.admissible = True
                d.governance_status = GovernanceStatus.ACTIVE
                d.truth_role = TruthRole.WINNER
                d.policy_trace.append("C1_USER_OVERRIDE_APPLIED")
            
        # --- C2: Canonical Truth (Rule 2, 3) ---
        if getattr(m.correction, "is_superseded", False):
            d.admissible = False
            d.governance_status = GovernanceStatus.SUPERSEDED
            d.retrievable_mode = RetrievableMode.AUDIT
            d.policy_trace.append("C2_SUPERSEDED_EXCLUSION")
            return d

        if d.truth_role == TruthRole.WINNER:
            d.policy_trace.append("C2_SLOT_WINNER_PROTECTION")
            
        # --- C3: Governance Risk & Budget (Rule 4, 9, 11) ---
        conflict_severity = getattr(m.conflict, "unresolved_contradiction", 0.0)
        entropy = d.score_trace.factors.get("entropy", 0.0) if d.score_trace else 0.0
        
        # Rule 4: High Conflict Quarantine
        if conflict_severity > 0.8:
            d.admissible = False
            d.governance_status = GovernanceStatus.QUARANTINED
            d.retrievable_mode = RetrievableMode.CONFLICT_PROBE
            d.policy_trace.append("C3_HIGH_CONFLICT_QUARANTINE")
            
        # Rule 9 & 11: Budget Pressure & Ambiguity Escalation
        budget_pressure = context.get("budget_pressure", 0.0)
        if (entropy > 0.7 or budget_pressure > 0.8) and d.governance_status != GovernanceStatus.ACTIVE:
            d.governance_status = GovernanceStatus.PENDING_REVIEW
            d.policy_trace.append("C3_AMBIGUITY_ESC_TO_REVIEW")

        # --- C4: Soft Judgment Adjustment ---
        score = context.get("score", 0.0)
        if score < 0.3 and d.governance_status not in [GovernanceStatus.ACTIVE, GovernanceStatus.SUPERSEDED]:
            d.admissible = False
            d.policy_trace.append("C4_LOW_RELEVANCE_SUPPRESSION")

        # Final synchronization
        if not d.admissible and d.retrievable_mode == RetrievableMode.NORMAL:
            if d.governance_status == GovernanceStatus.QUARANTINED:
                d.retrievable_mode = RetrievableMode.CONFLICT_PROBE
            elif d.governance_status == GovernanceStatus.PENDING_REVIEW:
                d.retrievable_mode = RetrievableMode.REVIEW_ONLY
            else:
                d.retrievable_mode = RetrievableMode.NONE
            
        return d

    def _violates_safety(self, m: Any) -> bool:
        # Placeholder for real safety filters
        return "ILLEGAL_CONTENT" in m.content.upper()
