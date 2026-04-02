#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_ARTIFACT = Path(".planning/benchmarks/ingest_pressure_diagnostic.json")


def load_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_readiness(summary: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    scenarios = summary.get("scenarios", {})

    low = scenarios.get("low_confidence_repetitive", {})
    low_summary = low.get("summary", {})
    low_attempted = int(low_summary.get("attempted_writes", 0))
    low_accepted = int(low_summary.get("accepted_writes", 0))
    low_rejected = int(low_summary.get("rejected_or_noop_writes", 0))
    low_outcomes = low_summary.get("diagnostic_outcomes", {})
    low_blocked_reasons = low_summary.get("blocked_reason_counts", {})

    if not low_summary.get("reconciled", False):
        failures.append("low_confidence_repetitive did not reconcile diagnostic and actual outcomes")
    if low_accepted <= 0:
        failures.append("low_confidence_repetitive admitted no writes at all")
    if low_rejected <= 0:
        failures.append("low_confidence_repetitive produced no blocked/no-op writes")
    if int(low_outcomes.get("policy_block", 0)) <= 0:
        failures.append("low_confidence_repetitive produced no policy blocks")
    if int(low_outcomes.get("exact_dedup", 0)) <= 0:
        failures.append("low_confidence_repetitive produced no exact dedup outcomes")
    if int(low_blocked_reasons.get("blocked_low_confidence", 0)) != int(low_outcomes.get("policy_block", 0)):
        failures.append("low_confidence_repetitive policy blocks were not fully explained by blocked_low_confidence")
    if low_attempted != low_accepted + low_rejected:
        failures.append("low_confidence_repetitive attempted_writes did not match accepted + rejected")
    if not low_summary.get("canonical_admitted", False):
        failures.append("low_confidence_repetitive canonical checkpoint was not admitted")

    high = scenarios.get("high_confidence_distinct", {})
    high_summary = high.get("summary", {})
    high_attempted = int(high_summary.get("attempted_writes", 0))
    high_accepted = int(high_summary.get("accepted_writes", 0))
    high_rejected = int(high_summary.get("rejected_or_noop_writes", 0))
    high_outcomes = high_summary.get("diagnostic_outcomes", {})

    if not high_summary.get("reconciled", False):
        failures.append("high_confidence_distinct did not reconcile diagnostic and actual outcomes")
    if high_attempted <= 0:
        failures.append("high_confidence_distinct had no attempts")
    if high_accepted != high_attempted:
        failures.append("high_confidence_distinct did not admit every attempted write")
    if high_rejected != 0:
        failures.append("high_confidence_distinct should not have rejected/no-op writes")
    if int(high_outcomes.get("policy_block", 0)) != 0:
        failures.append("high_confidence_distinct should not contain policy blocks")
    if int(high_outcomes.get("exact_dedup", 0)) != 0:
        failures.append("high_confidence_distinct should not contain exact dedup outcomes")
    if not high_summary.get("canonical_admitted", False):
        failures.append("high_confidence_distinct canonical checkpoint was not admitted")

    return len(failures) == 0, failures


def render_result(path: Path, passed: bool, failures: list[str], summary: dict[str, Any]) -> str:
    scenarios = summary.get("scenarios", {})
    lines = [
        "Aegis Ingest Policy Readiness",
        f"artifact: {path}",
        f"passed: {'yes' if passed else 'no'}",
    ]
    for scenario_name in ("low_confidence_repetitive", "high_confidence_distinct"):
        scenario = scenarios.get(scenario_name, {})
        metrics = scenario.get("summary", {})
        lines.append(
            f"{scenario_name}: attempted={int(metrics.get('attempted_writes', 0))}, "
            f"accepted={int(metrics.get('accepted_writes', 0))}, "
            f"rejected={int(metrics.get('rejected_or_noop_writes', 0))}, "
            f"reconciled={'yes' if metrics.get('reconciled', False) else 'no'}"
        )
        lines.append(
            f"  outcomes={json.dumps(metrics.get('diagnostic_outcomes', {}), ensure_ascii=False)}"
        )
        lines.append(
            f"  blocked_reason_counts={json.dumps(metrics.get('blocked_reason_counts', {}), ensure_ascii=False)}"
        )
    if failures:
        lines.append("failures:")
        lines.extend(f"- {item}" for item in failures)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether current ingest behavior is healthy enough to close the admission branch.")
    parser.add_argument(
        "--artifact",
        type=Path,
        default=DEFAULT_ARTIFACT,
        help="Path to the ingest pressure diagnostic artifact.",
    )
    args = parser.parse_args()

    summary = load_summary(args.artifact)
    passed, failures = evaluate_readiness(summary)
    print(render_result(args.artifact, passed, failures, summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
