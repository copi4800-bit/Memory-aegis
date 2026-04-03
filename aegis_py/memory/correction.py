from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Iterable


class CorrectionDetector:
    """Detects explicit correction signals in incoming text."""

    EN_PATTERNS = [
        r"\bno longer\b",
        r"\binstead of\b",
        r"\bcorrected to\b",
        r"\bactually\b",
        r"\bmoved to\b",
        r"\bchanged to\b",
        r"\bupdate:\b",
        r"\bcorrect:\b",
    ]

    VI_PATTERNS = [
        r"\bkhông còn là\b",
        r"\bthay vì\b",
        r"\bđã chuyển sang\b",
        r"\bthực ra\b",
        r"\bđã đổi thành\b",
        r"\bcải chính:\b",
        r"\bcập nhật:\b",
    ]

    def __init__(self):
        self.pattern = re.compile(
            "|".join(self.EN_PATTERNS + self.VI_PATTERNS), re.IGNORECASE
        )

    def is_correction(self, text: str) -> bool:
        """Returns True if the text contains an explicit correction signal."""
        if not text:
            return False
        return bool(self.pattern.search(text))


@dataclass
class CorrectionTarget:
    scope_type: str
    scope_id: str
    subject: str | None
    old_memory_id: str | None


def resolve_correction_target(
    content: str,
    *,
    default_scope_type: str,
    default_scope_id: str,
    scope_candidates: Iterable[tuple[str, str]],
    search_fn: Callable[..., list[Any]],
) -> CorrectionTarget:
    """Finds the best existing memory slot to correct without exposing search details to app surfaces."""
    resolved_scope_type = default_scope_type
    resolved_scope_id = default_scope_id
    existing: list[Any] = []

    for candidate_scope_type, candidate_scope_id in scope_candidates:
        existing = search_fn(
            content,
            scope_id=candidate_scope_id,
            scope_type=candidate_scope_type,
            limit=1,
            fallback_to_or=True,
        )
        if existing:
            resolved_scope_type = candidate_scope_type
            resolved_scope_id = candidate_scope_id
            break

    target_subject = None
    old_memory_id = None
    if existing:
        top_memory = existing[0].memory
        target_subject = top_memory.subject
        old_memory_id = top_memory.id

    return CorrectionTarget(
        scope_type=resolved_scope_type,
        scope_id=resolved_scope_id,
        subject=target_subject,
        old_memory_id=old_memory_id,
    )
