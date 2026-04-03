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

    def profile(
        self,
        *,
        content: str,
        session_id: str | None = None,
        source_kind: str = "message",
    ) -> dict[str, object]:
        normalized = " ".join(content.lower().split())
        lane_scores = {
            "working": 0.15,
            "procedural": 0.15,
            "semantic": 0.15,
            "episodic": 0.15,
        }

        if session_id and any(hint in normalized for hint in WORKING_HINTS):
            lane_scores["working"] += 0.5
        if normalized.startswith(PROCEDURAL_PREFIXES) or NUMBERED_STEP_PATTERN.search(normalized):
            lane_scores["procedural"] += 0.55
        if any(verb in normalized for verb in SEMANTIC_VERBS):
            lane_scores["semantic"] += 0.4
        if session_id and source_kind in {"message", "manual"}:
            lane_scores["working"] += 0.1
        if source_kind == "manual":
            lane_scores["semantic"] += 0.05
            lane_scores["procedural"] += 0.05

        ordered = sorted(lane_scores.items(), key=lambda item: item[1], reverse=True)
        predicted_lane, predicted_score = ordered[0]
        runner_up_score = ordered[1][1]
        chalicotherium_ecology_fit = min(0.99, 0.36 + (predicted_score - runner_up_score) * 1.4)
        return {
            "predicted_lane": predicted_lane,
            "lane_scores": {key: round(value, 3) for key, value in lane_scores.items()},
            "chalicotherium_ecology_fit": round(chalicotherium_ecology_fit, 3),
        }

    def infer(
        self,
        *,
        content: str,
        session_id: str | None = None,
        source_kind: str = "message",
    ) -> str:
        return str(
            self.profile(
                content=content,
                session_id=session_id,
                source_kind=source_kind,
            )["predicted_lane"]
        )
