from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from aegis_py.retrieval.compressed_tier import (
    DEFAULT_COMPRESSED_TIER_ARTIFACT,
    evaluate_compressed_tier_gate,
    load_compressed_tier_artifact,
)

DEFAULT_REPORT = Path(".planning/benchmarks/compressed_candidate_tier_report.md")


def render_report(artifact: dict[str, Any], artifact_path: Path) -> str:
    summary = artifact.get("summary", {})
    scenarios = artifact.get("scenarios", [])
    passed, failures, _ = evaluate_compressed_tier_gate(artifact)
    lines = [
        "# Compressed Tier Report",
        "",
        f"- artifact: `{artifact_path}`",
        f"- passed: `{passed}`",
        f"- compressed_candidate_yield_rate: `{summary.get('compressed_candidate_yield_rate', 0.0)}`",
        f"- governed_top1_preservation_rate: `{summary.get('governed_top1_preservation_rate', 0.0)}`",
        f"- persistent_coverage_rate: `{summary.get('persistent_coverage_rate', 0.0)}`",
        f"- rebuild_backfill_rate: `{summary.get('rebuild_backfill_rate', 0.0)}`",
        f"- average_compressed_count: `{summary.get('average_compressed_count', 0.0)}`",
        "",
        "## Scenarios",
        "",
    ]
    for scenario in scenarios:
        lines.extend(
            [
                f"### {scenario.get('name', 'unknown')}",
                "",
                f"- compressed_candidate_found: `{scenario.get('compressed_candidate_found', False)}`",
                f"- governed_top1_preserved: `{scenario.get('governed_top1_preserved', False)}`",
                f"- persistent_coverage_preserved: `{scenario.get('persistent_coverage_preserved', True)}`",
                f"- rebuild_backfill_preserved: `{scenario.get('rebuild_backfill_preserved', True)}`",
                f"- compressed_count: `{scenario.get('compressed_count', 0)}`",
                "",
            ]
        )
    if failures:
        lines.extend(["## Failures", ""])
        lines.extend(f"- {item}" for item in failures)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Markdown report from compressed tier benchmark output.")
    parser.add_argument("--artifact", type=Path, default=DEFAULT_COMPRESSED_TIER_ARTIFACT, help="Input benchmark summary JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT, help="Output Markdown report path.")
    args = parser.parse_args()

    artifact = load_compressed_tier_artifact(args.artifact)
    if artifact is None:
        raise SystemExit(f"Artifact not found: {args.artifact}")
    report = render_report(artifact, args.artifact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"[Artifact] Wrote {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
