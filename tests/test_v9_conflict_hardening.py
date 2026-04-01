from aegis_py.v9.models import MemoryRecordV9, ConflictSignals, TrustSignals
from aegis_py.v9.scorer import ResidualScorer

def test_v9_conflict_hardening():
    scorer = ResidualScorer()
    
    # 1. Normal Memory (No conflict)
    normal_mem = MemoryRecordV9(
        id="mem_normal",
        content="The server is in Zone A.",
        canonical_subject="server_location",
        trust=TrustSignals(trust_score=0.7)
    )
    
    # 2. Conflict Probe (Has unresolved contradiction)
    # This should be penalized heavily by v9
    conflict_mem = MemoryRecordV9(
        id="mem_conflict",
        content="The server is in Zone B.",
        canonical_subject="server_location",
        conflict=ConflictSignals(unresolved_contradiction=0.8, open_conflict_count=1),
        trust=TrustSignals(trust_score=0.7)
    )
    
    q = {"semantic_relevance": 1.0, "lexical_match": 1.0, "scope_fit": 1.0}
    
    score_normal = scorer.score(normal_mem, q).factors["final_score"]
    score_conflict = scorer.score(conflict_mem, q).factors["final_score"]
    
    # Assertion: Conflict memory should be penalized
    assert score_conflict < score_normal, f"Conflict memory ({score_conflict}) should be lower than normal ({score_normal})"
    assert score_conflict < 0, f"Unresolved contradictions should lead to negative scores, got {score_conflict}"
    print("✅ test_v9_conflict_hardening passed!")

if __name__ == "__main__":
    test_v9_conflict_hardening()
