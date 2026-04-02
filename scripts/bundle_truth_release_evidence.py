from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.check_truth_spotlight_gate import evaluate_thresholds


DEFAULT_SUMMARY = Path(".planning/benchmarks/truth_spotlight_summary.json")
DEFAULT_REPORT = Path(".planning/benchmarks/truth_spotlight_report.md")
DEFAULT_BUNDLE = Path(".planning/benchmarks/truth_release_evidence_bundle.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_bundle(summary_path: Path, report_path: Path, summary: dict[str, Any]) -> dict[str, Any]:
    passed, failures = evaluate_thresholds(summary)
    return {
        "bundle": "truth_release_evidence",
        "passed": passed,
        "failures": failures,
        "summary_path": str(summary_path),
        "report_path": str(report_path),
        "summary": summary.get("summary", {}),
        "grouped_summary": summary.get("grouped_summary", {}),
        "scenario_catalog": summary.get("scenario_catalog", {}),
        "scenario_count": len(summary.get("scenarios", [])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bundle truth evaluation outputs into one release-evidence manifest.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY, help="Path to truth spotlight summary JSON.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Path to truth spotlight Markdown report.")
    parser.add_argument("--output", type=Path, default=DEFAULT_BUNDLE, help="Output bundle manifest JSON path.")
    args = parser.parse_args()

    summary = load_json(args.summary)
    bundle = build_bundle(args.summary, args.report, summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Artifact] Wrote {args.output.resolve()}")
    return 0 if bundle["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
