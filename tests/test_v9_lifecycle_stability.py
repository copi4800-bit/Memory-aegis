from aegis_py.v9.models import MemoryRecordV9, LifecycleSignals, TrustSignals
from aegis_py.v9.scorer import ResidualScorer

def test_v9_lifecycle_stability():
    scorer = ResidualScorer()
    
    # Query: "Server access instructions"
    q = {"semantic_relevance": 0.8}
    
    # 1. New, unvalidated memory
    new_mem = MemoryRecordV9(
        id="new",
        content="Instruction A",
        canonical_subject="server_access",
        lifecycle=LifecycleSignals(usage_count=0, staleness_index=0.0)
    )
    
    # 2. Old, but highly validated and reused memory (Stable)
    stable_mem = MemoryRecordV9(
        id="stable",
        content="Instruction B",
        canonical_subject="server_access",
        lifecycle=LifecycleSignals(usage_count=50, validated_reuse_count=50, staleness_index=0.2),
        trust=TrustSignals(stability_score=1.0)
    )
    
    score_new = scorer.score(new_mem, q).factors["final_score"]
    score_stable = scorer.score(stable_mem, q).factors["final_score"]
    
    # Stable, validated memory should outrank a new, unvalidated one if relevance is equal
    assert score_stable > score_new, f"Stable ({score_stable}) should be preferred over New ({score_new})"
    print("✅ test_v9_lifecycle_stability passed!")

if __name__ == "__main__":
    test_v9_lifecycle_stability()
