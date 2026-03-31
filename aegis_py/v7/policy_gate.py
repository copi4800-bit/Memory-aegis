from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..storage.models import Memory


@dataclass
class PolicyGateDecision:
    promotable: bool
    target_state: str
    reasons: list[str] = field(default_factory=list)
    policy_name: str = "v7-default-policy-gate"
    confidence_floor: float = 0.6
    activation_floor: float = 0.1


class ValidationPolicyGate:
    """Central gate between extraction and durable memory admission."""

    def evaluate(
        self,
        *,
        memory: Memory,
        evidence_event_id: str | None,
        contradiction_risk: bool,
    ) -> PolicyGateDecision:
        reasons: list[str] = []
        promotable = True
        target_state = "validated"
        score_profile = memory.metadata.get("score_profile", {}) if isinstance(memory.metadata, dict) else {}
        directness = float(score_profile.get("directness", memory.confidence or 0.0) or 0.0)
        conflict_pressure = float(score_profile.get("conflict_pressure", 0.0) or 0.0)

        if not evidence_event_id:
            promotable = False
            target_state = "draft"
            reasons.append("blocked_missing_evidence")
        else:
            reasons.append("evidence_present")

        if float(memory.confidence or 0.0) < 0.6:
            promotable = False
            target_state = "draft"
            reasons.append("blocked_low_confidence")
        else:
            reasons.append("confidence_passed")
        if directness < 0.6:
            promotable = False
            target_state = "draft"
            reasons.append("blocked_low_directness")
        if conflict_pressure > 0.72:
            target_state = "hypothesized"
            reasons.append("elevated_conflict_pressure")

        if float(memory.activation_score or 0.0) < 0.1:
            promotable = False
            target_state = "draft"
            reasons.append("blocked_low_activation")

        if contradiction_risk:
            target_state = "hypothesized"
            reasons.append("review_contradiction_risk")

        if memory.type == "procedural":
            reasons.append("procedural_lane_checked")
        elif memory.type == "semantic":
            reasons.append("fact_lane_checked")
        else:
            reasons.append("general_lane_checked")

        if promotable:
            reasons.append("promotion_allowed")

        return PolicyGateDecision(
            promotable=promotable,
            target_state=target_state,
            reasons=reasons,
        )

    def to_payload(self, decision: PolicyGateDecision) -> dict[str, Any]:
        return {
            "promotable": decision.promotable,
            "target_state": decision.target_state,
            "reasons": list(decision.reasons),
            "policy_name": decision.policy_name,
            "confidence_floor": decision.confidence_floor,
            "activation_floor": decision.activation_floor,
        }
