from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, float(value)))


@dataclass(frozen=True)
class HybridRouteProfile:
    route: str
    confidence: float
    weights: dict[str, float]


@dataclass(frozen=True)
class HybridFusionResult:
    route: str
    route_confidence: float
    signals: dict[str, float]
    weights: dict[str, float]
    fused_score: float
    agreement: float
    governance_alignment: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "route_confidence": self.route_confidence,
            "signals": self.signals,
            "weights": self.weights,
            "fused_score": self.fused_score,
            "agreement": self.agreement,
            "governance_alignment": self.governance_alignment,
        }


ROUTE_WEIGHTS: dict[str, dict[str, float]] = {
    "exact": {
        "lexical": 0.34,
        "semantic": 0.14,
        "graph": 0.10,
        "compressed": 0.08,
        "scope": 0.16,
        "activation": 0.12,
        "agreement": 0.06,
    },
    "relational": {
        "lexical": 0.18,
        "semantic": 0.18,
        "graph": 0.26,
        "compressed": 0.08,
        "scope": 0.14,
        "activation": 0.10,
        "agreement": 0.06,
    },
    "semantic": {
        "lexical": 0.12,
        "semantic": 0.34,
        "graph": 0.14,
        "compressed": 0.10,
        "scope": 0.12,
        "activation": 0.12,
        "agreement": 0.06,
    },
    "balanced": {
        "lexical": 0.22,
        "semantic": 0.22,
        "graph": 0.16,
        "compressed": 0.08,
        "scope": 0.14,
        "activation": 0.12,
        "agreement": 0.06,
    },
}


def classify_query_route(query: str) -> HybridRouteProfile:
    text = (query or "").strip().lower()
    tokens = [token for token in re.findall(r"\w+", text, flags=re.UNICODE) if token]
    if not tokens:
        return HybridRouteProfile("balanced", 0.5, ROUTE_WEIGHTS["balanced"])

    exact_markers = sum(
        1
        for token in tokens
        if any(ch.isdigit() for ch in token) or "." in token or "_" in token or len(token) >= 14
    )
    relational_markers = sum(
        1
        for token in tokens
        if token
        in {
            "with",
            "between",
            "related",
            "relation",
            "owner",
            "supports",
            "support",
            "through",
            "via",
            "after",
            "before",
            "beside",
            "alongside",
            "link",
        }
    )
    semantic_markers = sum(
        1
        for token in tokens
        if token
        in {
            "meaning",
            "mean",
            "about",
            "explain",
            "context",
            "summary",
            "theme",
            "intent",
            "story",
        }
    )

    exact_score = _clamp((exact_markers / max(1, len(tokens))) * 1.8 + (0.18 if len(tokens) <= 4 else 0.0))
    relational_score = _clamp((relational_markers / max(1, len(tokens))) * 2.2)
    semantic_score = _clamp((semantic_markers / max(1, len(tokens))) * 2.1 + (0.16 if len(tokens) >= 7 else 0.0))

    scored = {
        "exact": exact_score,
        "relational": relational_score,
        "semantic": semantic_score,
        "balanced": 0.45,
    }
    route = max(scored, key=scored.get)
    confidence = round(scored[route], 6)
    if confidence < 0.52:
        route = "balanced"
        confidence = 0.52
    return HybridRouteProfile(route, confidence, ROUTE_WEIGHTS[route])


def compute_signal_agreement(signals: dict[str, float]) -> float:
    active = [_clamp(value) for key, value in signals.items() if key != "agreement" and value > 0.0]
    if len(active) < 2:
        return round(active[0] if active else 0.0, 6)
    spread = max(active) - min(active)
    agreement = _clamp(1.0 - spread)
    return round(agreement, 6)


def compute_governance_alignment(
    *,
    admission_state: str,
    conflict_status: str,
    truth_role: str | None = None,
    governance_status: str | None = None,
) -> float:
    alignment = 0.62
    if admission_state == "validated":
        alignment += 0.16
    elif admission_state == "hypothesized":
        alignment -= 0.12
    elif admission_state in {"consolidated", "archived"}:
        alignment -= 0.18
    if conflict_status != "none":
        alignment -= 0.16
    if truth_role == "winner":
        alignment += 0.10
    elif truth_role == "contender":
        alignment -= 0.06
    if governance_status == "active":
        alignment += 0.06
    elif governance_status in {"suppressed", "disputed"}:
        alignment -= 0.08
    return round(_clamp(alignment), 6)


def fuse_hybrid_signals(
    *,
    route_profile: HybridRouteProfile,
    signals: dict[str, float],
    governance_alignment: float,
) -> HybridFusionResult:
    normalized = {key: _clamp(value) for key, value in signals.items()}
    agreement = compute_signal_agreement(normalized)
    weighted = sum(
        normalized.get(signal, 0.0) * weight
        for signal, weight in route_profile.weights.items()
        if signal != "agreement"
    )
    fused = weighted + (agreement * route_profile.weights.get("agreement", 0.0))
    fused = _clamp((fused * 0.84) + (governance_alignment * 0.16))
    return HybridFusionResult(
        route=route_profile.route,
        route_confidence=round(route_profile.confidence, 6),
        signals={**normalized, "agreement": agreement},
        weights=route_profile.weights,
        fused_score=round(fused, 6),
        agreement=agreement,
        governance_alignment=round(governance_alignment, 6),
    )


def hybrid_reason_tags(result: HybridFusionResult) -> list[str]:
    return [
        f"hybrid_route:{result.route}",
        f"hybrid_route_confidence:{result.route_confidence}",
        f"hybrid_fused_score:{result.fused_score}",
        f"hybrid_agreement:{result.agreement}",
        f"hybrid_governance_alignment:{result.governance_alignment}",
    ]
