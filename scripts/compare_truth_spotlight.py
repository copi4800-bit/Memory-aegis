#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


def load_artifact(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_delta(before: float, after: float) -> str:
    delta = round(after - before, 3)
    if delta > 0:
        return f"improved by +{delta}"
    if delta < 0:
        return f"regressed by {delta}"
    return "unchanged"


def compare_scenarios(before: dict, after: dict) -> list[str]:
    before_map = {item["name"]: item for item in before.get("scenarios", [])}
    after_map = {item["name"]: item for item in after.get("scenarios", [])}
    lines: list[str] = []

    for name in sorted(set(before_map) | set(after_map)):
        old = before_map.get(name)
        new = after_map.get(name)
        if old is None:
            lines.append(f"- {name}: new scenario added")
            continue
        if new is None:
            lines.append(f"- {name}: scenario removed")
            continue
        if old["passed"] != new["passed"]:
            state = "PASS" if new["passed"] else "FAIL"
            lines.append(f"- {name}: changed status to {state}")
            continue
        if old.get("selected_id") != new.get("selected_id"):
            lines.append(
                f"- {name}: selected_id changed from {old.get('selected_id')} to {new.get('selected_id')}"
            )
            continue
        lines.append(f"- {name}: unchanged")
    return lines


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    repo_root = resolve_repo_root()
    default_current = repo_root / ".planning" / "benchmarks" / "truth_spotlight_summary.json"

    parser = argparse.ArgumentParser(description="Compare two Aegis truth spotlight benchmark artifacts")
    parser.add_argument("before", help="Path to the earlier artifact JSON")
    parser.add_argument(
        "after",
        nargs="?",
        default=str(default_current),
        help="Path to the later artifact JSON. Defaults to the latest truth_spotlight_summary.json",
    )
    args = parser.parse_args()

    before_path = Path(args.before)
    after_path = Path(args.after)
    before = load_artifact(before_path)
    after = load_artifact(after_path)

    before_summary = before.get("summary", {})
    after_summary = after.get("summary", {})

    print("## Aegis Truth Spotlight Comparison")
    print()
    print(f"Before: {before_path}")
    print(f"After:  {after_path}")
    print()
    print("[Metric Changes]")
    for metric in [
        "current_truth_top1_rate",
        "superseded_visibility_rate",
        "suppressed_visibility_rate",
    ]:
        old = float(before_summary.get(metric, 0.0))
        new = float(after_summary.get(metric, 0.0))
        print(f"- {metric}: {old} -> {new} ({metric_delta(old, new)})")

    print()
    print("[Scenario Changes]")
    for line in compare_scenarios(before, after):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
