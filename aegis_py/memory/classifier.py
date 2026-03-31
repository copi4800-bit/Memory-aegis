from __future__ import annotations

import re


PROCEDURAL_PREFIXES = (
    "how to ",
    "steps to ",
    "run ",
    "deploy ",
    "procedure:",
    "workflow:",
    "to ",
)
WORKING_HINTS = (
    "temporary",
    "for this session",
    "todo",
    "note to self",
    "remember for now",
)
SEMANTIC_VERBS = (" is ", " are ", " means ", " requires ", " refers to ")
NUMBERED_STEP_PATTERN = re.compile(r"\b1\.\s+\w+")


class LaneClassifier:
    """Deterministic conservative lane inference for omitted types."""

    def infer(
        self,
        *,
        content: str,
        session_id: str | None = None,
        source_kind: str = "message",
    ) -> str:
        normalized = " ".join(content.lower().split())

        if session_id and any(hint in normalized for hint in WORKING_HINTS):
            return "working"
        if normalized.startswith(PROCEDURAL_PREFIXES) or NUMBERED_STEP_PATTERN.search(normalized):
            return "procedural"
        if any(verb in normalized for verb in SEMANTIC_VERBS):
            return "semantic"
        if session_id and source_kind in {"message", "manual"}:
            return "working"
        return "episodic"
