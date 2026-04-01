from aegis_py.v9.models import MemoryRecordV9, TrustSignals, CorrectionSignals
from aegis_py.v9.scorer import ResidualScorer

def test_v9_truth_alignment():
    scorer = ResidualScorer()
    
    # CASE: Old memory has perfect lexical overlap, but is superseded.
    # Query: "What is my favorite color?"
    query_signals = {
        "semantic_relevance": 0.9,
        "lexical_match": 1.0, # Perfect wording match
        "scope_fit": 1.0
    }
    
    # 1. Old Memory (Superseded)
    old_mem = MemoryRecordV9(
        id="mem_old",
        content="My favorite color is blue.",
        canonical_subject="favorite_color",
        correction=CorrectionSignals(is_slot_winner=False, is_superseded=True)
    )
    
    # 2. New Memory (Winner - Correction)
    # Wording is slightly different, but it's the truth winner.
    new_mem = MemoryRecordV9(
        id="mem_new",
        content="Actually, I prefer red now.",
        canonical_subject="favorite_color",
        correction=CorrectionSignals(is_slot_winner=True, is_superseded=False, correction_freshness=1.0),
        trust=TrustSignals(evidence_strength=1.0, trust_score=1.0)
    )
    
    score_old = scorer.score(old_mem, query_signals).factors["final_score"]
    score_new = scorer.score(new_mem, query_signals).factors["final_score"]
    
    # Assert Truth Winner defeated Lexical Bias
    assert score_new > score_old, f"Expected New Memory ({score_new}) > Old Memory ({score_old})"
    assert score_old < 0, f"Superseded memory should be penalized, but got {score_old}"
    print("✅ test_v9_truth_alignment passed!")

if __name__ == "__main__":
    test_v9_truth_alignment()
