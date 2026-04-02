#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


@dataclass
class TruthScenarioResult:
    name: str
    category: str
    passed: bool
    selected_id: str | None
    expected_id: str | None
    superseded_visible: bool
    notes: list[str]


SCENARIO_CATALOG = {
    "correction_current_truth": {
        "category": "correction",
        "title": "Correction keeps current fact on top",
        "intent": "correction_lookup",
        "description": "A corrected fact should beat the older superseded fact and keep the stale fact visible in why-not.",
    },
    "conflict_winner_selection": {
        "category": "conflict",
        "title": "Conflict winner holds under evidence pressure",
        "intent": "correction_lookup",
        "description": "When two facts conflict, the stronger governed winner should remain selected.",
    },
    "lexical_trap_resistance": {
        "category": "lexical_resilience",
        "title": "Trusted truth beats flashy lexical bait",
        "intent": "correction_lookup",
        "description": "A low-trust but lexically flashy memory should not outrank the trusted winner.",
    },
    "user_override_priority": {
        "category": "override",
        "title": "User override stays active",
        "intent": "user_override_active",
        "description": "An explicit override should stay selected under the override intent path.",
    },
}


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.memory.core import MemoryManager
    from aegis_py.retrieval.search import SearchPipeline
    from aegis_py.spotlight_surface import build_spotlight_payload
    from aegis_py.storage.manager import StorageManager

    with tempfile.TemporaryDirectory(prefix="aegis_truth_benchmark_") as tmp:
        db_path = str(Path(tmp) / "truth_spotlight.db")
        storage = StorageManager(db_path)
        manager = MemoryManager(storage)
        pipeline = SearchPipeline(storage)

        try:
            results = [
                run_correction_truth_case(manager, pipeline, storage, build_spotlight_payload),
                run_conflict_truth_case(manager, pipeline, storage, build_spotlight_payload),
                run_lexical_trap_truth_case(manager, pipeline, storage, build_spotlight_payload),
                run_user_override_case(manager, pipeline, storage, build_spotlight_payload),
            ]
        finally:
            storage.close()

    current_truth_top1_rate = sum(1 for item in results if item.passed) / len(results)
    superseded_visibility_rate = sum(1 for item in results if item.superseded_visible) / len(results)
    suppressed_visibility_rate = sum(1 for item in results if item.notes) / len(results)
    summary = {
        "current_truth_top1_rate": round(current_truth_top1_rate, 3),
        "superseded_visibility_rate": round(superseded_visibility_rate, 3),
        "suppressed_visibility_rate": round(suppressed_visibility_rate, 3),
        "passed": all(item.passed for item in results),
    }
    grouped_summary = build_grouped_summary(results)

    print("## Aegis Truth Spotlight Benchmark")
    print()
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        print(f"- {item.name}: {status}")
        print(
            json.dumps(
                {
                    "selected_id": item.selected_id,
                    "expected_id": item.expected_id,
                    "superseded_visible": item.superseded_visible,
                    "notes": item.notes,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    print()
    print("[Summary]")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print()
    print("[Grouped Summary]")
    print(json.dumps(grouped_summary, indent=2, ensure_ascii=False))

    write_summary_artifact(repo_root, results, summary, grouped_summary)

    return 0 if summary["passed"] else 1


def sync_fts(storage) -> None:
    storage.execute("DELETE FROM memories_fts")
    storage.execute(
        "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
    )


def run_correction_truth_case(manager, pipeline, storage, build_spotlight_payload) -> TruthScenarioResult:
    old_fact = Memory(
        id="bench_old_fact",
        type="semantic",
        content="The release date is April 10.",
        subject="release_date",
        confidence=0.9,
        source_kind="manual",
        source_ref="bench://old",
        scope_type="agent",
        scope_id="truth_bench_correction",
    )
    current_fact = Memory(
        id="bench_current_fact",
        type="semantic",
        content="Correction: the release date moved to April 24.",
        subject="release_date",
        confidence=1.0,
        source_kind="manual",
        source_ref="bench://current",
        scope_type="agent",
        scope_id="truth_bench_correction",
        metadata={
            "is_winner": True,
            "is_correction": True,
            "corrected_from": ["bench_old_fact"],
        },
    )
    manager.store(old_fact)
    manager.store(current_fact)
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = 'bench_old_fact'")
    sync_fts(storage)

    query = SearchQuery(
        query="release date",
        scope_type="agent",
        scope_id="truth_bench_correction",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = pipeline.search(query)

    top = results[0] if results else None
    spotlight = build_spotlight_payload(top) if top else None
    suppressed_ids = {item["id"] for item in spotlight["why_not"]} if spotlight else set()

    return TruthScenarioResult(
        name="correction_current_truth",
        category="correction",
        passed=bool(top and top.memory.id == "bench_current_fact"),
        selected_id=top.memory.id if top else None,
        expected_id="bench_current_fact",
        superseded_visible="bench_old_fact" in suppressed_ids,
        notes=[item["reason"] for item in spotlight["why_not"]] if spotlight else ["No results returned"],
    )


def run_conflict_truth_case(manager, pipeline, storage, build_spotlight_payload) -> TruthScenarioResult:
    low_confidence = Memory(
        id="bench_conflict_low",
        type="semantic",
        content="The office is in Hanoi.",
        subject="office_location",
        confidence=0.7,
        source_kind="manual",
        source_ref="bench://low",
        scope_type="agent",
        scope_id="truth_bench_conflict",
    )
    winner = Memory(
        id="bench_conflict_winner",
        type="semantic",
        content="The office moved to Saigon.",
        subject="office_location",
        confidence=0.95,
        source_kind="manual",
        source_ref="bench://winner",
        scope_type="agent",
        scope_id="truth_bench_conflict",
        metadata={"is_winner": True},
    )
    manager.store(low_confidence)
    manager.store(winner)
    for index in range(5):
        storage.execute(
            """
            INSERT INTO evidence_events (
                id, scope_type, scope_id, memory_id, source_kind, source_ref, raw_content, created_at
            ) VALUES (?, 'agent', 'truth_bench_conflict', 'bench_conflict_winner', 'manual', 'bench://winner', 'Confirmed', '2026-04-02T00:00:00+00:00')
            """,
            (f"bench_conflict_event_{index}",),
        )
    sync_fts(storage)

    query = SearchQuery(
        query="office",
        scope_type="agent",
        scope_id="truth_bench_conflict",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = pipeline.search(query)

    top = results[0] if results else None
    spotlight = build_spotlight_payload(top) if top else None
    suppressed_ids = {item["id"] for item in spotlight["why_not"]} if spotlight else set()

    return TruthScenarioResult(
        name="conflict_winner_selection",
        category="conflict",
        passed=bool(top and top.memory.id == "bench_conflict_winner"),
        selected_id=top.memory.id if top else None,
        expected_id="bench_conflict_winner",
        superseded_visible="bench_conflict_low" in suppressed_ids,
        notes=[item["reason"] for item in spotlight["why_not"]] if spotlight else ["No results returned"],
    )


def run_lexical_trap_truth_case(manager, pipeline, storage, build_spotlight_payload) -> TruthScenarioResult:
    flashy = Memory(
        id="bench_lexical_flashy",
        type="semantic",
        content="Launch date launch date launch date April 10 launch date.",
        subject="launch_schedule",
        confidence=0.25,
        source_kind="manual",
        source_ref="bench://flashy",
        scope_type="agent",
        scope_id="truth_bench_lexical",
    )
    trusted = Memory(
        id="bench_lexical_trusted",
        type="semantic",
        content="The release schedule confirms April 24 as the launch date.",
        subject="launch_schedule",
        confidence=0.95,
        source_kind="manual",
        source_ref="bench://trusted",
        scope_type="agent",
        scope_id="truth_bench_lexical",
        metadata={"is_winner": True},
    )
    manager.store(flashy)
    manager.store(trusted)
    for index in range(4):
        storage.execute(
            """
            INSERT INTO evidence_events (
                id, scope_type, scope_id, memory_id, source_kind, source_ref, raw_content, created_at
            ) VALUES (?, 'agent', 'truth_bench_lexical', 'bench_lexical_trusted', 'manual', 'bench://trusted', 'Verified release schedule', '2026-04-02T00:00:00+00:00')
            """,
            (f"bench_lexical_event_{index}",),
        )
    sync_fts(storage)

    query = SearchQuery(
        query="launch date",
        scope_type="agent",
        scope_id="truth_bench_lexical",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    results = pipeline.search(query)

    top = results[0] if results else None
    spotlight = build_spotlight_payload(top) if top else None
    suppressed_ids = {item["id"] for item in spotlight["why_not"]} if spotlight else set()

    return TruthScenarioResult(
        name="lexical_trap_resistance",
        category="lexical_resilience",
        passed=bool(top and top.memory.id == "bench_lexical_trusted"),
        selected_id=top.memory.id if top else None,
        expected_id="bench_lexical_trusted",
        superseded_visible="bench_lexical_flashy" in suppressed_ids,
        notes=[item["reason"] for item in spotlight["why_not"]] if spotlight else ["No results returned"],
    )


def run_user_override_case(manager, pipeline, storage, build_spotlight_payload) -> TruthScenarioResult:
    preference = Memory(
        id="bench_override_pref",
        type="semantic",
        content="Use the nickname Hali in replies.",
        subject="user_nickname",
        confidence=0.5,
        source_kind="manual",
        source_ref="bench://override",
        scope_type="agent",
        scope_id="truth_bench_override",
        metadata={"is_winner": True},
    )
    manager.store(preference)
    sync_fts(storage)

    query = SearchQuery(
        query="nickname",
        scope_type="agent",
        scope_id="truth_bench_override",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "user_override_active")
    results = pipeline.search(query)

    top = results[0] if results else None
    spotlight = build_spotlight_payload(top) if top else None

    passed = bool(
        top
        and top.memory.id == "bench_override_pref"
        and spotlight
        and spotlight["truth_state"]["governance_status"] == "active"
    )

    return TruthScenarioResult(
        name="user_override_priority",
        category="override",
        passed=passed,
        selected_id=top.memory.id if top else None,
        expected_id="bench_override_pref",
        superseded_visible=False,
        notes=spotlight["truth_state"]["policy_trace"] if spotlight else ["No results returned"],
    )


def build_grouped_summary(results: list[TruthScenarioResult]) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, list[TruthScenarioResult]] = {}
    for item in results:
        grouped.setdefault(item.category, []).append(item)
    summary: dict[str, dict[str, float | int]] = {}
    for category, items in grouped.items():
        total = len(items)
        summary[category] = {
            "scenario_count": total,
            "pass_rate": round(sum(1 for item in items if item.passed) / total, 3),
            "superseded_visibility_rate": round(sum(1 for item in items if item.superseded_visible) / total, 3),
            "suppressed_visibility_rate": round(sum(1 for item in items if item.notes) / total, 3),
        }
    return summary


def write_summary_artifact(
    repo_root: Path,
    results: list[TruthScenarioResult],
    summary: dict[str, object],
    grouped_summary: dict[str, object],
) -> None:
    artifact_dir = repo_root / ".planning" / "benchmarks"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "truth_spotlight_summary.json"
    payload = {
        "benchmark": "truth_spotlight",
        "summary": summary,
        "grouped_summary": grouped_summary,
        "scenario_catalog": SCENARIO_CATALOG,
        "scenarios": [
            {
                "name": item.name,
                "category": item.category,
                "passed": item.passed,
                "selected_id": item.selected_id,
                "expected_id": item.expected_id,
                "superseded_visible": item.superseded_visible,
                "notes": item.notes,
            }
            for item in results
        ],
    }
    artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print(f"[Artifact] Wrote {artifact_path}")


if __name__ == "__main__":
    raise SystemExit(main())
