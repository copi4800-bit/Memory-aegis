from __future__ import annotations
from typing import Any, Dict
from .models import JudgmentTrace
from ..ux.i18n import get_text

class FaithfulRenderer:
    """
    Translates v9 JudgmentTrace into human-centric, faithful explanations.
    Follows 'Explain Before Acting' and 'Absolute Beauty' mandates.
    """

    def render(self, trace: JudgmentTrace, locale: str = "vi", detail: str = "standard") -> str:
        """Generates a structured narrative from the trace with UX layering."""
        # detail levels: standard (User mode), explain (Explain mode), deep (Audit mode)
        decisive = trace.decisive_factor
        
        # 1. Map natural wording from i18n
        factor_text = self._get_factor_text(trace, decisive, locale)

        # 2. Level 1: Standard / User Mode (1 concise, natural sentence)
        if detail == "standard" or detail == "compact":
            return f"Em chọn kết quả này vì {factor_text}."

        # 3. Level 2: Explain Mode (Natural narrative + Primary boosts)
        parts = [f"Em chọn kết quả này vì {factor_text}."]
        
        # Show primary boosts in explain mode
        positive_boosts = [k for k, v in trace.factors.items() if v > 0.15 and k != decisive]
        if positive_boosts:
            boost_texts = [self._get_factor_text(trace, k, locale) for k in positive_boosts[:2]]
            parts.append(f"Ngoài ra, nó còn {' và '.join(boost_texts)}.")
            
        if detail == "explain":
            return " ".join(parts)

        # 4. Level 3: Deep / Audit Mode (Math + Delta details)
        parts.append(f"\n[v9 Audit]: base={trace.base_score:.2f}, judge={trace.judge_delta:+.2f}, life={trace.life_delta:+.2f}, final={trace.factors.get('final_score', 0.0):.2f}.")
        return " ".join(parts)

    def _get_factor_text(self, trace: JudgmentTrace, factor: str, locale: str) -> str:
        """Returns natural wording for a specific factor based on trace context."""
        if factor == "corr":
            if trace.is_first_write:
                return get_text("wording_first_write", locale=locale)
            return get_text("wording_correction", locale=locale)
            
        if factor in ("hard_constraint_winner", "hard_constraint_confirmed"):
            if trace.is_first_write:
                return get_text("wording_first_write_confirmed", locale=locale)
            return get_text("wording_correction_confirmed", locale=locale)
            
        if factor == "trust":
            return get_text("reason_trust_v_high", locale=locale)
            
        if factor == "usage":
            return get_text("reason_usage_high", locale=locale)
            
        # Specific mappings for v9 scorer factors
        v9_map = {
            "sem": "khớp ngữ nghĩa mạnh",
            "lex": "trùng khớp từ khóa",
            "life": "có độ tươi mới cao",
            "bias": "phù hợp sở thích của sếp",
            "b_truth": "minh bạch về phả hệ sự thật"
        }
        if factor in v9_map:
            return v9_map[factor]
            
        # Fallback to generic i18n or factor name
        return get_text(f"reason_{factor}", locale=locale)
