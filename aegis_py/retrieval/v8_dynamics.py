from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

V8_STATE_METADATA_KEY = "v8_state"
LEGACY_V8_DYNAMICS_METADATA_KEY = "v8_dynamics"
PERSISTED_V8_STATE_FIELDS = (
    "belief_score",
    "usage_signal",
    "decay_signal",
    "regret_signal",
    "trust_score",
    "readiness_score",
    "feedback_count",
    "belief_delta",
)
DERIVED_V8_SIGNAL_FIELDS = (
    "evidence_signal",
    "support_signal",
    "conflict_signal",
    "stability_signal",
)


@dataclass(frozen=True)
class V8DynamicsProfile:
    evidence_directness_weight: float = 0.35
    evidence_specificity_weight: float = 0.2
    evidence_reliability_weight: float = 0.3
    evidence_completeness_weight: float = 0.15
    direct_conflict_open_bonus: float = 0.65
    usage_access_weight: float = 0.7
    usage_activation_weight: float = 0.3
    stability_profile_conflict_weight: float = 0.4
    stability_direct_conflict_bonus: float = 0.35
    stability_low_confidence_weight: float = 0.25
    stability_belief_delta_weight: float = 0.4
    belief_support_gain_weight: float = 0.45
    belief_usage_gain_weight: float = 0.25
    belief_evidence_gain_weight: float = 0.3
    belief_conflict_loss_weight: float = 0.4
    belief_base_decay: float = 0.08
    belief_regret_loss_weight: float = 0.3
    belief_decay_loss_weight: float = 0.22
    trust_evidence_weight: float = 1.0
    trust_support_weight: float = 0.55
    trust_usage_weight: float = 0.45
    trust_stability_weight: float = 0.35
    trust_belief_weight: float = 0.95
    trust_conflict_weight: float = 1.1
    trust_regret_weight: float = 0.7
    trust_decay_weight: float = 0.25
    decay_unused_weight: float = 0.45
    decay_conflict_weight: float = 0.35
    decay_support_relief_weight: float = 0.2
    readiness_trust_weight: float = 1.25
    readiness_usage_weight: float = 0.75
    readiness_admissibility_weight: float = 0.55
    readiness_decay_weight: float = 0.8
    readiness_conflict_weight: float = 0.9
    feedback_update_rate: float = 0.35
    feedback_decay_rate: float = 0.3
    feedback_success_weight: float = 0.55
    feedback_relevance_weight: float = 0.35
    feedback_override_penalty: float = 0.25
    feedback_regret_failure_weight: float = 0.65
    feedback_regret_override_weight: float = 0.35
    feedback_decay_unused_weight: float = 0.35
    feedback_decay_conflict_weight: float = 0.35
    feedback_decay_regret_weight: float = 0.2
    feedback_decay_support_relief_weight: float = 0.15
    transition_promote_trust: float = 0.8
    transition_demote_trust: float = 0.6
    transition_promote_evidence: float = 0.4
    transition_promote_conflict_max: float = 0.45
    transition_demote_conflict_min: float = 0.58
    score_bonus_trust_weight: float = 0.22
    score_bonus_readiness_weight: float = 0.18
    score_bonus_belief_weight: float = 0.08
    score_bonus_conflict_penalty: float = 0.08
    energy_complexity_weight: float = 0.08
    energy_conflict_weight: float = 0.7
    energy_support_relief_weight: float = 0.45
    objective_conflict_weight: float = 0.35
    objective_stability_weight: float = 0.25
    objective_cost_weight: float = 0.1


DEFAULT_V8_DYNAMICS_PROFILE = V8DynamicsProfile()
_ACTIVE_V8_DYNAMICS_PROFILE = DEFAULT_V8_DYNAMICS_PROFILE


def get_active_v8_profile() -> V8DynamicsProfile:
    return _ACTIVE_V8_DYNAMICS_PROFILE


def set_active_v8_profile(profile: V8DynamicsProfile) -> None:
    global _ACTIVE_V8_DYNAMICS_PROFILE
    _ACTIVE_V8_DYNAMICS_PROFILE = profile


def reset_active_v8_profile() -> None:
    set_active_v8_profile(DEFAULT_V8_DYNAMICS_PROFILE)


def with_profile(profile: V8DynamicsProfile, **updates: float) -> V8DynamicsProfile:
    return replace(profile, **updates)


def bounded_ratio(value: float) -> float:
    numeric = max(0.0, float(value or 0.0))
    return numeric / (1.0 + numeric)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _score_profile(row: dict[str, Any]) -> dict[str, float]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    profile = metadata.get("score_profile", {}) if isinstance(metadata, dict) else {}
    return profile if isinstance(profile, dict) else {}


def _v8_state(row: dict[str, Any]) -> dict[str, float]:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    raw = {}
    if isinstance(metadata, dict):
        canonical = metadata.get(V8_STATE_METADATA_KEY, {})
        legacy = metadata.get(LEGACY_V8_DYNAMICS_METADATA_KEY, {})
        if isinstance(canonical, dict) and canonical:
            raw = canonical
        elif isinstance(legacy, dict):
            raw = legacy
    if not isinstance(raw, dict):
        raw = {}
    return {
        "usage_signal": clamp01(raw.get("usage_signal", 0.0)),
        "decay_signal": clamp01(raw.get("decay_signal", 0.0)),
        "regret_signal": clamp01(raw.get("regret_signal", 0.0)),
        "belief_score": clamp01(raw.get("belief_score", _row_confidence(row))),
        "feedback_count": max(0.0, float(raw.get("feedback_count", 0.0) or 0.0)),
        "belief_delta": abs(float(raw.get("belief_delta", 0.0) or 0.0)),
    }


def build_persisted_v8_state(
    *,
    signals: dict[str, Any],
    feedback_count: float,
    belief_delta: float,
    last_feedback_at: str | None = None,
) -> dict[str, float | str]:
    payload: dict[str, float | str] = {
        "belief_score": round(float(signals.get("belief_score", 0.0) or 0.0), 6),
        "usage_signal": round(float(signals.get("usage_signal", 0.0) or 0.0), 6),
        "decay_signal": round(float(signals.get("decay_signal", 0.0) or 0.0), 6),
        "regret_signal": round(float(signals.get("regret_signal", 0.0) or 0.0), 6),
        "trust_score": round(float(signals.get("trust_score", 0.0) or 0.0), 6),
        "readiness_score": round(float(signals.get("readiness_score", 0.0) or 0.0), 6),
        "feedback_count": round(float(feedback_count or 0.0), 6),
        "belief_delta": round(float(belief_delta or 0.0), 6),
    }
    if last_feedback_at:
        payload["last_feedback_at"] = last_feedback_at
    return payload


def split_v8_signal_views(signals: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    persisted_state = {
        key: signals[key]
        for key in PERSISTED_V8_STATE_FIELDS
        if key in signals
    }
    if "last_feedback_at" in signals:
        persisted_state["last_feedback_at"] = signals["last_feedback_at"]
    derived_state = {
        key: signals[key]
        for key in DERIVED_V8_SIGNAL_FIELDS
        if key in signals
    }
    return persisted_state, derived_state


def _row_confidence(row: dict[str, Any]) -> float:
    return clamp01(float(row.get("confidence", 1.0) or 0.0))


def _row_activation(row: dict[str, Any]) -> float:
    return max(0.0, float(row.get("activation_score", 0.0) or 0.0))


def _row_access_count(row: dict[str, Any]) -> int:
    return max(0, int(row.get("access_count", 0) or 0))


def _evidence_signal(row: dict[str, Any], *, evidence_count: int, profile: V8DynamicsProfile) -> tuple[float, dict[str, float]]:
    score_profile = _score_profile(row)
    quality = (
        (float(score_profile.get("directness", 0.0) or 0.0) * profile.evidence_directness_weight)
        + (float(score_profile.get("specificity", 0.0) or 0.0) * profile.evidence_specificity_weight)
        + (float(score_profile.get("source_reliability", 0.0) or 0.0) * profile.evidence_reliability_weight)
        + (float(score_profile.get("evidence_completeness", 0.0) or 0.0) * profile.evidence_completeness_weight)
    )
    raw_strength = max(float(evidence_count), 0.0) + max(quality, 0.0)
    return round(1.0 - math.exp(-raw_strength), 6), score_profile


def _support_signal(*, support_weight: float) -> float:
    return round(bounded_ratio(support_weight), 6)


def _conflict_signal(*, conflict_weight: float, direct_conflict_open: bool, profile: V8DynamicsProfile) -> float:
    raw = max(conflict_weight, 0.0) + (profile.direct_conflict_open_bonus if direct_conflict_open else 0.0)
    return round(bounded_ratio(raw), 6)


def _usage_signal(row: dict[str, Any], profile: V8DynamicsProfile) -> float:
    dynamic = _v8_state(row)
    if dynamic["feedback_count"] > 0:
        return round(dynamic["usage_signal"], 6)
    access = _row_access_count(row)
    activation = _row_activation(row)
    return round(
        clamp01(
            (bounded_ratio(access) * profile.usage_access_weight)
            + (bounded_ratio(max(activation - 1.0, 0.0)) * profile.usage_activation_weight)
        ),
        6,
    )


def _stability_signal(row: dict[str, Any], *, direct_conflict_open: bool, profile: V8DynamicsProfile) -> float:
    dynamic = _v8_state(row)
    score_profile = _score_profile(row)
    volatility = (
        float(score_profile.get("conflict_pressure", 0.0) or 0.0) * profile.stability_profile_conflict_weight
        + (profile.stability_direct_conflict_bonus if direct_conflict_open else 0.0)
        + max(0.0, 0.8 - _row_confidence(row)) * profile.stability_low_confidence_weight
        + min(0.35, dynamic["belief_delta"]) * profile.stability_belief_delta_weight
    )
    return round(math.exp(-volatility), 6)


def _trust_score(
    *,
    evidence_signal: float,
    support_signal: float,
    usage_signal: float,
    stability_signal: float,
    conflict_signal: float,
) -> float:
    trust = sigmoid(
        (evidence_signal * 1.15)
        + (support_signal * 0.75)
        + (usage_signal * 0.65)
        + (stability_signal * 0.45)
        - (conflict_signal * 1.1)
    )
    return round(trust, 6)


def _decay_signal(*, usage_signal: float, support_signal: float, conflict_signal: float, profile: V8DynamicsProfile) -> float:
    raw = max(
        0.0,
        profile.decay_unused_weight * (1.0 - usage_signal)
        + profile.decay_conflict_weight * conflict_signal
        - profile.decay_support_relief_weight * support_signal,
    )
    return round(clamp01(raw), 6)


def _belief_score(
    *,
    prior_belief: float,
    evidence_signal: float,
    support_signal: float,
    usage_signal: float,
    conflict_signal: float,
    regret_signal: float,
    decay_signal: float,
    profile: V8DynamicsProfile,
) -> float:
    increased = (
        (1.0 - prior_belief)
        * (
            (support_signal * profile.belief_support_gain_weight)
            + (usage_signal * profile.belief_usage_gain_weight)
            + (evidence_signal * profile.belief_evidence_gain_weight)
        )
    )
    decreased = prior_belief * (
        (conflict_signal * profile.belief_conflict_loss_weight)
        + profile.belief_base_decay
        + (regret_signal * profile.belief_regret_loss_weight)
        + (decay_signal * profile.belief_decay_loss_weight)
    )
    return round(clamp01(prior_belief + increased - decreased), 6)


def _readiness_score(
    *,
    trust_score: float,
    usage_signal: float,
    decay_signal: float,
    conflict_signal: float,
    admission_state: str,
    profile: V8DynamicsProfile,
) -> float:
    admissibility = {
        "validated": 1.0,
        "consolidated": 0.85,
        "draft": 0.35,
        "hypothesized": 0.15,
        "invalidated": 0.0,
        "archived": 0.2,
    }.get(admission_state, 0.5)
    readiness = sigmoid(
        (trust_score * profile.readiness_trust_weight)
        + (usage_signal * profile.readiness_usage_weight)
        + (admissibility * profile.readiness_admissibility_weight)
        - (decay_signal * profile.readiness_decay_weight)
        - (conflict_signal * profile.readiness_conflict_weight)
    )
    return round(readiness, 6)


def _transition_gate(*, trust_score: float, evidence_signal: float, conflict_signal: float, admission_state: str, profile: V8DynamicsProfile) -> dict[str, Any]:
    thresholds = {
        "promote_trust": profile.transition_promote_trust,
        "demote_trust": profile.transition_demote_trust,
        "promote_evidence": profile.transition_promote_evidence,
        "promote_conflict_max": profile.transition_promote_conflict_max,
        "demote_conflict_min": profile.transition_demote_conflict_min,
    }
    recommended_state = admission_state
    if admission_state in {"draft", "hypothesized"}:
        if trust_score >= thresholds["promote_trust"] and evidence_signal >= thresholds["promote_evidence"] and conflict_signal <= thresholds["promote_conflict_max"]:
            recommended_state = "validated"
    elif admission_state == "validated":
        if trust_score < thresholds["demote_trust"] and conflict_signal >= thresholds["demote_conflict_min"]:
            recommended_state = "hypothesized"
    return {
        "current_state": admission_state,
        "recommended_state": recommended_state,
        "thresholds": thresholds,
        "promote_ready": recommended_state == "validated" and admission_state != "validated",
        "demote_ready": recommended_state != admission_state and admission_state == "validated",
    }


def compute_v8_core_signals(
    *,
    row: dict[str, Any],
    admission_state: str,
    evidence_count: int,
    support_weight: float,
    conflict_weight: float,
    direct_conflict_open: bool,
    profile: V8DynamicsProfile | None = None,
) -> dict[str, Any]:
    active_profile = profile or get_active_v8_profile()
    dynamic_state = _v8_state(row)
    evidence_signal, score_profile = _evidence_signal(row, evidence_count=evidence_count, profile=active_profile)
    support_signal = _support_signal(support_weight=support_weight)
    conflict_signal = _conflict_signal(conflict_weight=conflict_weight, direct_conflict_open=direct_conflict_open, profile=active_profile)
    usage_signal = _usage_signal(row, active_profile)
    regret_signal = round(dynamic_state["regret_signal"], 6)
    stability_signal = _stability_signal(row, direct_conflict_open=direct_conflict_open, profile=active_profile)
    derived_decay_signal = _decay_signal(
        usage_signal=usage_signal,
        support_signal=support_signal,
        conflict_signal=conflict_signal,
        profile=active_profile,
    )
    decay_signal = (
        round(dynamic_state["decay_signal"], 6)
        if dynamic_state["feedback_count"] > 0
        else derived_decay_signal
    )
    if dynamic_state["feedback_count"] > 0:
        belief_score = round(dynamic_state["belief_score"], 6)
    else:
        belief_score = _belief_score(
            prior_belief=round(dynamic_state["belief_score"], 6),
            evidence_signal=evidence_signal,
            support_signal=support_signal,
            usage_signal=usage_signal,
            conflict_signal=conflict_signal,
            regret_signal=regret_signal,
            decay_signal=decay_signal,
            profile=active_profile,
        )
    trust_score = sigmoid(
        (evidence_signal * active_profile.trust_evidence_weight)
        + (support_signal * active_profile.trust_support_weight)
        + (usage_signal * active_profile.trust_usage_weight)
        + (stability_signal * active_profile.trust_stability_weight)
        + (belief_score * active_profile.trust_belief_weight)
        - (conflict_signal * active_profile.trust_conflict_weight)
        - (regret_signal * active_profile.trust_regret_weight)
        - (decay_signal * active_profile.trust_decay_weight)
    )
    trust_score = round(trust_score, 6)
    readiness_score = _readiness_score(
        trust_score=trust_score,
        usage_signal=usage_signal,
        decay_signal=decay_signal,
        conflict_signal=conflict_signal,
        admission_state=admission_state,
        profile=active_profile,
    )
    transition_gate = _transition_gate(
        trust_score=trust_score,
        evidence_signal=evidence_signal,
        conflict_signal=conflict_signal,
        admission_state=admission_state,
        profile=active_profile,
    )
    signals = {
        "evidence_signal": evidence_signal,
        "support_signal": support_signal,
        "conflict_signal": conflict_signal,
        "usage_signal": usage_signal,
        "regret_signal": regret_signal,
        "stability_signal": stability_signal,
        "decay_signal": decay_signal,
        "belief_score": belief_score,
        "trust_score": trust_score,
        "readiness_score": 0.0 if admission_state == "invalidated" else readiness_score,
        "admission_state": admission_state,
        "evidence_count": evidence_count,
        "support_weight": round(max(0.0, support_weight), 6),
        "conflict_weight": round(max(0.0, conflict_weight), 6),
        "direct_conflict_open": direct_conflict_open,
        "score_profile": score_profile,
        "profile": {"name": "active"},
        "transition_gate": transition_gate,
    }
    persisted_state, derived_state = split_v8_signal_views(
        {
            **signals,
            **(
                {
                    "last_feedback_at": row.get("metadata", {}).get(V8_STATE_METADATA_KEY, {}).get("last_feedback_at")
                }
                if isinstance(row.get("metadata"), dict)
                else {}
            ),
        }
    )
    signals["persisted_state"] = persisted_state
    signals["derived_state"] = derived_state
    return signals


def apply_outcome_feedback(
    *,
    row: dict[str, Any],
    evidence_signal: float,
    support_signal: float,
    conflict_signal: float,
    success_score: float,
    relevance_score: float,
    override_score: float,
    profile: V8DynamicsProfile | None = None,
) -> dict[str, float]:
    active_profile = profile or get_active_v8_profile()
    dynamic = _v8_state(row)
    prior_usage = dynamic["usage_signal"] if dynamic["feedback_count"] > 0 else _usage_signal(row, active_profile)
    prior_decay = dynamic["decay_signal"] if dynamic["feedback_count"] > 0 else _decay_signal(
        usage_signal=prior_usage,
        support_signal=support_signal,
        conflict_signal=conflict_signal,
        profile=active_profile,
    )
    prior_belief = round(dynamic["belief_score"], 6)
    quality = clamp01(max(
        0.0,
        (success_score * active_profile.feedback_success_weight)
        + (relevance_score * active_profile.feedback_relevance_weight)
        - (override_score * active_profile.feedback_override_penalty),
    ))
    usage_signal = round(((1.0 - active_profile.feedback_update_rate) * prior_usage) + (active_profile.feedback_update_rate * quality), 6)
    regret_signal = round(
        clamp01(
            (max(0.0, 1.0 - success_score) * active_profile.feedback_regret_failure_weight)
            + (override_score * active_profile.feedback_regret_override_weight)
        ),
        6,
    )
    decay_target = clamp01(
        (active_profile.feedback_decay_unused_weight * (1.0 - usage_signal))
        + (active_profile.feedback_decay_conflict_weight * conflict_signal)
        + (active_profile.feedback_decay_regret_weight * regret_signal)
        - (active_profile.feedback_decay_support_relief_weight * support_signal)
    )
    decay_signal = round(((1.0 - active_profile.feedback_decay_rate) * prior_decay) + (active_profile.feedback_decay_rate * decay_target), 6)
    belief_score = _belief_score(
        prior_belief=prior_belief,
        evidence_signal=evidence_signal,
        support_signal=support_signal,
        usage_signal=usage_signal,
        conflict_signal=conflict_signal,
        regret_signal=regret_signal,
        decay_signal=decay_signal,
        profile=active_profile,
    )
    return {
        "usage_signal": usage_signal,
        "regret_signal": regret_signal,
        "decay_signal": decay_signal,
        "belief_score": belief_score,
        "belief_delta": round(abs(belief_score - prior_belief), 6),
        "feedback_count": round(dynamic["feedback_count"] + 1.0, 6),
        "outcome_quality": round(quality, 6),
    }


def bundle_energy_snapshot(
    signals_list: list[dict[str, Any]],
    *,
    profile: V8DynamicsProfile | None = None,
) -> dict[str, float]:
    active_profile = profile or get_active_v8_profile()
    if not signals_list:
        return {
            "bundle_size": 0.0,
            "energy": 0.0,
            "retrieval_loss": 0.0,
            "conflict_loss": 0.0,
            "stability_loss": 0.0,
            "cost_loss": 0.0,
            "objective": 0.0,
        }
    energy_terms: list[float] = []
    retrieval_terms: list[float] = []
    conflict_terms: list[float] = []
    stability_terms: list[float] = []
    for signals in signals_list:
        support = float(signals.get("support_signal", 0.0) or 0.0)
        conflict = float(signals.get("conflict_signal", 0.0) or 0.0)
        trust = float(signals.get("trust_score", 0.0) or 0.0)
        readiness = float(signals.get("readiness_score", 0.0) or 0.0)
        regret = float(signals.get("regret_signal", 0.0) or 0.0)
        decay = float(signals.get("decay_signal", 0.0) or 0.0)
        complexity = (1.0 - readiness) * active_profile.energy_complexity_weight
        energy_terms.append(
            (1.0 - trust) ** 2
            + (conflict * active_profile.energy_conflict_weight)
            - (support * active_profile.energy_support_relief_weight)
            + complexity
        )
        retrieval_terms.append(max(0.0, 1.0 - readiness))
        conflict_terms.append(conflict)
        stability_terms.append(decay + regret)
    bundle_size = float(len(signals_list))
    retrieval_loss = round(sum(retrieval_terms) / bundle_size, 6)
    conflict_loss = round(sum(conflict_terms) / bundle_size, 6)
    stability_loss = round(sum(stability_terms) / bundle_size, 6)
    cost_loss = round(min(1.0, bundle_size / 10.0), 6)
    energy = round(sum(energy_terms) / bundle_size, 6)
    objective = round(
        retrieval_loss
        + (active_profile.objective_conflict_weight * conflict_loss)
        + (active_profile.objective_stability_weight * stability_loss)
        + (active_profile.objective_cost_weight * cost_loss),
        6,
    )
    return {
        "bundle_size": bundle_size,
        "energy": energy,
        "retrieval_loss": retrieval_loss,
        "conflict_loss": conflict_loss,
        "stability_loss": stability_loss,
        "cost_loss": cost_loss,
        "objective": objective,
    }


def dynamic_score_bonus(signals: dict[str, Any]) -> float:
    active_profile = get_active_v8_profile()
    if signals["admission_state"] == "invalidated":
        return -1.0
    return round(
        (signals["trust_score"] * active_profile.score_bonus_trust_weight)
        + (signals["readiness_score"] * active_profile.score_bonus_readiness_weight)
        + (signals["belief_score"] * active_profile.score_bonus_belief_weight)
        - (signals["conflict_signal"] * active_profile.score_bonus_conflict_penalty),
        6,
    )


def dynamic_reason_tags(signals: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if signals["evidence_signal"] >= 0.7:
        reasons.append("v8_evidence_strong")
    if signals["support_signal"] >= 0.25:
        reasons.append("v8_support_present")
    if signals["conflict_signal"] >= 0.35:
        reasons.append("v8_conflict_pressure")
    if signals["usage_signal"] >= 0.25:
        reasons.append("v8_usage_reinforced")
    if signals["regret_signal"] >= 0.3:
        reasons.append("v8_regret_pressure")
    if signals["belief_score"] >= 0.7:
        reasons.append("v8_belief_elevated")
    if signals["trust_score"] >= 0.7:
        reasons.append("v8_trust_elevated")
    if signals["readiness_score"] >= 0.7:
        reasons.append("v8_readiness_elevated")
    if signals["transition_gate"]["promote_ready"]:
        reasons.append("v8_promote_ready")
    if signals["transition_gate"]["demote_ready"]:
        reasons.append("v8_demote_ready")
    return reasons
