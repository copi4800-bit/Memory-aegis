from typing import Any, Dict, Optional
from .models import MemoryRecordV9

def build_v9_query_signals(
    result: Any, # SearchResult from run_scoped_search
    query: str,
    storage: Any,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Enhanced Builder that produces granular mathematical query signals for v9.
    Leverages stage-specific normalization and cross-signal calibration.
    """
    context = context or {}
    intent = context.get("intent", "normal_recall")
    
    # Map from retrieval stage
    stage = getattr(result, "retrieval_stage", "lexical")
    raw_score = getattr(result, "score", 0.0)
    reasons = getattr(result, "reasons", [])
    
    # 1. Normalized Base Signals
    # BM25 scores can be wide-ranging; we use a sigmoid-like squash for normalization
    def squash(x: float) -> float:
        import math
        return 1 / (1 + math.exp(-x)) if x != 0 else 0.0

    normalized_score = max(0.0, min(1.0, raw_score))
    
    semantic_relevance = 0.0
    lexical_match = 0.0
    link_support = 0.0
    
    if stage == "lexical":
        lexical_match = normalized_score
        # Check for multi-word exact matches in reasons
        exact_bonus = 0.1 if any("exact_match" in r for r in reasons) else 0.0
        semantic_relevance = 0.2 + (lexical_match * 0.3) + exact_bonus
    elif stage in ["semantic_recall", "vector"]:
        semantic_relevance = normalized_score
        lexical_match = 0.1 + (semantic_relevance * 0.2)
    elif stage in ["link_expansion", "multi_hop_link_expansion"]:
        link_support = normalized_score
        semantic_relevance = 0.4 + (link_support * 0.2)
        lexical_match = 0.1
    elif stage == "subject_expansion":
        semantic_relevance = 0.5
        lexical_match = 0.1
        
    # 2. Scope & Subject Alignment
    # Penalize if result subject doesn't align with query keywords (coarse hint)
    subject = getattr(result, "subject", "")
    scope_fit = 1.0
    if subject and query and subject.lower() not in query.lower():
        scope_fit = 0.9 # Minor penalty for subject drift
    
    # 3. Intent Sensitivity
    intent_signal = 1.0
    if intent == "conflict_probe":
        intent_signal = 1.5
    elif intent == "correction_lookup":
        intent_signal = 1.3
    elif intent == "preference_lookup":
        intent_signal = 1.2

    return {
        "semantic_relevance": min(1.0, semantic_relevance),
        "lexical_match": min(1.0, lexical_match),
        "scope_fit": scope_fit,
        "link_support": min(1.0, link_support),
        "query_intent": intent_signal
    }
