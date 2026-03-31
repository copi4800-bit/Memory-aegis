from __future__ import annotations

import re


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
