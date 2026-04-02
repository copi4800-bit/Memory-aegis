from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACT = Path(".planning/benchmarks/truth_spotlight_summary.json")
DEFAULT_THRESHOLDS = {
    "current_truth_top1_rate": 1.0,
    "suppressed_visibility_rate": 1.0,
    "superseded_visibility_rate": 0.75,
}
DEFAULT_GROUPED_THRESHOLDS = {
    "correction": {
        "pass_rate": 1.0,
        "suppressed_visibility_rate": 1.0,
        "superseded_visibility_rate": 1.0,
    },
    "conflict": {
        "pass_rate": 1.0,
        "suppressed_visibility_rate": 1.0,
        "superseded_visibility_rate": 1.0,
    },
    "lexical_resilience": {
        "pass_rate": 1.0,
        "suppressed_visibility_rate": 1.0,
        "superseded_visibility_rate": 1.0,
    },
    "override": {
        "pass_rate": 1.0,
        "suppressed_visibility_rate": 1.0,
    },
}


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_thresholds(
    summary: dict[str, Any],
    thresholds: dict[str, float] | None = None,
) -> tuple[bool, list[str]]:
    gate = thresholds or DEFAULT_THRESHOLDS
    summary_metrics = summary.get("summary", summary)
    failures: list[str] = []
    for key, minimum in gate.items():
        actual = float(summary_metrics.get(key, 0.0))
        if actual < minimum:
            failures.append(f"{key}={actual:.3f} fell below required {minimum:.3f}")
    grouped_summary = summary.get("grouped_summary", {})
    for category, category_thresholds in DEFAULT_GROUPED_THRESHOLDS.items():
        actual_group = grouped_summary.get(category, {})
        if not actual_group:
            failures.append(f"grouped_summary missing required category '{category}'")
            continue
        for key, minimum in category_thresholds.items():
            actual = float(actual_group.get(key, 0.0))
            if actual < minimum:
                failures.append(
                    f"{category}.{key}={actual:.3f} fell below required {minimum:.3f}"
                )
    return (len(failures) == 0, failures)


def render_result(path: Path, passed: bool, failures: list[str], summary: dict[str, Any]) -> str:
    summary_metrics = summary.get("summary", summary)
    grouped_summary = summary.get("grouped_summary", {})
    lines = [
        "Aegis Truth Spotlight Gate",
        f"artifact: {path}",
        f"passed: {'yes' if passed else 'no'}",
        f"current_truth_top1_rate: {float(summary_metrics.get('current_truth_top1_rate', 0.0)):.3f}",
        f"suppressed_visibility_rate: {float(summary_metrics.get('suppressed_visibility_rate', 0.0)):.3f}",
        f"superseded_visibility_rate: {float(summary_metrics.get('superseded_visibility_rate', 0.0)):.3f}",
    ]
    if grouped_summary:
        lines.append("grouped_summary:")
        for category, metrics in grouped_summary.items():
            lines.append(
                f"- {category}: pass_rate={float(metrics.get('pass_rate', 0.0)):.3f}, "
                f"suppressed_visibility_rate={float(metrics.get('suppressed_visibility_rate', 0.0)):.3f}, "
                f"superseded_visibility_rate={float(metrics.get('superseded_visibility_rate', 0.0)):.3f}"
            )
    if failures:
        lines.append("failures:")
        lines.extend(f"- {item}" for item in failures)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the governed truth spotlight gate.")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=DEFAULT_ARTIFACT,
        help="Path to the spotlight benchmark summary JSON.",
    )
    args = parser.parse_args()

    summary = load_summary(args.artifact)
    passed, failures = evaluate_thresholds(summary)
    print(render_result(args.artifact, passed, failures, summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
