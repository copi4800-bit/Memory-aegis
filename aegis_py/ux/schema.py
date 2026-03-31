from __future__ import annotations
from typing import Any
from .i18n import get_text

# Standard thresholds for v8 signals (from 5.md / 6.md)
SIGNAL_THRESHOLDS = {
    "strong": 0.85,
    "good": 0.70,
    "moderate": 0.50,
    "weak": 0.35,
    "marginal": 0.20
}

def get_signal_label(score: float, keys: list[str] = None, locale: str = "vi") -> str:
    """Helper to convert a 0-1 score to a human-readable band using i18n keys."""
    if keys is None:
        keys = ["signal_v_high", "signal_high", "signal_medium", "signal_low", "signal_critical"]
    
    key = keys[4]
    if score >= SIGNAL_THRESHOLDS["strong"]: key = keys[0]
    elif score >= SIGNAL_THRESHOLDS["good"]: key = keys[1]
    elif score >= SIGNAL_THRESHOLDS["moderate"]: key = keys[2]
    elif score >= SIGNAL_THRESHOLDS["weak"]: key = keys[3]
    
    return get_text(key, locale=locale)

def get_trust_label(score: float, locale: str = "vi") -> str:
    keys = ["trust_level_v_high", "trust_level_high", "trust_level_medium", "trust_level_low", "trust_level_none"]
    return get_signal_label(score, keys, locale=locale)

def get_readiness_label(score: float, locale: str = "vi") -> str:
    keys = ["readiness_level_ready", "readiness_level_good", "readiness_level_normal", "readiness_level_faded", "readiness_level_latent"]
    return get_signal_label(score, keys, locale=locale)

def get_conflict_label(score: float, locale: str = "vi") -> str:
    keys = ["conflict_level_v_high", "conflict_level_high", "conflict_level_medium", "conflict_level_low", "conflict_level_none"]
    return get_signal_label(score, keys, locale=locale)

def unify_v8_signals(signals: dict[str, Any], locale: str = "vi") -> dict[str, Any]:
    """
    Translates v8 raw signals into the unified 5.md Data Contract.
    """
    # Base schema mapping
    unified = {
        "belief": {
            "score": signals.get("belief_score", 0.0),
            "level": get_signal_label(signals.get("belief_score", 0.0), locale=locale)
        },
        "trust": {
            "score": signals.get("trust_score", 0.0),
            "level": get_trust_label(signals.get("trust_score", 0.0), locale=locale)
        },
        "readiness": {
            "score": signals.get("readiness_score", 0.0),
            "level": get_readiness_label(signals.get("readiness_score", 0.0), locale=locale)
        },
        "conflict": {
            "score": signals.get("conflict_signal", 0.0),
            "level": get_conflict_label(signals.get("conflict_signal", 0.0), locale=locale)
        },
        "evidence": {
            "score": signals.get("evidence_signal", 0.0),
            "level": get_signal_label(signals.get("evidence_signal", 0.0), locale=locale)
        },
        "decay": {
            "score": signals.get("decay_signal", 0.0),
            "level": get_signal_label(signals.get("decay_signal", 0.0), locale=locale)
        },
        "usage": {
            "score": signals.get("usage_signal", 0.0),
            "level": get_signal_label(signals.get("usage_signal", 0.0), locale=locale)
        },
        "support": {
            "score": signals.get("support_signal", 0.0),
            "level": get_signal_label(signals.get("support_signal", 0.0), locale=locale)
        }
    }
    return unified
