from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if token]


def _band(score: float) -> str:
    if score >= 0.72:
        return "strong"
    if score >= 0.45:
        return "medium"
    return "light"


def _set_bit(mask: int, position: int) -> int:
    return mask | (1 << position)


def _bit_count(value: int) -> int:
    return int(value.bit_count())


def _hash_token(token: str, *, salt: str, width: int) -> int:
    digest = hashlib.blake2b(f"{salt}:{token}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % width


@dataclass(frozen=True)
class CompressedSignature:
    lexical_mask: int
    semantic_mask: int
    lexical_width: int
    semantic_width: int


@dataclass(frozen=True)
class CompressedPrefilterMatch:
    score: float
    lexical_overlap: float
    semantic_overlap: float
    band: str
    tier: str


class CompressedCandidatePrefilter:
    """TurboQuant-inspired candidate prefilter using asymmetric compressed token signatures."""

    def __init__(self, *, lexical_width: int = 64, semantic_width: int = 32):
        self.lexical_width = lexical_width
        self.semantic_width = semantic_width

    def build_signature(
        self,
        text: str,
        *,
        semantic_terms: Iterable[str] | None = None,
    ) -> CompressedSignature:
        lexical_mask = 0
        semantic_mask = 0
        for token in _tokens(text):
            lexical_mask = _set_bit(
                lexical_mask,
                _hash_token(token, salt="lexical", width=self.lexical_width),
            )
        for token in semantic_terms or ():
            normalized = str(token).strip().lower()
            if not normalized:
                continue
            semantic_mask = _set_bit(
                semantic_mask,
                _hash_token(normalized, salt="semantic", width=self.semantic_width),
            )
        return CompressedSignature(
            lexical_mask=lexical_mask,
            semantic_mask=semantic_mask,
            lexical_width=self.lexical_width,
            semantic_width=self.semantic_width,
        )

    def match(
        self,
        query: CompressedSignature,
        candidate: CompressedSignature,
        *,
        tier: str,
    ) -> CompressedPrefilterMatch:
        lexical_overlap = self._overlap(query.lexical_mask, candidate.lexical_mask)
        semantic_overlap = self._overlap(query.semantic_mask, candidate.semantic_mask)
        score = min(0.99, (lexical_overlap * 0.72) + (semantic_overlap * 0.28))
        return CompressedPrefilterMatch(
            score=round(score, 6),
            lexical_overlap=round(lexical_overlap, 6),
            semantic_overlap=round(semantic_overlap, 6),
            band=_band(score),
            tier=tier,
        )

    def signature_from_payload(self, payload: dict[str, object] | None) -> CompressedSignature | None:
        if not isinstance(payload, dict):
            return None
        try:
            lexical_mask = int(str(payload.get("lexical_mask") or "0"), 16)
            semantic_mask = int(str(payload.get("semantic_mask") or "0"), 16)
            lexical_width = int(payload.get("lexical_width") or self.lexical_width)
            semantic_width = int(payload.get("semantic_width") or self.semantic_width)
        except (TypeError, ValueError):
            return None
        return CompressedSignature(
            lexical_mask=lexical_mask,
            semantic_mask=semantic_mask,
            lexical_width=lexical_width,
            semantic_width=semantic_width,
        )

    def _overlap(self, left: int, right: int) -> float:
        if left == 0 or right == 0:
            return 0.0
        shared = _bit_count(left & right)
        total = max(_bit_count(left), 1)
        return shared / total
