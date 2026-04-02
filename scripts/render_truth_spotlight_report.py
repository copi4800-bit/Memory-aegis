from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.compare_truth_spotlight import compare_scenarios, metric_delta


DEFAULT_ARTIFACT = Path(".planning/benchmarks/truth_spotlight_summary.json")
DEFAULT_REPORT = Path(".planning/benchmarks/truth_spotlight_report.md")
DEFAULT_BEFORE_ARTIFACT = Path(".planning/benchmarks/truth_spotlight_summary.before.json")


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_report(
    summary: dict[str, Any],
    artifact_path: Path,
    before_summary: dict[str, Any] | None = None,
    before_artifact_path: Path | None = None,
) -> str:
    metrics = summary.get("summary", {})
    grouped_summary = summary.get("grouped_summary", {})
    scenario_catalog = summary.get("scenario_catalog", {})
    scenarios = summary.get("scenarios", [])

    lines = [
        "# Truth Spotlight Report",
        "",
        f"- artifact: `{artifact_path}`",
        f"- passed: `{metrics.get('passed', False)}`",
        f"- current_truth_top1_rate: `{metrics.get('current_truth_top1_rate', 0.0)}`",
        f"- suppressed_visibility_rate: `{metrics.get('suppressed_visibility_rate', 0.0)}`",
        f"- superseded_visibility_rate: `{metrics.get('superseded_visibility_rate', 0.0)}`",
        "",
    ]

    if before_summary is not None and before_artifact_path is not None:
        before_metrics = before_summary.get("summary", {})
        lines.extend(
            [
                "## Historical Trend",
                "",
                f"- previous_artifact: `{before_artifact_path}`",
                f"- current_truth_top1_rate: {before_metrics.get('current_truth_top1_rate', 0.0)} -> {metrics.get('current_truth_top1_rate', 0.0)} ({metric_delta(float(before_metrics.get('current_truth_top1_rate', 0.0)), float(metrics.get('current_truth_top1_rate', 0.0)))})",
                f"- suppressed_visibility_rate: {before_metrics.get('suppressed_visibility_rate', 0.0)} -> {metrics.get('suppressed_visibility_rate', 0.0)} ({metric_delta(float(before_metrics.get('suppressed_visibility_rate', 0.0)), float(metrics.get('suppressed_visibility_rate', 0.0)))})",
                f"- superseded_visibility_rate: {before_metrics.get('superseded_visibility_rate', 0.0)} -> {metrics.get('superseded_visibility_rate', 0.0)} ({metric_delta(float(before_metrics.get('superseded_visibility_rate', 0.0)), float(metrics.get('superseded_visibility_rate', 0.0)))})",
            ]
        )
        scenario_lines = compare_scenarios(before_summary, summary)
        if scenario_lines:
            lines.extend(["- scenario_changes:"])
            lines.extend(f"  {item}" for item in scenario_lines)
        lines.append("")

    lines.extend(["## Grouped Summary", ""])
    if grouped_summary:
        for category, category_metrics in grouped_summary.items():
            lines.extend(
                [
                    f"### {category}",
                    "",
                    f"- scenario_count: `{category_metrics.get('scenario_count', 0)}`",
                    f"- pass_rate: `{category_metrics.get('pass_rate', 0.0)}`",
                    f"- suppressed_visibility_rate: `{category_metrics.get('suppressed_visibility_rate', 0.0)}`",
                    f"- superseded_visibility_rate: `{category_metrics.get('superseded_visibility_rate', 0.0)}`",
                    "",
                ]
            )
    else:
        lines.extend(["- No grouped summary available.", ""])

    lines.extend(["## Scenario Catalog", ""])
    if scenario_catalog:
        for name, metadata in scenario_catalog.items():
            lines.extend(
                [
                    f"### {name}",
                    "",
                    f"- title: `{metadata.get('title', '')}`",
                    f"- category: `{metadata.get('category', 'uncategorized')}`",
                    f"- intent: `{metadata.get('intent', 'n/a')}`",
                    f"- description: {metadata.get('description', '')}",
                    "",
                ]
            )
    else:
        lines.extend(["- No scenario catalog available.", ""])

    lines.extend(["## Scenarios", ""])
    for scenario in scenarios:
        lines.extend(
            [
                f"### {scenario.get('name', 'unknown')}",
                "",
                f"- category: `{scenario.get('category', 'uncategorized')}`",
                f"- status: `{'PASS' if scenario.get('passed') else 'FAIL'}`",
                f"- selected_id: `{scenario.get('selected_id', 'n/a')}`",
                f"- expected_id: `{scenario.get('expected_id', 'n/a')}`",
                f"- superseded_visible: `{scenario.get('superseded_visible', False)}`",
            ]
        )
        notes = scenario.get("notes") or []
        if notes:
            lines.append("- notes:")
            lines.extend(f"  - {note}" for note in notes)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Markdown report from truth spotlight benchmark output.")
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT, help="Input benchmark summary JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT, help="Output Markdown report path.")
    parser.add_argument(
        "--before-artifact",
        type=Path,
        default=DEFAULT_BEFORE_ARTIFACT,
        help="Optional previous benchmark summary JSON for trend rendering.",
    )
    args = parser.parse_args()

    summary = load_summary(args.artifact)
    before_summary = load_summary(args.before_artifact) if args.before_artifact.exists() else None
    before_artifact_path = args.before_artifact if before_summary is not None else None
    report = render_report(summary, args.artifact, before_summary, before_artifact_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"[Artifact] Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
