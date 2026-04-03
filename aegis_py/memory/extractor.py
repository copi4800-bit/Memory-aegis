from __future__ import annotations

import re


WORD_PATTERN = re.compile(r"[a-z0-9]+")
WHITESPACE_PATTERN = re.compile(r"\s+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "has",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "with",
}


class ContentExtractor:
    """Deterministic local-only fallback extraction for ingest metadata."""

    def derive_subject(self, content: str) -> str | None:
        tokens = self._keywords(content)
        if not tokens:
            return None
        return ".".join(tokens[:3])

    def derive_summary(self, content: str, *, limit: int = 96) -> str | None:
        normalized = WHITESPACE_PATTERN.sub(" ", content).strip()
        if not normalized:
            return None
        if len(normalized) <= limit:
            return normalized
        cutoff = normalized[: limit - 3].rstrip()
        if " " in cutoff:
            cutoff = cutoff.rsplit(" ", 1)[0]
        return f"{cutoff}..."

    def _keywords(self, content: str) -> list[str]:
        tokens: list[str] = []
        seen: set[str] = set()
        for token in WORD_PATTERN.findall(content.lower()):
            if len(token) < 3 or token in STOPWORDS:
                continue
            if token in seen:
                continue
            seen.add(token)
            tokens.append(token)
        return tokens

    def derive_profile(self, content: str) -> dict[str, object]:
        normalized = WHITESPACE_PATTERN.sub(" ", content).strip()
        keywords = self._keywords(content)
        structural_markers = sum(
            1
            for marker in (":", ";", "->", "1.", "2.", "because", "using", "before", "after")
            if marker in normalized.lower()
        )
        dimetrodon_feature_separation = min(
            0.99,
            0.24 + (min(len(keywords), 8) * 0.07) + (min(structural_markers, 4) * 0.06),
        )
        return {
            "keywords": keywords[:8],
            "keyword_count": len(keywords),
            "structural_markers": structural_markers,
            "dimetrodon_feature_separation": round(dimetrodon_feature_separation, 3),
        }
