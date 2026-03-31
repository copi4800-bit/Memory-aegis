from __future__ import annotations
from typing import Any
from .i18n import get_text

def generate_human_reason(signals: dict[str, Any], locale: str = "vi") -> str:
    """
    Translates v8 internal signals (Math) into a human-centric narrative using i18n.
    """
    reasons: list[str] = []
    
    trust = signals.get("trust_score", 0.0)
    evidence = signals.get("evidence_signal", 0.0)
    conflict = signals.get("conflict_signal", 0.0)
    usage = signals.get("usage_signal", 0.0)
    regret = signals.get("regret_signal", 0.0)
    decay = signals.get("decay_signal", 0.0)
    
    # 1. Primary Selection Reason (Trust & Evidence)
    if trust >= 0.85:
        if evidence >= 0.8:
            reasons.append(get_text("reason_trust_v_high_evidence", locale=locale))
        else:
            reasons.append(get_text("reason_trust_v_high_stable", locale=locale))
    elif trust >= 0.65:
        reasons.append(get_text("reason_trust_high", locale=locale))
    
    # 2. Reinforcement/Usage
    if usage >= 0.7:
        reasons.append(get_text("reason_usage_high", locale=locale))
    
    # 3. Conflict Awareness
    if conflict >= 0.4:
        reasons.append(get_text("reason_conflict_high", locale=locale))
    
    # 4. Decay/Fading
    if decay >= 0.5 and usage <= 0.2:
        reasons.append(get_text("reason_decay_high", locale=locale))
    
    # 5. Regret (Learning from mistakes)
    if regret >= 0.5:
        reasons.append(get_text("reason_regret_high", locale=locale))

    # Fallback
    if not reasons:
        reasons.append(get_text("reason_fallback", locale=locale))
        
    return " ".join(reasons)

def get_signal_narratives(signals: dict[str, Any], locale: str = "vi") -> dict[str, str]:
    """
    Provides individual reason strings for each core signal.
    """
    narratives = {
        "trust": (
            get_text("narrative_trust_v_high", locale=locale) if signals.get("trust_score", 0.0) >= 0.9 
            else get_text("narrative_trust_high", locale=locale) if signals.get("trust_score", 0.0) >= 0.7
            else get_text("narrative_trust_medium", locale=locale)
        ),
        "evidence": (
            get_text("narrative_evidence_high", locale=locale) if signals.get("evidence_signal", 0.0) >= 0.7
            else get_text("narrative_evidence_low", locale=locale)
        ),
        "conflict": (
            get_text("narrative_conflict_high", locale=locale) if signals.get("conflict_signal", 0.0) >= 0.4
            else get_text("narrative_conflict_low", locale=locale)
        )
    }
    return narratives
