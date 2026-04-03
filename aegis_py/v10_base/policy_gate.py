from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..storage.models import Memory


@dataclass
class PolicyGateDecision:
    promotable: bool
    target_state: str
    reasons: list[str] = field(default_factory=list)
    policy_name: str = "v10-default-policy-gate"
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
        lane_profile = memory.metadata.get("lane_profile", {}) if isinstance(memory.metadata, dict) else {}
        subject_profile = memory.metadata.get("subject_profile", {}) if isinstance(memory.metadata, dict) else {}
        extraction_profile = memory.metadata.get("extraction_profile", {}) if isinstance(memory.metadata, dict) else {}
        oviraptor_profile = memory.metadata.get("oviraptor_profile", {}) if isinstance(memory.metadata, dict) else {}
        directness = float(score_profile.get("directness", memory.confidence or 0.0) or 0.0)
        conflict_pressure = float(score_profile.get("conflict_pressure", 0.0) or 0.0)
        decisive_pressure = float(score_profile.get("dunkleosteus_decisive_pressure", 0.0) or 0.0)
        conflict_sentinel_score = float(score_profile.get("thylacoleo_conflict_sentinel_score", 0.0) or 0.0)
        meganeura_capture_span = float(score_profile.get("meganeura_capture_span", 0.0) or 0.0)
        chalicotherium_fit = float(lane_profile.get("chalicotherium_ecology_fit", 0.0) or 0.0)
        ammonite_stability = float(subject_profile.get("ammonite_spiral_stability", 0.0) or 0.0)
        dimetrodon_feature_separation = float(extraction_profile.get("dimetrodon_feature_separation", 0.0) or 0.0)
        oviraptor_drift_risk = float(oviraptor_profile.get("drift_risk", 0.0) or 0.0)

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
        if decisive_pressure >= 0.82:
            reasons.append("dunkleosteus_decisive_signal")
        if meganeura_capture_span >= 0.82:
            reasons.append("meganeura_capture_broad")
        elif promotable and meganeura_capture_span > 0.0 and meganeura_capture_span < 0.45:
            target_state = "hypothesized"
            reasons.append("meganeura_capture_narrow")
        if dimetrodon_feature_separation >= 0.82:
            reasons.append("dimetrodon_feature_surgical")
        elif promotable and dimetrodon_feature_separation > 0.0 and dimetrodon_feature_separation < 0.52:
            target_state = "hypothesized"
            reasons.append("dimetrodon_feature_blended")
        if chalicotherium_fit >= 0.78:
            reasons.append("chalicotherium_lane_native")
        elif promotable and chalicotherium_fit > 0.0 and chalicotherium_fit < 0.55:
            target_state = "hypothesized"
            reasons.append("chalicotherium_lane_uncertain")
        if ammonite_stability >= 0.78:
            reasons.append("ammonite_subject_stable")
        elif (
            promotable
            and subject_profile.get("raw_subject")
            and ammonite_stability < 0.55
        ):
            target_state = "hypothesized"
            reasons.append("ammonite_subject_drift_risk")
        if oviraptor_drift_risk >= 0.82:
            target_state = "hypothesized"
            reasons.append("oviraptor_subject_drift_guard")
        elif oviraptor_drift_risk >= 0.64:
            reasons.append("oviraptor_subject_watchful")
        if conflict_pressure > 0.72:
            target_state = "hypothesized"
            reasons.append("elevated_conflict_pressure")
        if conflict_sentinel_score >= 0.62:
            target_state = "hypothesized"
            reasons.append("thylacoleo_sentinel_elevated")

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
