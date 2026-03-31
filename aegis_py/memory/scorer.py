from __future__ import annotations

import re


class WriteTimeScorer:
    """Deterministic conservative scoring for newly ingested memories."""

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return round(min(max(value, lower), upper), 3)

    @staticmethod
    def _contains_word(normalized: str, term: str) -> bool:
        return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized, flags=re.UNICODE) is not None

    def infer(
        self,
        *,
        content: str,
        memory_type: str,
        source_kind: str = "message",
    ) -> tuple[float, float]:
        normalized = " ".join(content.lower().split())
        profile = self.build_profile(
            content=content,
            memory_type=memory_type,
            source_kind=source_kind,
        )
        ambiguity_noise = profile["ambiguity_noise"]
        confidence = min(
            max(
                (
                    (profile["source_reliability"] * 0.26)
                    + (profile["directness"] * 0.26)
                    + (profile["specificity"] * 0.2)
                    + (profile["evidence_completeness"] * 0.14)
                    + (profile["recency"] * 0.12)
                    + (profile["frequency"] * 0.08)
                    - (profile["conflict_pressure"] * 0.16)
                    - (ambiguity_noise * 0.08)
                ),
                0.55,
            ),
            1.0,
        )
        if memory_type == "procedural":
            confidence += 0.04
        if profile["directness"] >= 0.95 and profile["specificity"] >= 0.8:
            confidence += 0.03
        if profile["evidence_completeness"] >= 0.88 and ambiguity_noise <= 0.2:
            confidence += 0.02
        activation = min(
            max(
                (
                    0.61
                    + (profile["specificity"] * 0.26)
                    + (profile["directness"] * 0.18)
                    + (profile["evidence_completeness"] * 0.06)
                    + (profile["frequency"] * 0.15)
                    - (profile["conflict_pressure"] * 0.12)
                    - (ambiguity_noise * 0.1)
                ),
                0.78,
            ),
            1.5,
        )
        if memory_type == "procedural":
            activation += 0.08
        if any(marker in normalized for marker in ("1.", "2.", "steps", "how to", "procedure", "must", "requires")):
            activation += 0.08
        if 0.96 <= activation <= 1.04:
            activation = 1.0
        return round(confidence, 3), round(activation, 3)

    def build_profile(
        self,
        *,
        content: str,
        memory_type: str,
        source_kind: str = "message",
    ) -> dict[str, float]:
        normalized = " ".join(content.lower().split())
        token_count = len(re.findall(r"\w+", normalized, flags=re.UNICODE))
        sentence_count = max(1, len(re.findall(r"[.!?]+", content)) or 1)
        digits_count = len(re.findall(r"\d", content))
        has_list_markers = any(marker in normalized for marker in ("1.", "2.", "steps", "how to", "procedure"))
        has_modality = any(marker in normalized for marker in ("must", "requires", "always", "never"))
        has_hedging = any(marker in normalized for marker in ("maybe", "perhaps", "probably", "có lẽ", "hình như"))
        has_negation = (
            self._contains_word(normalized, "not")
            or self._contains_word(normalized, "never")
            or self._contains_word(normalized, "no")
            or self._contains_word(normalized, "không")
            or self._contains_word(normalized, "chưa")
        )
        has_temporal_detail = any(marker in normalized for marker in ("morning", "evening", "when", "while", "lúc", "khi", "buổi"))
        has_example_detail = any(marker in normalized for marker in ("because", "via", "using", "with", "under", "through", "do", "set", "open"))
        source_reliability = 0.9 if source_kind == "manual" else 0.86 if source_kind == "message" else 0.82
        recency = 0.78
        specificity = min(0.98, 0.55 + min(token_count, 20) * 0.018)
        directness = 0.82
        frequency = 0.52
        conflict_pressure = 0.12
        evidence_completeness = 0.5 + min(token_count, 24) * 0.012
        ambiguity_noise = 0.14

        if memory_type == "procedural":
            directness += 0.08
            frequency += 0.08
            evidence_completeness += 0.08
        elif memory_type == "semantic":
            directness += 0.06
            specificity += 0.06
            evidence_completeness += 0.05
        elif memory_type == "working":
            source_reliability -= 0.05
            recency += 0.08

        if has_modality:
            directness += 0.06
            specificity += 0.03
            evidence_completeness += 0.06
        if has_list_markers:
            directness += 0.05
            frequency += 0.08
            evidence_completeness += 0.08
        if has_hedging:
            source_reliability -= 0.1
            directness -= 0.08
            conflict_pressure += 0.12
            ambiguity_noise += 0.2
        if has_negation:
            conflict_pressure += 0.1
            ambiguity_noise += 0.04
        if has_temporal_detail:
            specificity += 0.04
            evidence_completeness += 0.05
        if has_example_detail:
            specificity += 0.03
            evidence_completeness += 0.05
        if digits_count > 0:
            specificity += min(0.08, digits_count * 0.015)
            evidence_completeness += min(0.1, digits_count * 0.02)
        if sentence_count >= 2:
            evidence_completeness += min(0.1, (sentence_count - 1) * 0.04)
        if token_count <= 5:
            evidence_completeness -= 0.14
            ambiguity_noise += 0.04
        elif token_count >= 18:
            evidence_completeness += 0.06
        if token_count >= 36:
            ambiguity_noise += 0.05

        return {
            "source_reliability": self._clamp(source_reliability, 0.3, 0.99),
            "recency": self._clamp(recency, 0.3, 0.99),
            "specificity": self._clamp(specificity, 0.3, 0.99),
            "directness": self._clamp(directness, 0.3, 0.99),
            "evidence_completeness": self._clamp(evidence_completeness, 0.25, 0.99),
            "ambiguity_noise": self._clamp(ambiguity_noise, 0.0, 0.95),
            "frequency": self._clamp(frequency, 0.2, 0.95),
            "conflict_pressure": self._clamp(conflict_pressure, 0.0, 0.95),
        }
