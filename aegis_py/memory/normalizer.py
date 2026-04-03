from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")
DOT_RUN_PATTERN = re.compile(r"\.+")


@dataclass(frozen=True)
class SubjectNormalizationProfile:
    raw_subject: str | None
    canonical_subject: str | None
    ammonite_spiral_stability: float
    segment_count: int
    alnum_retention_ratio: float


class SubjectNormalizer:
    """Deterministic local-only subject canonicalization."""

    def _strip_accents(self, text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in decomposed if not unicodedata.combining(ch))

    def profile(self, subject: str | None) -> SubjectNormalizationProfile:
        if subject is None:
            return SubjectNormalizationProfile(
                raw_subject=None,
                canonical_subject=None,
                ammonite_spiral_stability=0.0,
                segment_count=0,
                alnum_retention_ratio=0.0,
            )

        lowered = self._strip_accents(subject.strip().lower())
        if not lowered:
            return SubjectNormalizationProfile(
                raw_subject=subject,
                canonical_subject=None,
                ammonite_spiral_stability=0.0,
                segment_count=0,
                alnum_retention_ratio=0.0,
            )

        canonical = NON_ALNUM_PATTERN.sub(".", lowered)
        canonical = DOT_RUN_PATTERN.sub(".", canonical).strip(".") or None
        raw_alnum = len(re.findall(r"[a-z0-9]", lowered))
        canonical_alnum = len(re.findall(r"[a-z0-9]", canonical or ""))
        segment_count = len([part for part in (canonical or "").split(".") if part])
        retention_ratio = 0.0 if raw_alnum == 0 else canonical_alnum / raw_alnum
        ammonite_spiral_stability = min(
            0.99,
            0.38 + (min(segment_count, 4) * 0.08) + (retention_ratio * 0.34),
        )
        return SubjectNormalizationProfile(
            raw_subject=subject,
            canonical_subject=canonical,
            ammonite_spiral_stability=round(ammonite_spiral_stability, 3),
            segment_count=segment_count,
            alnum_retention_ratio=round(retention_ratio, 3),
        )

    def normalize(self, subject: str | None) -> str | None:
        return self.profile(subject).canonical_subject
