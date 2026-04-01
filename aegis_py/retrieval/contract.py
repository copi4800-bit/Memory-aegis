from __future__ import annotations

from typing import Iterable, Dict, Any


def normalize_fts_rank(rank: float) -> float:
    return 1.0 / (1.0 + abs(rank))


def blend_retrieval_score(rank: float, activation_score: float, score_profile: dict[str, float] | None = None) -> float:
    normalized_rank = normalize_fts_rank(rank)
    profile = score_profile or {}
    profile_boost = (
        (float(profile.get("source_reliability", 0.0) or 0.0) * 0.08)
        + (float(profile.get("directness", 0.0) or 0.0) * 0.08)
        + (float(profile.get("specificity", 0.0) or 0.0) * 0.04)
        - (float(profile.get("conflict_pressure", 0.0) or 0.0) * 0.1)
    )
    return round((normalized_rank * 0.62) + (activation_score * 0.28) + profile_boost, 6)


def build_reason_tags(
    *,
    query: str,
    content: str | None,
    summary: str | None,
    subject: str | None,
    memory_type: str,
    scope_type: str,
    scope_id: str,
    requested_scope_type: str | None,
    requested_scope_id: str | None,
    include_global: bool,
    activation_score: float,
    conflict_status: str,
    admission_state: str = "validated",
    score_profile: dict[str, float] | None = None,
) -> list[str]:
    reasons: list[str] = []
    haystack = " ".join(filter(None, [content, summary, subject])).lower()
    query_tokens = [token for token in query.lower().split() if token]
    matched = [token for token in query_tokens if token in haystack]

    if matched:
        reasons.append(f"fts_match:{','.join(sorted(set(matched)))}")
    else:
        reasons.append("fts_match")
    if requested_scope_type and scope_type == requested_scope_type:
        reasons.append("scope_type_match")
    if requested_scope_id and scope_id == requested_scope_id:
        reasons.append("scope_exact_match")
    if include_global and requested_scope_type and requested_scope_id and scope_type == "global":
        reasons.append("global_fallback")
    if memory_type == "procedural":
        reasons.append("procedural_bonus")
    if activation_score > 1.0:
        reasons.append("activation_boost")
    profile = score_profile or {}
    if float(profile.get("directness", 0.0) or 0.0) >= 0.85:
        reasons.append("directness_high")
    if float(profile.get("source_reliability", 0.0) or 0.0) >= 0.9:
        reasons.append("source_reliability_high")
    if float(profile.get("conflict_pressure", 0.0) or 0.0) >= 0.5:
        reasons.append("conflict_pressure_elevated")
    if memory_type == "semantic":
        reasons.append("semantic_fact_match")
    if conflict_status != "none":
        reasons.append("conflict_visible")
    if admission_state == "hypothesized":
        reasons.append("admission_hypothesized")
    elif admission_state == "consolidated":
        reasons.append("admission_consolidated")
    elif admission_state == "archived":
        reasons.append("admission_archived")
    return reasons


def summarize_reason(*, memory_type: str, activation_score: float, conflict_status: str) -> str:
    if memory_type == "semantic":
        return "Strong semantic fact match."

    parts = ["Matched query keywords."]
    if activation_score > 1.0:
        parts.append("Active context boost.")
    if conflict_status != "none":
        parts.append("Conflict visible.")
    return " ".join(parts)


def derive_trust_shape(
    *,
    score: float,
    conflict_status: str,
    retrieval_stage: str,
    activation_score: float,
    confidence: float,
    admission_state: str = "validated",
    score_profile: dict[str, float] | None = None,
    truth_role: str | None = None,
    governance_status: str | None = None,
) -> tuple[str, str]:
    profile = score_profile or {}
    
    # v10 Governance overrides
    if governance_status == "disputed" or truth_role == "contender":
        return "conflicting", "This memory is one of multiple contenders for the same fact slot and requires review."
    
    if conflict_status != "none":
        return "conflicting", "This memory is tied to an unresolved conflict."
    if admission_state == "archived":
        return "uncertain", "This memory is archived historical context and should not be treated as fresh truth."
    if admission_state == "hypothesized":
        return "uncertain", "This memory remains admission-hypothesized and should be treated cautiously."
    if admission_state == "consolidated" and retrieval_stage == "lexical":
        return "uncertain", "This memory is consolidated historical context rather than fresh validated recall."
    if retrieval_stage == "vector":
        return "uncertain", "This memory was recalled through the local vector store rather than a direct lexical match."
    if retrieval_stage != "lexical":
        return "uncertain", "This memory was added through relationship expansion, not a direct match."
    if float(profile.get("conflict_pressure", 0.0) or 0.0) >= 0.6:
        return "uncertain", "This memory has elevated conflict pressure despite matching the query."
    if score >= 0.95 and confidence >= 0.9 and activation_score >= 1.0 and float(profile.get("directness", 0.8) or 0.8) >= 0.8:
        return "strong", "This memory is a direct, high-confidence match."
    if score < 0.6 or confidence < 0.75:
        return "weak", "This memory matched, but the signal is relatively weak."
    return "strong", "This memory is a solid direct match."


def build_provenance(source_kind: str, source_ref: str | None) -> str:
    return f"[{source_kind}] {source_ref or 'memory-engine'}"


def score_link_expansion(
    *,
    link_weight: float,
    hop_depth: int,
    link_type: str,
    memory_type: str,
) -> float:
    hop_factor = 0.5 if hop_depth == 1 else 0.35
    type_bonus = {
        "procedural_supports_semantic": 0.14,
        "supports": 0.1,
        "extends": 0.08,
        "same_subject": 0.04,
    }.get(link_type, 0.05)
    memory_bonus = 0.04 if memory_type == "semantic" else 0.03 if memory_type == "procedural" else 0.0
    score = (float(link_weight) * hop_factor) + type_bonus + memory_bonus
    floor = 0.03 if hop_depth > 1 else 0.05
    return round(max(score, floor), 6)


class ExplainerBeast:
    """Generates human-readable explanations and structured trust metadata for retrieved results."""

    @staticmethod
    def build_explain_payload(
        score: float,
        conflict_status: str,
        retrieval_stage: str,
        activation_score: float,
        confidence: float,
        source_kind: str,
        source_ref: str | None,
        reason_tags: list[str]
    ) -> Dict[str, Any]:
        """Unifies trust_shape, provenance, and reason_tags into a single object."""
        shape, description = derive_trust_shape(
            score=score,
            conflict_status=conflict_status,
            retrieval_stage=retrieval_stage,
            activation_score=activation_score,
            confidence=confidence
        )
        provenance = build_provenance(source_kind, source_ref)
        
        return {
            "trust_shape": shape,
            "trust_description": description,
            "provenance": provenance,
            "reasons": reason_tags,
            "metrics": {
                "score": score,
                "activation": activation_score,
                "confidence": confidence
            }
        }

    @staticmethod
    def format_explain_text(payload: Dict[str, Any]) -> str:
        """Formats the explain payload into a human-readable string."""
        text = f"Trust: {payload['trust_shape'].upper()} - {payload['trust_description']}\n"
        text += f"Provenance: {payload['provenance']}\n"
        if payload['reasons']:
            text += f"Reasons: {', '.join(payload['reasons'])}\n"
        return text
