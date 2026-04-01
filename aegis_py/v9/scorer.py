from __future__ import annotations
import math
from typing import List, Dict, Any
from .models import MemoryRecordV9, JudgmentTrace, MemoryState

class ResidualScorer:
    """
    Aegis v9 Residual Judgment Engine Scorer.
    Follows 'Fortress' Calibration: S_final = S_base + Delta_judge + Delta_life + H_constraints
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "base": {"sem": 0.63, "lex": 0.02, "scope": 0.20, "link": 0.10, "prior": 0.05},
            "judge": {"trust": 1.20, "conflict": 0.60, "corr": 0.70, "source": 0.15, "bias_bad": 1.50, "bias_truth": 0.60},
            "life": {"decay": 0.20, "ready": 0.15, "stale": 0.25, "reuse": 0.10, "archive": 0.10},
            "thresholds": {"slot_winner": 0.15, "conflict_safety": 0.5}
        }

    def score(self, memory: MemoryRecordV9, query_signals: Dict[str, float], intent: str = "normal_recall") -> JudgmentTrace:
        """
        Computes the unified v9 Residual Judgment Score.
        Formula: S_final = S_base + Δ_judge + Δ_life + H_constraints
        """
        trace = JudgmentTrace()
        
        # 1. Base Relevance Tier (S_base)
        trace.base_score = self.compute_base_score(memory, query_signals, trace)
        
        # 2. Judgment Tier (Delta_judge)
        trace.judge_delta = self.compute_judge_delta(memory, query_signals, trace, intent=intent)
        
        # 3. Lifecycle Tier (Delta_life)
        trace.life_delta = self.compute_life_delta(memory, trace)
        
        # 4. Preliminary Final Score
        pre_constraint_score = trace.base_score + trace.judge_delta + trace.life_delta
        
        # 5. Hard Constraints Tier (H_constraints)
        final_score = self.apply_hard_constraints(memory, pre_constraint_score, intent, trace)
        
        trace.factors["final_score"] = final_score
        
        # 6. Determine Decisive Factor
        self._determine_decisive_factor(trace)
        
        return trace

    def compute_base_score(self, m: MemoryRecordV9, q: Dict[str, float], trace: JudgmentTrace) -> float:
        w = self.config["base"]
        sem = w["sem"] * q.get("semantic_relevance", 0.0)
        lex = w["lex"] * q.get("lexical_match", 0.0)
        scope = w["scope"] * q.get("scope_fit", 1.0)
        link = w["link"] * q.get("link_support", 0.0)
        prior = w["prior"] * math.log1p(m.lifecycle.usage_count) * 0.1
        
        trace.factors.update({"sem": sem, "lex": lex, "scope": scope, "link": link, "prior": prior})
        return sem + lex + scope + link + prior

    def compute_judge_delta(self, m: MemoryRecordV9, query_signals: Dict[str, float], trace: JudgmentTrace, intent: str = "normal_recall") -> float:
        w = self.config["judge"]
        
        # Trust (Hyperbolic Squashing)
        trust_input = (2.0 * m.trust.evidence_strength + m.trust.support_strength + m.trust.stability_score - 2.0 * m.trust.regret_score + m.trust.trust_score)
        d_trust = w["trust"] * math.tanh(trust_input)
        
        # Conflict
        lambda_c = w["conflict"] if intent == "normal_recall" else 0.05
        d_conflict = -lambda_c * (m.conflict.open_conflict_count * 0.5 + m.conflict.conflict_severity + m.conflict.slot_collision + m.conflict.unresolved_contradiction)
        
        # Correction
        d_corr = w["corr"] * ((1.0 if m.correction.is_slot_winner else 0.0) - (1.5 if m.correction.is_superseded else 0.0) + m.correction.correction_freshness - m.correction.supersession_depth * 0.1)
        
        # Bias
        d_bias = self.compute_bias_delta(m, query_signals, trace)
        
        trace.factors.update({"trust": d_trust, "conflict": d_conflict, "corr": d_corr, "bias": d_bias})
        return d_trust + d_conflict + d_corr + d_bias

    def compute_bias_delta(self, m: MemoryRecordV9, q: Dict[str, float], trace: JudgmentTrace) -> float:
        w = self.config["judge"]
        lex_overlap = q.get("lexical_match", 0.0)
        truth_strength = (m.trust.evidence_strength + (1.0 if m.correction.is_slot_winner else 0.0)) / 2.0
        
        # Aggressive Lexical Bias Penalty:
        b_lex = max(0, lex_overlap - (truth_strength + 0.05)) * w["bias_bad"] * 4.0
        
        # NUCLEAR PENALTY: Zero-Trust Threshold (0.4)
        if m.trust.trust_score < 0.4:
            b_lex += 15.0 # Absolute exclusion
        
        b_rec = m.correction.correction_freshness * (1.0 - m.trust.trust_score) * 0.5 * w["bias_bad"]
        b_act = max(0, math.log1p(m.lifecycle.usage_count) - math.log1p(m.lifecycle.validated_reuse_count)) * 0.1 * w["bias_bad"]
        b_truth = truth_strength * w["bias_truth"]
        
        trace.factors.update({"b_lex": -b_lex, "b_rec": -b_rec, "b_act": -b_act, "b_truth": b_truth})
        return b_truth - (b_lex + b_rec + b_act)

    def compute_life_delta(self, m: MemoryRecordV9, trace: JudgmentTrace) -> float:
        w = self.config["life"]
        # Staleness Curve accelerated by 25% (6.25)
        d_decay = -w["decay"] * (1.0 - math.exp(-m.lifecycle.decay_rate * 6.25))
        d_ready = w["ready"] * m.lifecycle.readiness_base
        d_stale = -w["stale"] * m.lifecycle.staleness_index
        d_reuse = w["reuse"] * math.log1p(m.lifecycle.validated_reuse_count)
        d_archive = -w["archive"] * m.lifecycle.archive_pressure
        
        delta = d_decay + d_ready + d_stale + d_reuse + d_archive
        cap = 0.4
        final_d_life = max(-cap, min(cap, delta))
        
        trace.factors.update({"decay": d_decay, "ready": d_ready, "stale": d_stale, "reuse": d_reuse, "archive": d_archive, "life_final": final_d_life})
        return final_d_life

    def apply_hard_constraints(self, m: MemoryRecordV9, score: float, intent: str, trace: JudgmentTrace) -> float:
        t = self.config["thresholds"]
        
        # Exclusion constraints
        if m.lifecycle.memory_state == MemoryState.ARCHIVED:
            trace.factors["hard_constraint_archived"] = -10.0
            trace.hard_constraints_delta = -10.0
            return -10.0
            
        if m.correction.is_superseded:
            trace.factors["hard_constraint_superseded"] = -5.0
            trace.hard_constraints_delta = -5.0
            return -5.0

        # Conflict safety
        if intent == "normal_recall" and m.conflict.unresolved_contradiction > t["conflict_safety"]:
            trace.factors["hard_constraint_conflict"] = -5.0
            trace.hard_constraints_delta -= 5.0
            score -= 5.0
            
        # Promotion constraints
        if m.correction.is_slot_winner:
            trace.factors["hard_constraint_winner"] = t["slot_winner"]
            trace.hard_constraints_delta += t["slot_winner"]
            score += t["slot_winner"]
            
        return score

    def _determine_decisive_factor(self, trace: JudgmentTrace):
        """Identifies which factor had the most significant impact on the ranking."""
        relevant_factors = {k: v for k, v in trace.factors.items() if k not in ["final_score", "life_final", "scope"]}
        if not relevant_factors:
            trace.decisive_factor = "relevance"
            return
        
        # Priority: Hard constraints > Large Deltas > Base
        if trace.hard_constraints_delta < -1.0:
            trace.decisive_factor = "hard_constraint_archived" if "hard_constraint_archived" in trace.factors else "hard_constraint_superseded"
        elif trace.factors.get("hard_constraint_winner", 0) > 0.1:
            trace.decisive_factor = "hard_constraint_winner"
        else:
            sorted_factors = sorted(relevant_factors.items(), key=lambda x: abs(x[1]), reverse=True)
            trace.decisive_factor = sorted_factors[0][0]
