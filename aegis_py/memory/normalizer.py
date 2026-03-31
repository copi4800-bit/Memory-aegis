from __future__ import annotations

import re


NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")
DOT_RUN_PATTERN = re.compile(r"\.+")


class SubjectNormalizer:
    """Deterministic local-only subject canonicalization."""

    def normalize(self, subject: str | None) -> str | None:
        if subject is None:
            return None
        lowered = subject.strip().lower()
        if not lowered:
            return None
        canonical = NON_ALNUM_PATTERN.sub(".", lowered)
        canonical = DOT_RUN_PATTERN.sub(".", canonical).strip(".")
        return canonical or None
