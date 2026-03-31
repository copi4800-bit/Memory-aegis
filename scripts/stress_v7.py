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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aegis_py.app import AegisApp
from aegis_py.replication.identity import IdentityManager
from aegis_py.replication.sync import Mutation, ReplicationPayload, SyncManager
from aegis_py.storage.db import DatabaseManager


@dataclass
class PhaseResult:
    name: str
    duration_s: float
    details: dict[str, Any]


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


def make_scopes(scope_count: int) -> list[tuple[str, str]]:
    return [("project", f"STRESS_{index:03d}") for index in range(scope_count)]


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def canary_value(index: int) -> str:
    return f"canary-{index:05d}-{(index * 17) % 997:03d}"


def apply_profile(args: argparse.Namespace) -> None:
    profiles = {
        "default": {},
        "heavy": {
            "seed_count": 25000,
            "recall_queries": 6000,
            "read_pressure_queries": 10000,
            "reader_threads": 12,
            "mixed_operations": 3500,
            "scope_count": 20,
            "background_cycles": 32,
            "sync_cycles": 18,
            "backup_cycles": 6,
            "replication_cycles": 18,
            "surface_queries": 120,
        },
        "apocalypse": {
            "seed_count": 50000,
            "recall_queries": 12000,
            "read_pressure_queries": 22000,
            "reader_threads": 20,
            "mixed_operations": 8000,
            "scope_count": 32,
            "background_cycles": 64,
            "sync_cycles": 32,
            "backup_cycles": 10,
            "replication_cycles": 32,
            "surface_queries": 240,
        },
    }
    for key, value in profiles.get(args.profile, {}).items():
        setattr(args, key, value)


def seed_memories(app: AegisApp, scopes: list[tuple[str, str]], seed_count: int, *, rng: random.Random) -> dict[str, Any]:
    latencies: list[float] = []
    seeded_canaries: list[dict[str, str]] = []
    procedural = 0
    conflict_pairs = 0
    working = 0
    semantic = 0

    for index in range(seed_count):
        scope_type, scope_id = scopes[index % len(scopes)]
        memory_type = rng.choice(["semantic", "working", "episodic", "procedural"])
        subject = f"stress.topic.{index % 75}"
        canary = canary_value(index)
        content = (
            f"Stress seed {index}. Scope {scope_id}. Canary {canary}. "
            f"Owner lane {index % 9}. Workflow token W{index % 31}."
        )
        started = time.perf_counter()
        stored = app.put_memory(
            content,
            type=memory_type,
            scope_type=scope_type,
            scope_id=scope_id,
            source_kind="manual",
            source_ref=f"stress://seed/{index}",
            subject=subject,
        )
        latencies.append((time.perf_counter() - started) * 1000.0)
        if stored is None:
            raise RuntimeError(f"seed put_memory failed at index {index}")
        seeded_canaries.append({"scope_type": scope_type, "scope_id": scope_id, "query": canary, "memory_id": stored.id})
        if memory_type == "procedural":
            procedural += 1
        elif memory_type == "working":
            working += 1
        else:
            semantic += 1

        if index % 20 == 0:
            started = time.perf_counter()
            app.put_memory(
                f"Conflict seed {index}. Subject {subject} is DISABLED despite prior claims. Canary {canary}.",
                type="semantic",
                scope_type=scope_type,
                scope_id=scope_id,
                source_kind="manual",
                source_ref=f"stress://conflict/{index}",
                subject=subject,
            )
            latencies.append((time.perf_counter() - started) * 1000.0)
            conflict_pairs += 1

    return {
        "latency_ms": summarize_latencies(latencies),
        "seeded_canaries": seeded_canaries,
        "semantic_like_records": semantic,
        "working_records": working,
        "procedural_records": procedural,
        "conflict_pairs": conflict_pairs,
        "total_records_written": seed_count + conflict_pairs,
    }


def run_recall_pass(app: AegisApp, canaries: list[dict[str, str]], query_count: int, *, rng: random.Random) -> dict[str, Any]:
    latencies: list[float] = []
    hits = 0
    misses = 0

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
        if any(result.memory.id == case["memory_id"] or case["query"] in result.memory.content for result in results):
            hits += 1
        else:
            misses += 1

    total = hits + misses
    return {
        "latency_ms": summarize_latencies(latencies),
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hits / total, 4) if total else 0.0,
    }


def _read_worker(db_path: str, jobs: list[dict[str, str]]) -> dict[str, Any]:
    app = AegisApp(db_path=db_path)
    latencies: list[float] = []
    hits = 0
    errors = 0
    try:
        for job in jobs:
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
                if any(job["query"] in item.memory.content for item in results):
                    hits += 1
            except Exception:
                errors += 1
    finally:
        app.close()
    return {
        "latencies": latencies,
        "hits": hits,
        "errors": errors,
        "queries": len(jobs),
    }


def run_read_pressure(db_path: str, canaries: list[dict[str, str]], reader_threads: int, query_count: int, *, rng: random.Random) -> dict[str, Any]:
    jobs: list[dict[str, str]] = [rng.choice(canaries) for _ in range(query_count)]
    buckets: list[list[dict[str, str]]] = [[] for _ in range(reader_threads)]
    for index, job in enumerate(jobs):
        buckets[index % reader_threads].append(job)

    all_latencies: list[float] = []
    hits = 0
    errors = 0
    with ThreadPoolExecutor(max_workers=reader_threads) as executor:
        futures = [executor.submit(_read_worker, db_path, bucket) for bucket in buckets if bucket]
        for future in as_completed(futures):
            payload = future.result()
            all_latencies.extend(payload["latencies"])
            hits += payload["hits"]
            errors += payload["errors"]

    return {
        "threads": reader_threads,
        "queries": query_count,
        "hits": hits,
        "errors": errors,
        "hit_rate": round(hits / query_count, 4) if query_count else 0.0,
        "latency_ms": summarize_latencies(all_latencies),
    }


def run_mixed_workload(app: AegisApp, scopes: list[tuple[str, str]], operations: int, *, rng: random.Random) -> dict[str, Any]:
    counts = {"remember": 0, "recall": 0, "correct": 0, "forget": 0, "background": 0, "errors": 0}
    latencies: list[float] = []
    retained_queries: list[str] = []

    for index in range(operations):
        op = rng.choices(
            ["remember", "recall", "correct", "forget", "background"],
            weights=[40, 35, 10, 5, 10],
            k=1,
        )[0]
        started = time.perf_counter()
        try:
            if op == "remember":
                phrase = f"mixed-op-{index}-token-{rng.randint(1000, 9999)}"
                app.memory_remember(f"Hãy nhớ rằng dữ kiện kiểm thử của anh là {phrase}")
                retained_queries.append(phrase)
            elif op == "recall":
                if retained_queries:
                    query = rng.choice(retained_queries)
                    app.memory_recall(query)
                else:
                    app.memory_recall("mixed-op-empty-probe")
            elif op == "correct":
                phrase = f"corrected-op-{index}-token-{rng.randint(1000, 9999)}"
                app.memory_correct(f"Dữ kiện kiểm thử hiện tại là {phrase}")
                retained_queries.append(phrase)
            elif op == "forget":
                target = retained_queries.pop(0) if retained_queries else "mixed-op-empty-probe"
                app.memory_forget(target)
            else:
                scope_type, scope_id = scopes[index % len(scopes)]
                plan = app.plan_background_intelligence(scope_type=scope_type, scope_id=scope_id)
                if plan["proposal_count"] > 0:
                    run = next(
                        (
                            item for item in app.storage.list_background_intelligence_runs(
                                scope_type=scope_type,
                                scope_id=scope_id,
                                status="planned",
                            )
                            if item["worker_kind"] == "graph_repair"
                        ),
                        None,
                    )
                    if run is not None:
                        app.apply_background_intelligence_run(run["id"], max_mutations=25)
                        app.rollback_background_intelligence_run(run["id"])
            counts[op] += 1
        except Exception:
            counts["errors"] += 1
        latencies.append((time.perf_counter() - started) * 1000.0)

    counts["retained_queries"] = len(retained_queries)
    counts["latency_ms"] = summarize_latencies(latencies)
    return counts


def run_background_pressure(app: AegisApp, scopes: list[tuple[str, str]], cycles: int) -> dict[str, Any]:
    planned = 0
    applied = 0
    rolled_back = 0
    blocked = 0
    latencies: list[float] = []

    for index in range(cycles):
        scope_type, scope_id = scopes[index % len(scopes)]
        started = time.perf_counter()
        plan = app.plan_background_intelligence(scope_type=scope_type, scope_id=scope_id)
        planned += plan["proposal_count"]
        runs = app.storage.list_background_intelligence_runs(scope_type=scope_type, scope_id=scope_id, status="planned")
        for run in runs[:3]:
            if run["worker_kind"] == "condensation":
                shadow = app.shadow_background_intelligence_run(run["id"])
                if shadow.get("shadowed"):
                    blocked += 1
                continue
            outcome = app.apply_background_intelligence_run(run["id"], max_mutations=25)
            if outcome.get("applied"):
                applied += 1
                rb = app.rollback_background_intelligence_run(run["id"])
                if rb.get("rolled_back"):
                    rolled_back += 1
            else:
                blocked += 1
        latencies.append((time.perf_counter() - started) * 1000.0)

    return {
        "cycles": cycles,
        "planned_proposals": planned,
        "applied_runs": applied,
        "rolled_back_runs": rolled_back,
        "blocked_or_shadowed_runs": blocked,
        "latency_ms": summarize_latencies(latencies),
    }


def run_sync_roundtrip(source_app: AegisApp, workspace_dir: Path, scopes: list[tuple[str, str]], sync_cycles: int) -> dict[str, Any]:
    target_db = workspace_dir / "sync_target.db"
    if target_db.exists():
        target_db.unlink()
    target_app = AegisApp(db_path=str(target_db))
    latencies: list[float] = []
    exported = 0
    imported = 0
    previewed = 0
    errors = 0
    try:
        for scope_type, scope_id in scopes:
            source_app.set_scope_policy(scope_type=scope_type, scope_id=scope_id, sync_policy="sync_eligible")
            target_app.set_scope_policy(scope_type=scope_type, scope_id=scope_id, sync_policy="sync_eligible")
        for index in range(sync_cycles):
            scope_type, scope_id = scopes[index % len(scopes)]
            started = time.perf_counter()
            try:
                envelope = source_app.export_sync_envelope(scope_type=scope_type, scope_id=scope_id, workspace_dir=str(workspace_dir))
                exported += 1
                preview = target_app.preview_sync_envelope(envelope["path"])
                if preview.get("dry_run"):
                    previewed += 1
                imported_payload = target_app.import_sync_envelope(envelope["path"])
                if imported_payload.get("imported"):
                    imported += 1
            except Exception:
                errors += 1
            latencies.append((time.perf_counter() - started) * 1000.0)

        target_status = target_app.status()
    finally:
        target_app.close()

    return {
        "cycles": sync_cycles,
        "exported": exported,
        "previewed": previewed,
        "imported": imported,
        "errors": errors,
        "target_counts": target_status["counts"],
        "latency_ms": summarize_latencies(latencies),
    }


def run_backup_restore_roundtrip(source_app: AegisApp, workspace_dir: Path, backup_cycles: int) -> dict[str, Any]:
    restore_db = workspace_dir / "restore_target.db"
    if restore_db.exists():
        restore_db.unlink()
    restore_app = AegisApp(db_path=str(restore_db))
    created = 0
    previewed = 0
    restored = 0
    errors = 0
    latencies: list[float] = []
    last_restore: dict[str, Any] | None = None

    try:
        for _ in range(backup_cycles):
            started = time.perf_counter()
            try:
                backup = source_app.create_backup(mode="snapshot", workspace_dir=str(workspace_dir))
                created += 1
                preview = restore_app.preview_restore(backup["path"])
                if preview.get("preview"):
                    previewed += 1
                restored_payload = restore_app.restore_backup(backup["path"])
                if restored_payload.get("restored"):
                    restored += 1
                    last_restore = restored_payload
            except Exception:
                errors += 1
            latencies.append((time.perf_counter() - started) * 1000.0)
        restore_status = restore_app.status()
    finally:
        restore_app.close()

    return {
        "cycles": backup_cycles,
        "created": created,
        "previewed": previewed,
        "restored": restored,
        "errors": errors,
        "restore_status": restore_status["counts"],
        "last_restore": last_restore,
        "latency_ms": summarize_latencies(latencies),
    }


def run_surface_pressure(app: AegisApp, canaries: list[dict[str, str]], surface_queries: int, *, rng: random.Random) -> dict[str, Any]:
    context_latencies: list[float] = []
    vector_latencies: list[float] = []
    governance_latencies: list[float] = []
    evidence_latencies: list[float] = []
    rebuild_latencies: list[float] = []
    scan_latencies: list[float] = []
    context_hits = 0
    vector_hits = 0
    evidence_artifact_count = 0

    for index in range(surface_queries):
        case = rng.choice(canaries)

        started = time.perf_counter()
        pack = app.search_context_pack(
            case["query"],
            scope_type=case["scope_type"],
            scope_id=case["scope_id"],
            limit=5,
            semantic=True,
        )
        context_latencies.append((time.perf_counter() - started) * 1000.0)
        if pack.get("results"):
            context_hits += 1

        started = time.perf_counter()
        vector = app.inspect_vector_store(
            query=case["query"],
            scope_type=case["scope_type"],
            scope_id=case["scope_id"],
            limit=5,
        )
        vector_latencies.append((time.perf_counter() - started) * 1000.0)
        if vector.get("matches"):
            vector_hits += 1

        if index % 12 == 0:
            started = time.perf_counter()
            governance = app.inspect_governance(scope_type=case["scope_type"], scope_id=case["scope_id"], limit=25)
            governance_latencies.append((time.perf_counter() - started) * 1000.0)
            started = time.perf_counter()
            evidence = app.evidence_artifacts(scope_type=case["scope_type"], scope_id=case["scope_id"])
            evidence_latencies.append((time.perf_counter() - started) * 1000.0)
            evidence_artifact_count += len(evidence.get("artifacts", []))

        if index % 40 == 0:
            started = time.perf_counter()
            app.rebuild()
            rebuild_latencies.append((time.perf_counter() - started) * 1000.0)
            started = time.perf_counter()
            app.scan()
            scan_latencies.append((time.perf_counter() - started) * 1000.0)

    visual = app.visualize(limit=min(500, max(100, len(canaries) * 2)), include_analysis=True)
    return {
        "surface_queries": surface_queries,
        "context_hit_rate": round(context_hits / surface_queries, 4) if surface_queries else 0.0,
        "vector_hit_rate": round(vector_hits / surface_queries, 4) if surface_queries else 0.0,
        "visual_nodes": len(visual.get("nodes", [])),
        "visual_links": len(visual.get("links", [])),
        "evidence_artifact_count": evidence_artifact_count,
        "context_latency_ms": summarize_latencies(context_latencies),
        "vector_latency_ms": summarize_latencies(vector_latencies),
        "governance_latency_ms": summarize_latencies(governance_latencies),
        "evidence_latency_ms": summarize_latencies(evidence_latencies),
        "rebuild_latency_ms": summarize_latencies(rebuild_latencies),
        "scan_latency_ms": summarize_latencies(scan_latencies),
    }


def run_replication_pressure(workspace_dir: Path, replication_cycles: int, *, rng: random.Random) -> dict[str, Any]:
    db_path = workspace_dir / "replication_stress.db"
    if db_path.exists():
        db_path.unlink()
    db = DatabaseManager(str(db_path))
    db.initialize()
    identity = IdentityManager(db)
    manager = SyncManager(db, identity)
    local_identity = identity.get_local_identity()

    apply_latencies: list[float] = []
    successes = 0
    failures = 0
    conflicts = 0
    skipped = 0

    try:
        for cycle in range(replication_cycles):
            remote_node = f"remote-stress-{cycle % 5}"
            base_id = f"rep-{cycle:05d}"
            payload = ReplicationPayload(
                payload_id=str(uuid.uuid4()),
                origin_node_id=remote_node,
                scope_type="project",
                scope_id=f"REPL_{cycle % 4}",
                mutations=[
                    Mutation(
                        action="upsert",
                        entity_type="memory",
                        entity_id=base_id,
                        data={
                            "id": base_id,
                            "type": "semantic",
                            "scope_type": "project",
                            "scope_id": f"REPL_{cycle % 4}",
                            "content": f"replication payload {cycle} token {rng.randint(1000, 9999)}",
                            "status": "active",
                        },
                        timestamp=datetime.now(timezone.utc),
                    )
                ],
            )

            if cycle % 6 == 0:
                db.execute(
                    """
                    INSERT OR REPLACE INTO memories (
                        id, type, scope_type, scope_id, content, source_kind, status, origin_node_id, created_at, updated_at, metadata_json
                    ) VALUES (?, 'semantic', 'project', ?, ?, 'manual', 'active', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '{}')
                    """,
                    (base_id, f"REPL_{cycle % 4}", f"local conflicting record {cycle}", local_identity.node_id),
                )

            started = time.perf_counter()
            try:
                stats = manager.apply_payload(payload)
                apply_latencies.append((time.perf_counter() - started) * 1000.0)
                successes += stats["applied"]
                conflicts += stats["conflicts"]
                skipped += stats["skipped"]
            except Exception:
                failures += 1
        audit_rows = db.fetch_one("SELECT COUNT(*) AS count FROM replication_audit_log")
    finally:
        db.close()

    return {
        "cycles": replication_cycles,
        "applied": successes,
        "conflicts": conflicts,
        "skipped": skipped,
        "failures": failures,
        "audit_rows": audit_rows["count"] if audit_rows else 0,
        "latency_ms": summarize_latencies(apply_latencies),
    }


def run_compaction_phase(app: AegisApp) -> dict[str, Any]:
    before = app.storage_footprint()
    started = time.perf_counter()
    result = app.compact_storage(vacuum=True)
    duration_ms = (time.perf_counter() - started) * 1000.0
    after = app.storage_footprint()
    return {
        "duration_ms": round(duration_ms, 3),
        "deleted": result["deleted"],
        "vacuumed": result["vacuumed"],
        "allocated_bytes_before": before["allocated_bytes"],
        "allocated_bytes_after": after["allocated_bytes"],
        "free_bytes_before": before["free_bytes"],
        "free_bytes_after": after["free_bytes"],
        "memory_rows_before": before["rows"].get("memories", 0),
        "memory_rows_after": after["rows"].get("memories", 0),
    }


def evaluate_report(report: dict[str, Any]) -> dict[str, Any]:
    phases = report["phases"]
    checks = {
        "doctor_healthy": report["final_doctor"]["health_state"] in {"HEALTHY", "DEGRADED_SYNC"},
        "read_pressure_no_errors": phases["read_pressure"]["errors"] == 0,
        "mixed_no_errors": phases["mixed_workload"]["errors"] == 0,
        "sync_no_errors": phases["sync"]["errors"] == 0,
        "backup_no_errors": phases["backup_restore"]["errors"] == 0,
        "replication_no_failures": phases["replication"]["failures"] == 0,
        "recall_hit_rate_floor": phases["recall"]["hit_rate"] >= 0.90,
        "surface_context_floor": phases["surfaces"]["context_hit_rate"] >= 0.75,
        "compaction_did_not_grow_db": phases["compaction"]["allocated_bytes_after"] <= phases["compaction"]["allocated_bytes_before"],
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
    }


def build_report(args: argparse.Namespace, phase_results: list[PhaseResult], app: AegisApp, workspace_dir: Path) -> dict[str, Any]:
    return {
        "started_at": args.started_at,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "db_path": str(Path(args.db_path).resolve()),
        "workspace_dir": str(workspace_dir.resolve()),
        "config": {
            "profile": args.profile,
            "seed_count": args.seed_count,
            "recall_queries": args.recall_queries,
            "read_pressure_queries": args.read_pressure_queries,
            "reader_threads": args.reader_threads,
            "mixed_operations": args.mixed_operations,
            "scope_count": args.scope_count,
            "background_cycles": args.background_cycles,
            "sync_cycles": args.sync_cycles,
            "backup_cycles": args.backup_cycles,
            "replication_cycles": args.replication_cycles,
            "surface_queries": args.surface_queries,
            "random_seed": args.random_seed,
        },
        "phases": {item.name: {"duration_s": round(item.duration_s, 3), **item.details} for item in phase_results},
        "final_status": app.status(),
        "final_doctor": app.doctor(workspace_dir=str(workspace_dir)),
        "observability": app.observability_snapshot(),
    }


def run_phase(name: str, fn) -> PhaseResult:
    started = time.perf_counter()
    details = fn()
    return PhaseResult(name=name, duration_s=time.perf_counter() - started, details=details)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heavy stress harness for Memory Aegis v7.")
    parser.add_argument("--db-path", default=str(REPO_ROOT / ".tmp_stress" / "stress_v7.db"))
    parser.add_argument("--workspace-dir", default=str(REPO_ROOT / ".tmp_stress"))
    parser.add_argument("--profile", choices=["default", "heavy", "apocalypse"], default="default")
    parser.add_argument("--seed-count", type=int, default=12000)
    parser.add_argument("--recall-queries", type=int, default=2500)
    parser.add_argument("--read-pressure-queries", type=int, default=4000)
    parser.add_argument("--reader-threads", type=int, default=8)
    parser.add_argument("--mixed-operations", type=int, default=1800)
    parser.add_argument("--scope-count", type=int, default=12)
    parser.add_argument("--background-cycles", type=int, default=18)
    parser.add_argument("--sync-cycles", type=int, default=12)
    parser.add_argument("--backup-cycles", type=int, default=4)
    parser.add_argument("--replication-cycles", type=int, default=10)
    parser.add_argument("--surface-queries", type=int, default=60)
    parser.add_argument("--random-seed", type=int, default=4419)
    parser.add_argument("--report-path", default=None)
    parser.add_argument("--keep-workspace", action="store_true")
    parser.add_argument("--verbose-events", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    apply_profile(args)
    workspace_dir = Path(args.workspace_dir)
    db_path = Path(args.db_path)
    rng = random.Random(args.random_seed)

    if not args.verbose_events:
        logging.getLogger("aegis.runtime.observability").setLevel(logging.CRITICAL)
        logging.getLogger("aegis.sync.metrics").setLevel(logging.CRITICAL)

    if not args.keep_workspace:
        ensure_clean_dir(workspace_dir)
    else:
        workspace_dir.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    scopes = make_scopes(args.scope_count)
    phase_results: list[PhaseResult] = []
    app = AegisApp(db_path=str(db_path))

    try:
        seed_phase = run_phase("seed", lambda: seed_memories(app, scopes, args.seed_count, rng=rng))
        phase_results.append(seed_phase)

        canaries = seed_phase.details["seeded_canaries"]
        phase_results.append(run_phase("recall", lambda: run_recall_pass(app, canaries, args.recall_queries, rng=rng)))
        phase_results.append(run_phase("read_pressure", lambda: run_read_pressure(str(db_path), canaries, args.reader_threads, args.read_pressure_queries, rng=rng)))
        phase_results.append(run_phase("mixed_workload", lambda: run_mixed_workload(app, scopes, args.mixed_operations, rng=rng)))
        phase_results.append(run_phase("background", lambda: run_background_pressure(app, scopes, args.background_cycles)))
        phase_results.append(run_phase("surfaces", lambda: run_surface_pressure(app, canaries, args.surface_queries, rng=rng)))
        phase_results.append(run_phase("sync", lambda: run_sync_roundtrip(app, workspace_dir, scopes, args.sync_cycles)))
        phase_results.append(run_phase("backup_restore", lambda: run_backup_restore_roundtrip(app, workspace_dir, args.backup_cycles)))
        phase_results.append(run_phase("replication", lambda: run_replication_pressure(workspace_dir, args.replication_cycles, rng=rng)))
        phase_results.append(run_phase("compaction", lambda: run_compaction_phase(app)))

        report = build_report(args, phase_results, app, workspace_dir)
        report["evaluation"] = evaluate_report(report)
        report_path = Path(args.report_path) if args.report_path else workspace_dir / f"stress-report-{now_slug()}.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        print(json.dumps(
            {
                "report_path": str(report_path),
                "health_state": report["final_doctor"]["health_state"],
                "active_counts": report["final_status"]["counts"],
                "phase_names": list(report["phases"].keys()),
                "read_pressure_p95_ms": report["phases"]["read_pressure"]["latency_ms"]["p95_ms"],
                "surface_context_hit_rate": report["phases"]["surfaces"]["context_hit_rate"],
                "mixed_errors": report["phases"]["mixed_workload"]["errors"],
                "sync_errors": report["phases"]["sync"]["errors"],
                "backup_errors": report["phases"]["backup_restore"]["errors"],
                "replication_failures": report["phases"]["replication"]["failures"],
                "evaluation_passed": report["evaluation"]["passed"],
            },
            indent=2,
            ensure_ascii=False,
        ))
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
