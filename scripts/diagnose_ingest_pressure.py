#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


def write_artifact(repo_root: Path, payload: dict[str, object]) -> Path:
    artifact_dir = repo_root / ".planning" / "benchmarks"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "ingest_pressure_diagnostic.json"
    artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact_path


def _run_attempts(app, attempts: list[dict[str, Any]], canonical_payload: dict[str, Any]) -> dict[str, Any]:
    accepted = 0
    rejected = 0
    outcome_counts: dict[str, int] = {}
    blocked_reason_counts: dict[str, int] = {}
    reconciliation_failures: list[dict[str, object]] = []
    attempt_records: list[dict[str, object]] = []

    for index, payload in enumerate(attempts):
        diagnostic = app.diagnose_ingest_attempt(**payload)
        stored = app.put_memory(**payload)

        actual_outcome = "accepted" if stored is not None else "no_op"
        if stored is not None:
            accepted += 1
        else:
            rejected += 1

        outcome = str(diagnostic["outcome"])
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        for reason in diagnostic.get("reasons", []):
            if isinstance(reason, str) and reason.startswith("blocked_"):
                blocked_reason_counts[reason] = blocked_reason_counts.get(reason, 0) + 1

        expected_actual = "accepted" if outcome in {"admit", "exact_dedup"} else "no_op"
        reconciled = expected_actual == actual_outcome
        if not reconciled:
            reconciliation_failures.append(
                {
                    "index": index,
                    "diagnostic_outcome": outcome,
                    "actual_outcome": actual_outcome,
                    "reason_code": diagnostic.get("reason_code"),
                }
            )
        attempt_records.append(
            {
                "index": index,
                "content": payload["content"],
                "confidence": payload.get("confidence"),
                "diagnostic_outcome": outcome,
                "reason_code": diagnostic.get("reason_code"),
                "actual_outcome": actual_outcome,
                "reconciled": reconciled,
            }
        )

    canonical = app.put_memory(**canonical_payload)
    spotlight = app.spotlight(
        canonical_payload["subject"].replace(".", " "),
        scope_type=canonical_payload["scope_type"],
        scope_id=canonical_payload["scope_id"],
        limit=1,
        intent="correction_lookup",
    )
    selected = spotlight.get("results", [{}])[0].get("selected_memory") if spotlight.get("result_count") else None

    return {
        "summary": {
            "attempted_writes": len(attempts),
            "accepted_writes": accepted,
            "rejected_or_noop_writes": rejected,
            "diagnostic_outcomes": outcome_counts,
            "blocked_reason_counts": blocked_reason_counts,
            "reconciled": not reconciliation_failures,
            "selected_memory": selected,
            "canonical_admitted": canonical is not None,
        },
        "attempts": attempt_records,
        "reconciliation_failures": reconciliation_failures,
    }


def build_low_confidence_repetitive_payloads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    attempts = []
    for index in range(30):
        attempts.append(
            {
                "content": f"Repeated ingest payload {index % 3} for admission pressure.",
                "type": "semantic",
                "scope_type": "agent",
                "scope_id": "gauntlet_ingest_diagnostic_low",
                "source_kind": "manual",
                "source_ref": f"diag://ingest/low/{index}",
                "subject": "ingest.pressure",
                "confidence": 0.4 + (index % 3) * 0.1,
            }
        )
    canonical = {
        "content": "Canonical ingest checkpoint is ACCEPTABLE.",
        "type": "semantic",
        "scope_type": "agent",
        "scope_id": "gauntlet_ingest_diagnostic_low",
        "source_kind": "manual",
        "source_ref": "diag://ingest/low/canonical",
        "subject": "ingest.checkpoint",
        "confidence": 0.95,
        "metadata": {"is_winner": True},
    }
    return attempts, canonical


def build_high_confidence_distinct_payloads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    attempts = []
    for index in range(12):
        attempts.append(
            {
                "content": f"Confirmed project checkpoint {index} is stable and verified.",
                "type": "semantic",
                "scope_type": "agent",
                "scope_id": "gauntlet_ingest_diagnostic_high",
                "source_kind": "manual",
                "source_ref": f"diag://ingest/high/{index}",
                "subject": f"checkpoint.{index}",
                "confidence": 0.95,
            }
        )
    canonical = {
        "content": "Canonical high-confidence checkpoint is GREEN.",
        "type": "semantic",
        "scope_type": "agent",
        "scope_id": "gauntlet_ingest_diagnostic_high",
        "source_kind": "manual",
        "source_ref": "diag://ingest/high/canonical",
        "subject": "checkpoint.canonical",
        "confidence": 0.98,
        "metadata": {"is_winner": True},
    }
    return attempts, canonical


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="aegis_ingest_diagnostic_") as tmp:
        db_path = str(Path(tmp) / "ingest_diagnostic.db")
        app = AegisApp(db_path)
        try:
            low_attempts, low_canonical = build_low_confidence_repetitive_payloads()
            high_attempts, high_canonical = build_high_confidence_distinct_payloads()
            low_summary = _run_attempts(app, low_attempts, low_canonical)
            high_summary = _run_attempts(app, high_attempts, high_canonical)
        finally:
            app.close()

    payload = {
        "diagnostic": "ingest_pressure",
        "scenario_catalog": {
            "low_confidence_repetitive": "Repeated low-confidence writes should mostly resolve into low-confidence blocks plus exact deduplication.",
            "high_confidence_distinct": "Distinct high-confidence writes should admit cleanly without policy blocks.",
        },
        "scenarios": {
            "low_confidence_repetitive": low_summary,
            "high_confidence_distinct": high_summary,
        },
    }
    artifact_path = write_artifact(repo_root, payload)

    print("## Aegis Ingest Pressure Diagnostic")
    print()
    for name, scenario in payload["scenarios"].items():
        print(f"[{name}]")
        print(json.dumps(scenario["summary"], indent=2, ensure_ascii=False))
        print()
    print(f"[Artifact] Wrote {artifact_path}")
    low_ok = payload["scenarios"]["low_confidence_repetitive"]["summary"]["reconciled"]
    high_ok = payload["scenarios"]["high_confidence_distinct"]["summary"]["reconciled"]
    return 0 if low_ok and high_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
