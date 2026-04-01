from __future__ import annotations
from typing import Any, Dict
from .models import JudgmentTrace

class FaithfulRenderer:
    """
    Translates v9 JudgmentTrace into human-centric, faithful explanations.
    Follows 'Explainable by construction' philosophy.
    """

    FACTOR_MAP_VI = {
        "sem": "khớp ngữ nghĩa mạnh",
        "lex": "trùng khớp từ khóa",
        "scope": "nằm đúng phạm vi tìm kiếm",
        "link": "liên quan qua các kết nối",
        "trust": "có độ tin cậy cao",
        "conflict": "đang có mâu thuẫn cần lưu ý",
        "corr": "là bản sửa lỗi mới nhất",
        "hard_constraint_winner": "được xác nhận là sự thật hiện tại",
        "hard_constraint_conflict": "bị loại do mâu thuẫn nghiêm trọng",
        "decay": "bắt đầu mờ nhạt theo thời gian",
        "stale": "không còn phù hợp với hiện tại",
        "reuse": "đã được sếp tin dùng nhiều lần",
        "b_truth": "minh bạch về phả hệ sự thật"
    }

    def render(self, trace: JudgmentTrace, locale: str = "vi", detail: str = "standard") -> str:
        """Generates a structured narrative from the trace."""
        decisive = trace.decisive_factor
        decisive_text = self.FACTOR_MAP_VI.get(decisive, "phù hợp bối cảnh")

        # 1. Compact Narrative (1 sentence)
        if detail == "compact":
            return f"Em chọn kết quả này vì {decisive_text}."

        # 2. Standard Narrative (Reason + Primary Boosts)
        parts = [f"Em chọn kết quả này vì {decisive_text}."]
        positive_boosts = [k for k, v in trace.factors.items() if v > 0.2 and k != decisive and k in self.FACTOR_MAP_VI]
        negative_penalties = [k for k, v in trace.factors.items() if v < -0.2 and k != decisive and k in self.FACTOR_MAP_VI]

        if positive_boosts:
            boost_texts = [self.FACTOR_MAP_VI[k] for k in positive_boosts[:2]]
            parts.append(f"Ngoài ra, nó còn {' và '.join(boost_texts)}.")

        if negative_penalties:
            penalty_texts = [self.FACTOR_MAP_VI[k] for k in negative_penalties[:2]]
            parts.append(f"Dù vậy, em có lưu ý là nó {' và '.join(penalty_texts)}.")

        if detail == "standard":
            return " ".join(parts)

        # 3. Deep Narrative (Math + Delta details)
        parts.append(f"\n[v9 Audit]: base={trace.base_score:.2f}, judge={trace.judge_delta:+.2f}, life={trace.life_delta:+.2f}, final={trace.factors.get('final_score', 0.0):.2f}.")
        return " ".join(parts)

