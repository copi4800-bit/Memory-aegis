from __future__ import annotations
from typing import Any, Dict, List, Optional
from .models import DecisionObject, TruthRole

class TruthRegistryV10:
    """Manages Fact Slots and Winner assignments."""
    
    def __init__(self, storage: Any):
        self.storage = storage

    def resolve_slot_ownership(self, contenders: List[Any], intent: str = "normal_recall") -> Dict[str, DecisionObject]:
        """
        Groups contenders by fact_slot and determines the winner for each.
        Implements Margin-aware winner selection.
        """
        slots: Dict[str, List[Any]] = {}
        for c in contenders:
            slot_id = getattr(c.memory, "subject", "general")
            if slot_id not in slots:
                slots[slot_id] = []
            slots[slot_id].append(c)
            
        decisions: Dict[str, DecisionObject] = {}
        
        for slot_id, members in slots.items():
            # Sort by score (v9_score or similar)
            members.sort(key=lambda x: getattr(x, "v9_score", 0.0), reverse=True)
            
            # Implementation of Rule 2: Singleton Truth
            for i, member in enumerate(members):
                decision = getattr(member, "v10_decision", None)
                if not decision: continue
                
                if i == 0: # Candidate for Winner
                    # Margin check
                    margin = 0.0
                    if len(members) > 1:
                        margin = members[0].v9_score - members[1].v9_score
                        
                    if margin > 0.2 or intent == "correction_lookup":
                        decision.truth_role = TruthRole.WINNER
                        decision.decision_reason.append(f"slot_winner_confirmed (margin: {margin:.2f})")
                    else:
                        decision.truth_role = TruthRole.CONTENDER
                        decision.decision_reason.append("high_entropy_slot_pending_review")
                else:
                    decision.truth_role = TruthRole.CONTENDER
                    decision.decision_reason.append("superseded_by_higher_ranked_winner")
                    
                decisions[member.memory.id] = decision
                
        return decisions
