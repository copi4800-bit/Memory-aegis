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
