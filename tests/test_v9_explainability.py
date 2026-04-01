from aegis_py.v9.models import MemoryRecordV9, TrustSignals, CorrectionSignals
from aegis_py.v9.scorer import ResidualScorer

def test_v9_explainability():
    scorer = ResidualScorer()
    
    # 1. Correction Winner case
    mem = MemoryRecordV9(
        id="mem1",
        content="Winner content",
        canonical_subject="test",
        correction=CorrectionSignals(is_slot_winner=True, correction_freshness=1.0)
    )
    q = {"semantic_relevance": 0.5}
    trace = scorer.score(mem, q)
    
    # The decisive factor should be 'hard_constraint_winner' or 'corr'
    assert trace.decisive_factor in ["hard_constraint_winner", "corr"]
    
    # 2. Strong Trust case
    mem2 = MemoryRecordV9(
        id="mem2",
        content="Trusted content",
        canonical_subject="test",
        trust=TrustSignals(evidence_strength=1.0, trust_score=1.0)
    )
    trace2 = scorer.score(mem2, q)
    assert trace2.decisive_factor == "trust"
    print("✅ test_v9_explainability passed!")

if __name__ == "__main__":
    test_v9_explainability()
