#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import random
import shutil
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aegis_py.app import AegisApp
from aegis_py.conflict.core import ConflictManager


logging.getLogger("aegis.runtime.observability").handlers.clear()
logging.getLogger("aegis.runtime.observability").propagate = False
logging.getLogger("aegis.runtime.observability").setLevel(logging.CRITICAL)


@dataclass(frozen=True)
class StressProfile:
    seed_count: int
    scope_count: int
    conflict_every: int
    evidence_every: int
    transition_candidates: int
    feedback_cycles: int
    retrieval_queries: int
    read_pressure_queries: int
    reader_threads: int
    surface_cycles: int
    maintenance_cycles: int
    backup_cycles: int


PROFILES: dict[str, StressProfile] = {
    "smoke": StressProfile(
        seed_count=400,
        scope_count=4,
        conflict_every=11,
        evidence_every=3,
        transition_candidates=80,
        feedback_cycles=40,
        retrieval_queries=120,
        read_pressure_queries=240,
        reader_threads=4,
        surface_cycles=18,
        maintenance_cycles=2,
        backup_cycles=1,
    ),
    "extreme": StressProfile(
        seed_count=12000,
        scope_count=10,
        conflict_every=9,
        evidence_every=3,
        transition_candidates=600,
        feedback_cycles=500,
        retrieval_queries=2500,
        read_pressure_queries=6000,
        reader_threads=8,
        surface_cycles=120,
        maintenance_cycles=6,
        backup_cycles=2,
    ),
    "apocalypse": StressProfile(
        seed_count=30000,
        scope_count=18,
        conflict_every=7,
        evidence_every=2,
        transition_candidates=1800,
        feedback_cycles=1200,
        retrieval_queries=6000,
        read_pressure_queries=18000,
        reader_threads=16,
        surface_cycles=240,
        maintenance_cycles=12,
        backup_cycles=4,
    ),
    "blackhole": StressProfile(
        seed_count=60000,
        scope_count=28,
        conflict_every=5,
        evidence_every=2,
        transition_candidates=3600,
        feedback_cycles=2400,
        retrieval_queries=12000,
        read_pressure_queries=36000,
        reader_threads=24,
        surface_cycles=420,
        maintenance_cycles=20,
        backup_cycles=6,
    ),
}


def now_slug() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
    return ordered[index]


def summarize_latencies(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "min_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "mean_ms": 0.0}
    return {
        "count": len(values),
        "min_ms": round(min(values), 3),
        "p50_ms": round(percentile(values, 0.50), 3),
        "p95_ms": round(percentile(values, 0.95), 3),
        "max_ms": round(max(values), 3),
        "mean_ms": round(statistics.fmean(values), 3),
    }


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def make_scopes(scope_count: int) -> list[tuple[str, str]]:
    return [("project", f"V8_STRESS_{index:03d}") for index in range(scope_count)]


def canary_value(index: int) -> str:
    return f"v8-canary-{index:06d}-{(index * 37) % 997:03d}"


def build_memory_content(index: int, canary: str, topic: str, lane: int) -> str:
    return (
        f"V8 stress seed {index}. Topic {topic}. Canary {canary}. "
        f"Lane {lane}. Release token R{index % 97}. "
        f"Operator protocol requires evidence-backed handling for subject family {topic}."
    )


def coerce_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def remember_seed_corpus(
    app: AegisApp,
    scopes: list[tuple[str, str]],
    profile: StressProfile,
    *,
    rng: random.Random,
) -> dict[str, Any]:
    latencies: list[float] = []
    canaries: list[dict[str, str]] = []
    transition_candidates: list[str] = []
    subject_pool = [f"stress.subject.{idx:03d}" for idx in range(max(120, profile.scope_count * 10))]
    type_counts: dict[str, int] = {"semantic": 0, "episodic": 0, "working": 0, "procedural": 0}
    conflict_records = 0
    evidence_events = 0

    for index in range(profile.seed_count):
        scope_type, scope_id = scopes[index % len(scopes)]
        subject = subject_pool[index % len(subject_pool)]
        lane = index % 11
        canary = canary_value(index)
        memory_type = rng.choices(
            ["semantic", "episodic", "working", "procedural"],
            weights=[45, 20, 15, 20],
            k=1,
        )[0]
        content = build_memory_content(index, canary, subject, lane)
        started = time.perf_counter()
        stored = app.put_memory(
            content,
            type=memory_type,
            scope_type=scope_type,
            scope_id=scope_id,
            source_kind="manual" if index % 2 == 0 else "message",
            source_ref=f"stress://seed/{index}",
            subject=subject,
        )
        latencies.append((time.perf_counter() - started) * 1000.0)
        if stored is None:
            raise RuntimeError(f"seed ingestion failed at index {index}")
        type_counts[memory_type] += 1
        canaries.append(
            {
                "scope_type": scope_type,
                "scope_id": scope_id,
                "query": canary,
                "memory_id": stored.id,
                "subject": subject,
            }
        )

        if len(transition_candidates) < profile.transition_candidates:
            transition_candidates.append(stored.id)

        if index % profile.evidence_every == 0:
            app.storage.create_evidence_event(
                scope_type=scope_type,
                scope_id=scope_id,
                memory_id=stored.id,
                source_kind="manual",
                source_ref=f"stress://evidence/{index}",
                raw_content=f"Independent evidence confirms {canary} for {subject}.",
                metadata={"capture_stage": "v8_apocalypse_seed"},
            )
            evidence_events += 1

        if index % profile.conflict_every == 0:
            started = time.perf_counter()
            challenger = app.put_memory(
                (
                    f"V8 contradiction {index}. Topic {subject}. Canary {canary}. "
                    f"Operator protocol is NOT approved for lane {lane} under rollback."
                ),
                type="semantic",
                scope_type=scope_type,
                scope_id=scope_id,
                source_kind="message",
                source_ref=f"stress://conflict/{index}",
                subject=subject,
            )
            latencies.append((time.perf_counter() - started) * 1000.0)
            if challenger is None:
                raise RuntimeError(f"conflict ingestion failed at index {index}")
            conflict_records += 1

    return {
        "latency_ms": summarize_latencies(latencies),
        "type_counts": type_counts,
        "conflict_records": conflict_records,
        "evidence_events": evidence_events,
        "total_records_written": profile.seed_count + conflict_records,
        "canaries": canaries,
        "transition_candidates": transition_candidates,
    }


def amplify_v8_state(
    app: AegisApp,
    canaries: list[dict[str, str]],
    *,
    rng: random.Random,
) -> dict[str, Any]:
    scanned_subjects: set[tuple[str, str, str]] = set()
    promoted_drafts = 0
    prepared_demotions = 0
    warmed_usage = 0
    feedback_events = 0

    for index, case in enumerate(canaries):
        memory = app.storage.get_memory(case["memory_id"])
        if memory is None:
            continue
        metadata = dict(memory.metadata)

        if index % 8 == 0:
            app.storage.execute(
                "UPDATE memories SET access_count = ?, activation_score = ? WHERE id = ?",
                (rng.randint(6, 14), round(rng.uniform(1.8, 3.1), 3), case["memory_id"]),
            )
            warmed_usage += 1

        if index % 21 == 0:
            metadata["memory_state"] = "draft"
            metadata["admission_state"] = "draft"
            app.storage.execute(
                "UPDATE memories SET metadata_json = ?, access_count = ?, activation_score = ? WHERE id = ?",
                (json.dumps(metadata, ensure_ascii=True), rng.randint(8, 15), 2.6, case["memory_id"]),
            )
            promoted_drafts += 1

        if index % 17 == 0:
            app.apply_v8_outcome_feedback(
                case["memory_id"],
                success_score=1.0,
                relevance_score=1.0,
                override_score=0.0,
                actor="v8_apocalypse_seed_feedback",
            )
            feedback_events += 1

        if index % 19 == 0:
            app.apply_v8_outcome_feedback(
                case["memory_id"],
                success_score=0.15,
                relevance_score=0.2,
                override_score=0.85,
                actor="v8_apocalypse_seed_penalty",
            )
            feedback_events += 1

        subject_key = (case["scope_type"], case["scope_id"], case["subject"])
        if subject_key not in scanned_subjects and index % 5 == 0:
            ConflictManager(app.storage).scan_conflicts(case["subject"])
            scanned_subjects.add(subject_key)

    demotion_pool = [case for idx, case in enumerate(canaries) if idx % 23 == 0][: max(32, len(canaries) // 40)]
    for case in demotion_pool:
        memory = app.storage.get_memory(case["memory_id"])
        if memory is None:
            continue
        metadata = dict(memory.metadata)
        metadata["memory_state"] = "validated"
        metadata["admission_state"] = "validated"
        app.storage.execute(
            "UPDATE memories SET metadata_json = ?, access_count = ?, activation_score = ?, confidence = ? WHERE id = ?",
            (json.dumps(metadata, ensure_ascii=True), 0, 1.0, 0.22, case["memory_id"]),
        )
        app.storage.execute("DELETE FROM evidence_events WHERE memory_id = ?", (case["memory_id"],))
        prepared_demotions += 1

    return {
        "scanned_subjects": len(scanned_subjects),
        "warmed_usage_records": warmed_usage,
        "prepared_draft_promotions": promoted_drafts,
        "prepared_demotions": prepared_demotions,
        "seed_feedback_events": feedback_events,
    }


def run_retrieval_storm(
    app: AegisApp,
    canaries: list[dict[str, str]],
    query_count: int,
    *,
    rng: random.Random,
) -> dict[str, Any]:
    latencies: list[float] = []
    hits = 0
    dynamic_reason_hits = 0
    signal_coverage = 0

    for _ in range(query_count):
        case = rng.choice(canaries)
        started = time.perf_counter()
        results = app.search(
            case["query"],
            scope_type=case["scope_type"],
            scope_id=case["scope_id"],
            limit=5,
            fallback_to_or=True,
        )
        latencies.append((time.perf_counter() - started) * 1000.0)
        if results and results[0].v8_core_signals is not None:
            signal_coverage += 1
        if any(result.memory.id == case["memory_id"] for result in results):
            hits += 1
        if results and any(reason.startswith("v8_") for reason in results[0].reasons):
            dynamic_reason_hits += 1

    return {
        "queries": query_count,
        "hit_rate": round(hits / query_count, 4) if query_count else 0.0,
        "dynamic_reason_rate": round(dynamic_reason_hits / query_count, 4) if query_count else 0.0,
        "signal_coverage_rate": round(signal_coverage / query_count, 4) if query_count else 0.0,
        "latency_ms": summarize_latencies(latencies),
    }


def _read_worker(db_path: str, jobs: list[dict[str, str]]) -> dict[str, Any]:
    app = AegisApp(db_path=db_path)
    latencies: list[float] = []
    hits = 0
    errors = 0
    snapshots = 0
    try:
        for index, job in enumerate(jobs):
            started = time.perf_counter()
            try:
                results = app.search(
                    job["query"],
                    scope_type=job["scope_type"],
                    scope_id=job["scope_id"],
                    limit=5,
                    fallback_to_or=True,
                )
                latencies.append((time.perf_counter() - started) * 1000.0)
                if any(item.memory.id == job["memory_id"] for item in results):
                    hits += 1
                if index % 17 == 0:
                    app.v8_bundle_snapshot(
                        query=job["query"],
                        scope_type=job["scope_type"],
                        scope_id=job["scope_id"],
                        limit=5,
                    )
                    snapshots += 1
            except Exception:
                errors += 1
    finally:
        app.close()
    return {
        "latencies": latencies,
        "hits": hits,
        "errors": errors,
        "queries": len(jobs),
        "snapshots": snapshots,
    }


def run_concurrent_read_pressure(
    db_path: str,
    canaries: list[dict[str, str]],
    query_count: int,
    reader_threads: int,
    *,
    rng: random.Random,
) -> dict[str, Any]:
    jobs = [rng.choice(canaries) for _ in range(query_count)]
    buckets: list[list[dict[str, str]]] = [[] for _ in range(reader_threads)]
    for index, job in enumerate(jobs):
        buckets[index % reader_threads].append(job)

    all_latencies: list[float] = []
    hits = 0
    errors = 0
    snapshots = 0
    with ThreadPoolExecutor(max_workers=reader_threads) as executor:
        futures = [executor.submit(_read_worker, db_path, bucket) for bucket in buckets if bucket]
        for future in as_completed(futures):
            payload = future.result()
            all_latencies.extend(payload["latencies"])
            hits += payload["hits"]
            errors += payload["errors"]
            snapshots += payload["snapshots"]
    return {
        "threads": reader_threads,
        "queries": query_count,
        "hit_rate": round(hits / query_count, 4) if query_count else 0.0,
        "errors": errors,
        "bundle_snapshots": snapshots,
        "latency_ms": summarize_latencies(all_latencies),
    }


def run_transition_storm(app: AegisApp, memory_ids: list[str], *, rng: random.Random) -> dict[str, Any]:
    evaluate_latencies: list[float] = []
    apply_latencies: list[float] = []
    actions = {"promote": 0, "demote": 0, "hold": 0}
    applied = 0
    errors = 0

    for memory_id in memory_ids:
        started = time.perf_counter()
        try:
            gate = app.v8_transition_gate(memory_id)
            evaluate_latencies.append((time.perf_counter() - started) * 1000.0)
            action = gate["transition_operator"]["decision"]["recommended_action"]
            actions[action] = actions.get(action, 0) + 1
            if action != "hold" or rng.random() < 0.15:
                started = time.perf_counter()
                result = app.apply_v8_transition_gate(memory_id, actor="v8_apocalypse_transition")
                apply_latencies.append((time.perf_counter() - started) * 1000.0)
                if result.get("applied"):
                    applied += 1
        except Exception:
            errors += 1

    return {
        "candidates": len(memory_ids),
        "applied": applied,
        "actions": actions,
        "errors": errors,
        "evaluate_latency_ms": summarize_latencies(evaluate_latencies),
        "apply_latency_ms": summarize_latencies(apply_latencies),
    }


def run_feedback_storm(
    app: AegisApp,
    canaries: list[dict[str, str]],
    cycles: int,
    *,
    rng: random.Random,
) -> dict[str, Any]:
    latencies: list[float] = []
    applied = 0
    no_result = 0
    objective_regressions: list[float] = []
    energy_deltas: list[float] = []

    for index in range(cycles):
        case = rng.choice(canaries)
        results = app.search(
            case["query"],
            scope_type=case["scope_type"],
            scope_id=case["scope_id"],
            limit=5,
            fallback_to_or=True,
        )
        selected = [results[0].memory.id] if results else []
        overrides = [results[-1].memory.id] if len(results) > 1 and index % 2 == 0 else []
        success_score = 1.0 if index % 3 else 0.35
        started = time.perf_counter()
        payload = app.apply_v8_retrieval_feedback(
            query=case["query"],
            scope_type=case["scope_type"],
            scope_id=case["scope_id"],
            selected_memory_ids=selected,
            override_memory_ids=overrides,
            success_score=success_score,
            limit=5,
            include_global=True,
            actor="v8_apocalypse_feedback",
        )
        latencies.append((time.perf_counter() - started) * 1000.0)
        if payload.get("applied"):
            applied += 1
            before = payload["before_snapshot"]
            after = payload["after_snapshot"]
            objective_regressions.append(max(0.0, float(after["objective"]) - float(before["objective"])))
            energy_deltas.append(float(after["energy"]) - float(before["energy"]))
        else:
            no_result += 1

    return {
        "cycles": cycles,
        "applied": applied,
        "no_result": no_result,
        "objective_regression_mean": round(statistics.fmean(objective_regressions), 6) if objective_regressions else 0.0,
        "energy_delta_mean": round(statistics.fmean(energy_deltas), 6) if energy_deltas else 0.0,
        "latency_ms": summarize_latencies(latencies),
    }


def run_surface_pressure(
    app: AegisApp,
    scopes: list[tuple[str, str]],
    cycles: int,
    *,
    rng: random.Random,
) -> dict[str, Any]:
    field_latencies: list[float] = []
    context_latencies: list[float] = []
    governance_latencies: list[float] = []
    evidence_latencies: list[float] = []
    energy_samples: list[float] = []
    objective_samples: list[float] = []
    evidence_artifact_count = 0

    for index in range(cycles):
        scope_type, scope_id = scopes[index % len(scopes)]
        query = f"stress subject {index % 17}"

        started = time.perf_counter()
        snapshot = app.v8_field_snapshot(scope_type=scope_type, scope_id=scope_id)
        field_latencies.append((time.perf_counter() - started) * 1000.0)
        energy_samples.append(float(snapshot["energy"]["energy"]))
        objective_samples.append(float(snapshot["energy"]["objective"]))

        started = time.perf_counter()
        app.search_context_pack(query, scope_type=scope_type, scope_id=scope_id, limit=5, semantic=True)
        context_latencies.append((time.perf_counter() - started) * 1000.0)

        if index % 5 == 0:
            started = time.perf_counter()
            app.inspect_governance(scope_type=scope_type, scope_id=scope_id, limit=25)
            governance_latencies.append((time.perf_counter() - started) * 1000.0)

            started = time.perf_counter()
            artifacts = app.evidence_artifacts(scope_type=scope_type, scope_id=scope_id)
            evidence_latencies.append((time.perf_counter() - started) * 1000.0)
            evidence_artifact_count += len(artifacts.get("artifacts", []))

    return {
        "cycles": cycles,
        "energy_mean": round(statistics.fmean(energy_samples), 6) if energy_samples else 0.0,
        "objective_mean": round(statistics.fmean(objective_samples), 6) if objective_samples else 0.0,
        "evidence_artifact_count": evidence_artifact_count,
        "field_snapshot_latency_ms": summarize_latencies(field_latencies),
        "context_pack_latency_ms": summarize_latencies(context_latencies),
        "governance_latency_ms": summarize_latencies(governance_latencies),
        "evidence_latency_ms": summarize_latencies(evidence_latencies),
    }


def run_maintenance_pressure(
    app: AegisApp,
    scopes: list[tuple[str, str]],
    cycles: int,
) -> dict[str, Any]:
    plan_latencies: list[float] = []
    rebuild_latencies: list[float] = []
    scan_latencies: list[float] = []
    compact_latencies: list[float] = []
    planned = 0
    applied = 0
    rolled_back = 0

    for index in range(cycles):
        scope_type, scope_id = scopes[index % len(scopes)]
        started = time.perf_counter()
        plan = app.plan_background_intelligence(scope_type=scope_type, scope_id=scope_id)
        plan_latencies.append((time.perf_counter() - started) * 1000.0)
        planned += int(plan.get("proposal_count", 0))

        for run in app.storage.list_background_intelligence_runs(scope_type=scope_type, scope_id=scope_id, status="planned")[:2]:
            if run["worker_kind"] == "graph_repair":
                outcome = app.apply_background_intelligence_run(run["id"], max_mutations=20)
                if outcome.get("applied"):
                    applied += 1
                    rollback = app.rollback_background_intelligence_run(run["id"])
                    if rollback.get("rolled_back"):
                        rolled_back += 1

        started = time.perf_counter()
        app.rebuild()
        rebuild_latencies.append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        app.scan()
        scan_latencies.append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        app.compact_storage(vacuum=(index % 3 == 0))
        compact_latencies.append((time.perf_counter() - started) * 1000.0)

    return {
        "cycles": cycles,
        "planned_proposals": planned,
        "applied_runs": applied,
        "rolled_back_runs": rolled_back,
        "plan_latency_ms": summarize_latencies(plan_latencies),
        "rebuild_latency_ms": summarize_latencies(rebuild_latencies),
        "scan_latency_ms": summarize_latencies(scan_latencies),
        "compact_latency_ms": summarize_latencies(compact_latencies),
    }


def run_backup_roundtrip(app: AegisApp, workspace_dir: Path, cycles: int) -> dict[str, Any]:
    restore_db = workspace_dir / "restore_target.db"
    if restore_db.exists():
        restore_db.unlink()
    restore_app = AegisApp(db_path=str(restore_db))
    latencies: list[float] = []
    created = 0
    restored = 0
    errors = 0
    try:
        for _ in range(cycles):
            started = time.perf_counter()
            try:
                payload = app.create_backup(mode="snapshot", workspace_dir=str(workspace_dir))
                created += 1
                restored_payload = restore_app.restore_backup(payload["path"])
                if restored_payload.get("restored"):
                    restored += 1
            except Exception:
                errors += 1
            latencies.append((time.perf_counter() - started) * 1000.0)
        restore_status = restore_app.status()
    finally:
        restore_app.close()

    return {
        "cycles": cycles,
        "created": created,
        "restored": restored,
        "errors": errors,
        "restore_counts": restore_status["counts"],
        "latency_ms": summarize_latencies(latencies),
    }


def evaluate_report(report: dict[str, Any]) -> dict[str, Any]:
    phases = report["phases"]
    checks = {
        "retrieval_hits_hold": phases["retrieval_storm"]["hit_rate"] >= 0.95,
        "read_pressure_no_errors": phases["concurrent_read_pressure"]["errors"] == 0,
        "transition_errors_zero": phases["transition_storm"]["errors"] == 0,
        "feedback_applies": phases["feedback_storm"]["applied"] >= max(1, phases["feedback_storm"]["cycles"] // 2),
        "maintenance_runs": phases["maintenance_pressure"]["planned_proposals"] >= 0,
        "backup_errors_zero": phases["backup_roundtrip"]["errors"] == 0,
        "runtime_health_ok": report["final_status"]["health_state"] in {"HEALTHY", "DEGRADED_SYNC"},
    }
    passed = all(checks.values())
    return {
        "passed": passed,
        "checks": checks,
        "score": round(sum(1.0 for ok in checks.values() if ok) / len(checks), 4) if checks else 0.0,
    }


def save_report(results_dir: Path, report: dict[str, Any], profile_name: str) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / f"v8-superstress-{profile_name}_{now_slug()}.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the heaviest v8 stress test available in this repo.")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="apocalypse")
    parser.add_argument("--workspace-dir", type=Path, default=Path("/tmp") / f"aegis_v8_superstress_{uuid.uuid4().hex[:8]}")
    parser.add_argument("--results-dir", type=Path, default=REPO_ROOT / "stress-results")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--keep-workspace", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profile = PROFILES[args.profile]
    rng = random.Random(args.seed)
    ensure_clean_dir(args.workspace_dir)
    db_path = args.workspace_dir / "v8_superstress.db"
    app = AegisApp(db_path=str(db_path))
    scopes = make_scopes(profile.scope_count)

    started_all = time.perf_counter()
    try:
        seed_phase = remember_seed_corpus(app, scopes, profile, rng=rng)
        canaries = seed_phase.pop("canaries")
        transition_candidates = seed_phase.pop("transition_candidates")

        phases = {
            "seed_corpus": seed_phase,
            "v8_state_amplification": amplify_v8_state(app, canaries, rng=rng),
            "retrieval_storm": run_retrieval_storm(app, canaries, profile.retrieval_queries, rng=rng),
            "concurrent_read_pressure": run_concurrent_read_pressure(
                str(db_path), canaries, profile.read_pressure_queries, profile.reader_threads, rng=rng
            ),
            "transition_storm": run_transition_storm(app, transition_candidates, rng=rng),
            "feedback_storm": run_feedback_storm(app, canaries, profile.feedback_cycles, rng=rng),
            "surface_pressure": run_surface_pressure(app, scopes, profile.surface_cycles, rng=rng),
            "maintenance_pressure": run_maintenance_pressure(app, scopes, profile.maintenance_cycles),
            "backup_roundtrip": run_backup_roundtrip(app, args.workspace_dir, profile.backup_cycles),
        }

        final_status = app.status()
        final_field = app.v8_field_snapshot()
        footprint = app.storage_footprint()
        report = {
            "profile": args.profile,
            "seed": args.seed,
            "workspace_dir": str(args.workspace_dir),
            "db_path": str(db_path),
            "duration_s": round(time.perf_counter() - started_all, 3),
            "phases": phases,
            "final_status": final_status,
            "final_field_snapshot": final_field,
            "final_storage_footprint": footprint,
        }
        report["gate"] = evaluate_report(report)
        output = save_report(args.results_dir, report, args.profile)
        print(json.dumps({"report_path": str(output), "gate": report["gate"], "duration_s": report["duration_s"]}, ensure_ascii=False, indent=2))
        return 0 if report["gate"]["passed"] else 2
    finally:
        app.close()
        if not args.keep_workspace:
            shutil.rmtree(args.workspace_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
