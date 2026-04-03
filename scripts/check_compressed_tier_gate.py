from __future__ import annotations

import argparse
from pathlib import Path

from aegis_py.retrieval.compressed_tier import (
    DEFAULT_COMPRESSED_TIER_ARTIFACT,
    evaluate_compressed_tier_gate,
    load_compressed_tier_artifact,
)


def render_result(path: Path, passed: bool, failures: list[str], artifact: dict | None) -> str:
    summary = (artifact or {}).get("summary", {})
    lines = [
        "TruthKeep Compressed Tier Gate",
        f"artifact: {path}",
        f"passed: {'yes' if passed else 'no'}",
        f"compressed_candidate_yield_rate: {float(summary.get('compressed_candidate_yield_rate', 0.0)):.3f}",
        f"governed_top1_preservation_rate: {float(summary.get('governed_top1_preservation_rate', 0.0)):.3f}",
        f"persistent_coverage_rate: {float(summary.get('persistent_coverage_rate', 0.0)):.3f}",
        f"rebuild_backfill_rate: {float(summary.get('rebuild_backfill_rate', 0.0)):.3f}",
    ]
    if failures:
        lines.append("failures:")
        lines.extend(f"- {item}" for item in failures)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the compressed tier software-level gate.")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=DEFAULT_COMPRESSED_TIER_ARTIFACT,
        help="Path to the compressed candidate tier benchmark summary JSON.",
    )
    args = parser.parse_args()

    artifact = load_compressed_tier_artifact(args.artifact)
    passed, failures, _ = evaluate_compressed_tier_gate(artifact)
    print(render_result(args.artifact, passed, failures, artifact))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
