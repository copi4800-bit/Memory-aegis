#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


@dataclass
class LongHorizonResult:
    name: str
    horizon_days: int
    passed: bool
    details: dict[str, Any]


def age_scope_records(app, *, scope_type: str, scope_id: str, days_ago: int) -> None:
    aged_at = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    app.storage.execute(
        """
        UPDATE memories
        SET created_at = ?, updated_at = ?, archived_at = ?, last_accessed_at = COALESCE(last_accessed_at, ?)
        WHERE scope_type = ? AND scope_id = ? AND status IN ('archived', 'superseded', 'expired')
        """,
        (aged_at, aged_at, aged_at, aged_at, scope_type, scope_id),
    )
    app.storage.execute(
        """
        UPDATE memories
        SET created_at = ?, updated_at = ?, last_accessed_at = COALESCE(last_accessed_at, ?)
        WHERE scope_type = ? AND scope_id = ? AND status = 'active'
        """,
        (aged_at, aged_at, aged_at, scope_type, scope_id),
    )
    if app.storage._table_exists("evidence_events"):
        app.storage.execute(
            "UPDATE evidence_events SET created_at = ? WHERE scope_type = ? AND scope_id = ?",
            (aged_at, scope_type, scope_id),
        )
    if app.storage._table_exists("governance_events"):
        app.storage.execute(
            "UPDATE governance_events SET created_at = ? WHERE scope_type = ? AND scope_id = ?",
            (aged_at, scope_type, scope_id),
        )
    if app.storage._table_exists("memory_state_transitions"):
        app.storage.execute(
            "UPDATE memory_state_transitions SET created_at = ? WHERE memory_id IN (SELECT id FROM memories WHERE scope_type = ? AND scope_id = ?)",
            (aged_at, scope_type, scope_id),
        )


def current_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_noise(app, *, scope_id: str, count: int, confidence: float, prefix: str) -> None:
    for index in range(count):
        app.put_memory(
            f"{prefix} noise memory {index} that should fade away over long-horizon retention.",
            type="semantic",
            scope_type="agent",
            scope_id=scope_id,
            source_kind="manual",
            source_ref=f"{prefix}://noise/{index}",
            subject=f"{prefix}.noise.{index}",
            confidence=confidence,
        )


def run_survival_case(app, *, horizon_days: int, noise_count: int, scope_id: str, prefix: str) -> LongHorizonResult:
    old_fact = app.put_memory(
        "The office address is 100 First Street.",
        type="semantic",
        scope_type="agent",
        scope_id=scope_id,
        source_kind="manual",
        source_ref=f"{prefix}://old",
        subject="office.address",
        confidence=0.9,
    )
    current_fact = app.put_memory(
        "Correction: the office address is now 200 Second Street.",
        type="semantic",
        scope_type="agent",
        scope_id=scope_id,
        source_kind="manual",
        source_ref=f"{prefix}://current",
        subject="office.address",
        confidence=1.0,
        metadata={"is_winner": True, "is_correction": True},
    )
    if old_fact is not None:
        app.storage.execute(
            "UPDATE memories SET status = 'superseded', archived_at = ? WHERE id = ?",
            (current_iso(), old_fact.id),
        )

    seed_noise(app, scope_id=scope_id, count=noise_count, confidence=0.78, prefix=prefix)

    archived = app.put_memory(
        f"{prefix} archived reference that should eventually be compacted.",
        type="semantic",
        scope_type="agent",
        scope_id=scope_id,
        source_kind="manual",
        source_ref=f"{prefix}://archived",
        subject=f"{prefix}.archived.reference",
        confidence=0.7,
    )
    if archived is not None:
        app.storage.execute(
            "UPDATE memories SET status = 'archived', archived_at = ? WHERE id = ?",
            (current_iso(), archived.id),
        )

    age_scope_records(app, scope_type="agent", scope_id=scope_id, days_ago=horizon_days)
    if current_fact is not None:
        # Keep the current truth fresh so the gauntlet measures survival of the canonical winner.
        fresh_at = current_iso()
        app.storage.execute(
            "UPDATE memories SET created_at = ?, updated_at = ?, last_accessed_at = ? WHERE id = ?",
            (fresh_at, fresh_at, fresh_at, current_fact.id),
        )
        if app.storage._table_exists("evidence_events"):
            app.storage.execute(
                "UPDATE evidence_events SET created_at = ? WHERE memory_id = ?",
                (fresh_at, current_fact.id),
            )
        if app.storage._table_exists("governance_events"):
            app.storage.execute(
                "UPDATE governance_events SET created_at = ? WHERE memory_id = ?",
                (fresh_at, current_fact.id),
            )
        if app.storage._table_exists("memory_state_transitions"):
            app.storage.execute(
                "UPDATE memory_state_transitions SET created_at = ? WHERE memory_id = ?",
                (fresh_at, current_fact.id),
            )

    before = app.storage.storage_footprint()
    state_before = app.storage.summarize_memory_states(scope_type="agent", scope_id=scope_id)
    app.hygiene_engine.run_maintenance()
    compact = app.storage.compact_storage(
        archived_memory_days=30,
        superseded_memory_days=30,
        evidence_days=30,
        governance_days=30,
        replication_days=14,
        background_days=14,
        vacuum=True,
    )
    after = app.storage.storage_footprint()
    state_after = app.storage.summarize_memory_states(scope_type="agent", scope_id=scope_id)
    spotlight = app.core_showcase(
        "office address",
        scope_type="agent",
        scope_id=scope_id,
        intent="correction_lookup",
    )
    selected = spotlight.get("result", {}).get("selected_memory") if spotlight.get("result") else None
    rows_before = before["rows"].get("memories", 0)
    rows_after = after["rows"].get("memories", 0)
    deleted = compact["deleted"]
    passed = bool(
        selected == "Correction: the office address is now 200 Second Street."
        and rows_after < rows_before
        and deleted["archived_memories"] + deleted["superseded_memories"] > 0
    )
    return LongHorizonResult(
        name=f"survival_{horizon_days}d",
        horizon_days=horizon_days,
        passed=passed,
        details={
            "selected_memory": selected,
            "rows_before": rows_before,
            "rows_after": rows_after,
            "allocated_bytes_before": before["allocated_bytes"],
            "allocated_bytes_after": after["allocated_bytes"],
            "free_bytes_before": before["free_bytes"],
            "free_bytes_after": after["free_bytes"],
            "deleted": deleted,
            "state_before": state_before["state_counts"],
            "state_after": state_after["state_counts"],
        },
    )


def write_artifact(repo_root: Path, results: list[LongHorizonResult]) -> Path:
    artifact_path = repo_root / ".planning" / "benchmarks" / "long_horizon_survival_summary.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": "long_horizon_memory_survival",
        "summary": {
            "scenario_count": len(results),
            "pass_rate": round(sum(1 for item in results if item.passed) / len(results), 3),
            "passed": all(item.passed for item in results),
        },
        "scenarios": [
            {
                "name": item.name,
                "horizon_days": item.horizon_days,
                "passed": item.passed,
                "details": item.details,
            }
            for item in results
        ],
    }
    artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact_path


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="aegis_long_horizon_") as tmp:
        db_path = str(Path(tmp) / "long_horizon.db")
        app = AegisApp(db_path)
        try:
            results = [
                run_survival_case(app, horizon_days=90, noise_count=40, scope_id="long_horizon_90d", prefix="lh90"),
                run_survival_case(app, horizon_days=365, noise_count=120, scope_id="long_horizon_365d", prefix="lh365"),
            ]
        finally:
            app.close()

    print("## Aegis Long-Horizon Memory Survival")
    print()
    for item in results:
        print(f"- {item.name}: {'PASS' if item.passed else 'FAIL'}")
        print(json.dumps(item.details, indent=2, ensure_ascii=False))
    print()
    artifact_path = write_artifact(repo_root, results)
    print(f"[Artifact] Wrote {artifact_path}")
    return 0 if all(item.passed for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
