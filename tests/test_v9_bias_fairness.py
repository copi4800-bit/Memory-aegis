from aegis_py.v9.models import MemoryRecordV9, TrustSignals, CorrectionSignals
from aegis_py.v9.scorer import ResidualScorer

def test_v9_bias_fairness():
    scorer = ResidualScorer()
    
    # Query: "Project X status"
    q = {"semantic_relevance": 0.8, "lexical_match": 0.5, "scope_fit": 1.0}
    
    # 1. Flashy Candidate (High lexical match, but low evidence)
    flashy = MemoryRecordV9(
        id="flashy",
        content="Project X is great!",
        canonical_subject="project_x",
        trust=TrustSignals(evidence_strength=0.1, trust_score=0.3)
    )
    
    # 2. Truth Candidate (Low lexical match, but high evidence and winner)
    truth = MemoryRecordV9(
        id="truth",
        content="Project X is currently in phase 2 with verified milestones.",
        canonical_subject="project_x",
        correction=CorrectionSignals(is_slot_winner=True, correction_freshness=0.9),
        trust=TrustSignals(evidence_strength=0.9, trust_score=0.9)
    )
    
    score_flashy = scorer.score(flashy, q).factors["final_score"]
    score_truth = scorer.score(truth, q).factors["final_score"]
    
    assert score_truth > score_flashy, f"Truth ({score_truth}) should be preferred over Flashy ({score_flashy})"
    print("✅ test_v9_bias_fairness passed!")

if __name__ == "__main__":
    test_v9_bias_fairness()
