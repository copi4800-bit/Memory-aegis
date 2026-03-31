#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import random
import shutil
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aegis_py.app import AegisApp


@dataclass
class ApocalypseConfig:
    profile: str
    seed_count: int
    scope_count: int
    writer_threads: int
    reader_threads: int
    operations_per_writer: int
    operations_per_reader: int
    random_seed: int
    write_p95_budget_ms: float
    search_p95_budget_ms: float
    context_p95_budget_ms: float
    max_retry_budget: int


MAX_ERROR_SAMPLES = 8


def now_slug() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def summarize_latencies(values: list[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "min_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "mean_ms": 0.0}
    ordered = sorted(values)
    def at(ratio: float) -> float:
        index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
        return ordered[index]
    return {
        "count": len(values),
        "min_ms": round(min(values), 3),
        "p50_ms": round(at(0.50), 3),
        "p95_ms": round(at(0.95), 3),
        "max_ms": round(max(values), 3),
        "mean_ms": round(sum(values) / len(values), 3),
    }


def apply_profile(args: argparse.Namespace) -> ApocalypseConfig:
    profiles: dict[str, dict[str, int]] = {
        "quick": {
            "seed_count": 120,
            "scope_count": 4,
            "writer_threads": 2,
            "reader_threads": 2,
            "operations_per_writer": 20,
            "operations_per_reader": 30,
            "random_seed": 4419,
            "write_p95_budget_ms": 150.0,
            "search_p95_budget_ms": 100.0,
            "context_p95_budget_ms": 100.0,
            "max_retry_budget": 5,
        },
        "apocalypse": {
            "seed_count": 2000,
            "scope_count": 12,
            "writer_threads": 6,
            "reader_threads": 8,
            "operations_per_writer": 250,
            "operations_per_reader": 400,
            "random_seed": 4419,
            "write_p95_budget_ms": 800.0,
            "search_p95_budget_ms": 250.0,
            "context_p95_budget_ms": 300.0,
            "max_retry_budget": 10,
        },
        "overload": {
            "seed_count": 2400,
            "scope_count": 12,
            "writer_threads": 8,
            "reader_threads": 10,
            "operations_per_writer": 260,
            "operations_per_reader": 420,
            "random_seed": 4419,
            "write_p95_budget_ms": 1100.0,
            "search_p95_budget_ms": 300.0,
            "context_p95_budget_ms": 350.0,
            "max_retry_budget": 20,
        },
    }
    config = profiles[args.profile]
    return ApocalypseConfig(profile=args.profile, **config)


def make_scopes(scope_count: int) -> list[tuple[str, str]]:
    return [("project", f"APOC_{index:03d}") for index in range(scope_count)]


def canary_value(index: int) -> str:
    return f"apoc-canary-{index:05d}-{(index * 19) % 997:03d}"


def ensure_clean_dir(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)


def seed_baseline(
    app: AegisApp,
    *,
    scopes: list[tuple[str, str]],
    seed_count: int,
    rng: random.Random,
) -> dict[str, Any]:
    canaries: list[dict[str, str]] = []
    latencies: list[float] = []
    for index in range(seed_count):
        scope_type, scope_id = scopes[index % len(scopes)]
        memory_type = rng.choice(["semantic", "episodic", "working", "procedural"])
        canary = canary_value(index)
        started = time.perf_counter()
        stored = app.put_memory(
            f"Apocalypse seed {index}. Scope {scope_id}. Canary {canary}. Route token R{index % 31}.",
            type=memory_type,
            scope_type=scope_type,
            scope_id=scope_id,
            source_kind="manual",
            source_ref=f"apocalypse://seed/{index}",
            subject=f"apocalypse.topic.{index % 23}",
        )
        latencies.append((time.perf_counter() - started) * 1000.0)
        if stored is None:
            raise RuntimeError(f"seed rejected at index {index}")
        canaries.append(
            {
                "scope_type": scope_type,
                "scope_id": scope_id,
                "query": canary,
                "memory_id": stored.id,
            }
        )
    return {
        "seeded": seed_count,
        "canaries": canaries,
        "latency_ms": summarize_latencies(latencies),
    }


def is_retryable_sqlite_error(exc: BaseException) -> bool:
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    message = str(exc).lower()
    return "locked" in message or "busy" in message


def call_with_retry(fn: Callable[[], Any], *, retries: int = 8, base_sleep_s: float = 0.01) -> tuple[Any, int]:
    attempt = 0
    while True:
        try:
            return fn(), attempt
        except Exception as exc:
            if not is_retryable_sqlite_error(exc) or attempt >= retries:
                raise
            attempt += 1
            time.sleep(base_sleep_s * attempt)


def record_error_sample(samples: list[dict[str, str]], *, phase: str, operation: str, exc: BaseException) -> None:
    if len(samples) >= MAX_ERROR_SAMPLES:
        return
    samples.append(
        {
            "phase": phase,
            "operation": operation,
            "type": exc.__class__.__name__,
            "message": str(exc),
        }
    )


def _writer_worker(
    db_path: str,
    scopes: list[tuple[str, str]],
    operations: int,
    *,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    app = AegisApp(db_path=db_path)
    latencies: list[float] = []
    retries = 0
    written = 0
    errors = 0
    error_samples: list[dict[str, str]] = []
    try:
        for index in range(operations):
            scope_type, scope_id = rng.choice(scopes)
            started = time.perf_counter()
            try:
                _, used_retries = call_with_retry(
                    lambda: app.put_memory(
                        (
                            f"Concurrency write {index}. Scope {scope_id}. "
                            f"Worker seed {seed}. Token W{rng.randint(1000, 9999)}."
                        ),
                        type=rng.choice(["semantic", "episodic", "working"]),
                        scope_type=scope_type,
                        scope_id=scope_id,
                        source_kind="manual",
                        source_ref=f"apocalypse://writer/{seed}/{index}",
                        subject=f"apocalypse.concurrent.{index % 17}",
                    )
                )
                retries += used_retries
                written += 1
            except Exception as exc:
                errors += 1
                record_error_sample(
                    error_samples,
                    phase="concurrency_write",
                    operation=f"put_memory[{index}]",
                    exc=exc,
                )
            latencies.append((time.perf_counter() - started) * 1000.0)
    finally:
        app.close()
    return {
        "written": written,
        "errors": errors,
        "retries": retries,
        "latency_ms": latencies,
        "error_samples": error_samples,
    }


def _reader_worker(
    db_path: str,
    canaries: list[dict[str, str]],
    operations: int,
    *,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    app = AegisApp(db_path=db_path)
    search_latencies: list[float] = []
    context_latencies: list[float] = []
    retries = 0
    recall_hits = 0
    context_hits = 0
    errors = 0
    error_samples: list[dict[str, str]] = []
    try:
        for _ in range(operations):
            case = rng.choice(canaries)
            started = time.perf_counter()
            try:
                results, used_retries = call_with_retry(
                    lambda: app.search(
                        case["query"],
                        scope_type=case["scope_type"],
                        scope_id=case["scope_id"],
                        limit=5,
                        fallback_to_or=True,
                    )
                )
                retries += used_retries
                if any(case["query"] in item.memory.content for item in results):
                    recall_hits += 1
            except Exception as exc:
                errors += 1
                record_error_sample(
                    error_samples,
                    phase="concurrency_read",
                    operation=f"search[{case['memory_id']}]",
                    exc=exc,
                )
            search_latencies.append((time.perf_counter() - started) * 1000.0)

            started = time.perf_counter()
            try:
                pack, used_retries = call_with_retry(
                    lambda: app.search_context_pack(
                        case["query"],
                        scope_type=case["scope_type"],
                        scope_id=case["scope_id"],
                        limit=5,
                        semantic=True,
                    )
                )
                retries += used_retries
                if pack.get("results"):
                    context_hits += 1
            except Exception as exc:
                errors += 1
                record_error_sample(
                    error_samples,
                    phase="concurrency_context",
                    operation=f"search_context_pack[{case['memory_id']}]",
                    exc=exc,
                )
            context_latencies.append((time.perf_counter() - started) * 1000.0)
    finally:
        app.close()
    return {
        "errors": errors,
        "retries": retries,
        "recall_hits": recall_hits,
        "context_hits": context_hits,
        "search_latency_ms": search_latencies,
        "context_latency_ms": context_latencies,
        "operations": operations,
        "error_samples": error_samples,
    }


def run_concurrency_war(
    db_path: str,
    *,
    scopes: list[tuple[str, str]],
    canaries: list[dict[str, str]],
    writer_threads: int,
    reader_threads: int,
    operations_per_writer: int,
    operations_per_reader: int,
    rng: random.Random,
) -> dict[str, Any]:
    search_latencies: list[float] = []
    context_latencies: list[float] = []
    write_latencies: list[float] = []
    retries = 0
    hard_errors = 0
    written = 0
    recall_hits = 0
    context_hits = 0
    error_samples: list[dict[str, str]] = []
    futures = []
    with ThreadPoolExecutor(max_workers=writer_threads + reader_threads) as executor:
        for worker_index in range(writer_threads):
            futures.append(
                executor.submit(
                    _writer_worker,
                    db_path,
                    scopes,
                    operations_per_writer,
                    seed=rng.randint(1, 10_000_000),
                )
            )
        for worker_index in range(reader_threads):
            futures.append(
                executor.submit(
                    _reader_worker,
                    db_path,
                    canaries,
                    operations_per_reader,
                    seed=rng.randint(1, 10_000_000),
                )
            )
        for future in as_completed(futures):
            payload = future.result()
            retries += payload.get("retries", 0)
            hard_errors += payload.get("errors", 0)
            written += payload.get("written", 0)
            recall_hits += payload.get("recall_hits", 0)
            context_hits += payload.get("context_hits", 0)
            write_latencies.extend(payload.get("latency_ms", []))
            search_latencies.extend(payload.get("search_latency_ms", []))
            context_latencies.extend(payload.get("context_latency_ms", []))
            error_samples.extend(payload.get("error_samples", []))

    total_reader_ops = reader_threads * operations_per_reader
    return {
        "writer_threads": writer_threads,
        "reader_threads": reader_threads,
        "operations_per_writer": operations_per_writer,
        "operations_per_reader": operations_per_reader,
        "written": written,
        "hard_errors": hard_errors,
        "retries": retries,
        "recall_hit_rate": round(recall_hits / total_reader_ops, 4) if total_reader_ops else 0.0,
        "context_hit_rate": round(context_hits / total_reader_ops, 4) if total_reader_ops else 0.0,
        "write_latency_ms": summarize_latencies(write_latencies),
        "search_latency_ms": summarize_latencies(search_latencies),
        "context_latency_ms": summarize_latencies(context_latencies),
        "error_samples": error_samples[:MAX_ERROR_SAMPLES],
    }


def truncate_file_in_place(path: Path, *, ratio: float = 0.5, floor_bytes: int = 1024) -> None:
    with path.open("r+b") as fh:
        target = max(floor_bytes, int(path.stat().st_size * ratio))
        fh.truncate(target)


def simulate_corruption_and_recovery(
    db_path: str,
    workspace_dir: Path,
    *,
    canary: dict[str, str],
) -> dict[str, Any]:
    base_app = AegisApp(db_path=db_path)
    try:
        clean_snapshot = base_app.create_backup(workspace_dir=str(workspace_dir))
        clean_preview = base_app.preview_restore(clean_snapshot["path"])
    finally:
        base_app.close()

    corrupt_snapshot = workspace_dir / "corrupt-snapshot.db"
    shutil.copy2(clean_snapshot["path"], corrupt_snapshot)
    truncate_file_in_place(corrupt_snapshot)

    preview_probe = AegisApp(db_path=str(workspace_dir / "preview-probe.db"))
    try:
        corrupt_snapshot_error = None
        try:
            preview_probe.preview_restore(str(corrupt_snapshot))
        except Exception as exc:
            corrupt_snapshot_error = {
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
    finally:
        preview_probe.close()

    corrupt_live = workspace_dir / "corrupt-live.db"
    shutil.copy2(clean_snapshot["path"], corrupt_live)
    truncate_file_in_place(corrupt_live)
    corrupt_live_error = None
    try:
        broken = AegisApp(db_path=str(corrupt_live))
        try:
            broken.doctor(workspace_dir=str(workspace_dir))
        finally:
            broken.close()
    except Exception as exc:
        corrupt_live_error = {
            "type": exc.__class__.__name__,
            "message": str(exc),
        }

    recovered_db = workspace_dir / "recovered.db"
    recovery_app = AegisApp(db_path=str(recovered_db))
    try:
        restore = recovery_app.restore_backup(clean_snapshot["path"])
        doctor = recovery_app.doctor(workspace_dir=str(workspace_dir))
        status = recovery_app.status()
        results = recovery_app.search(
            canary["query"],
            scope_type=canary["scope_type"],
            scope_id=canary["scope_id"],
            limit=5,
            fallback_to_or=True,
        )
    finally:
        recovery_app.close()

    return {
        "clean_snapshot_path": clean_snapshot["path"],
        "clean_preview_records": clean_preview["preview"]["records"],
        "corrupt_snapshot_path": str(corrupt_snapshot),
        "corrupt_snapshot_rejected": corrupt_snapshot_error is not None,
        "corrupt_snapshot_error": corrupt_snapshot_error,
        "corrupt_live_path": str(corrupt_live),
        "corrupt_live_rejected": corrupt_live_error is not None,
        "corrupt_live_error": corrupt_live_error,
        "restore": restore,
        "recovered_health_state": doctor["health_state"],
        "recovered_counts": status["counts"],
        "recovered_canary_hit": any(canary["query"] in item.memory.content for item in results),
    }


def build_performance_budget(config: ApocalypseConfig) -> dict[str, float | int]:
    return {
        "write_p95_ms": config.write_p95_budget_ms,
        "search_p95_ms": config.search_p95_budget_ms,
        "context_p95_ms": config.context_p95_budget_ms,
        "max_retries": config.max_retry_budget,
    }


def evaluate_report(report: dict[str, Any], *, config: ApocalypseConfig) -> dict[str, Any]:
    budget = build_performance_budget(config)
    checks = {
        "concurrency_no_hard_errors": report["concurrency"]["hard_errors"] == 0,
        "concurrency_recall_floor": report["concurrency"]["recall_hit_rate"] >= 0.90,
        "concurrency_context_floor": report["concurrency"]["context_hit_rate"] >= 0.75,
        "concurrency_retry_budget": report["concurrency"]["retries"] <= budget["max_retries"],
        "write_p95_budget": report["concurrency"]["write_latency_ms"]["p95_ms"] <= budget["write_p95_ms"],
        "search_p95_budget": report["concurrency"]["search_latency_ms"]["p95_ms"] <= budget["search_p95_ms"],
        "context_p95_budget": report["concurrency"]["context_latency_ms"]["p95_ms"] <= budget["context_p95_ms"],
        "corrupt_snapshot_rejected": report["corruption_recovery"]["corrupt_snapshot_rejected"],
        "corrupt_live_rejected": report["corruption_recovery"]["corrupt_live_rejected"],
        "restore_succeeds": bool(report["corruption_recovery"]["restore"].get("restored")),
        "recovered_runtime_healthy": report["corruption_recovery"]["recovered_health_state"] in {"HEALTHY", "DEGRADED_SYNC"},
        "recovered_canary_hit": report["corruption_recovery"]["recovered_canary_hit"],
    }
    return {"passed": all(checks.values()), "checks": checks, "budgets": budget}


def run_apocalypse(
    *,
    db_path: str,
    workspace_dir: str,
    config: ApocalypseConfig,
) -> dict[str, Any]:
    workspace = Path(workspace_dir)
    ensure_clean_dir(workspace)
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
    db_file.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(config.random_seed)
    scopes = make_scopes(config.scope_count)
    app = AegisApp(db_path=str(db_file))
    try:
        seeded = seed_baseline(app, scopes=scopes, seed_count=config.seed_count, rng=rng)
    finally:
        app.close()

    concurrency = run_concurrency_war(
        str(db_file),
        scopes=scopes,
        canaries=seeded["canaries"],
        writer_threads=config.writer_threads,
        reader_threads=config.reader_threads,
        operations_per_writer=config.operations_per_writer,
        operations_per_reader=config.operations_per_reader,
        rng=rng,
    )

    corruption_recovery = simulate_corruption_and_recovery(
        str(db_file),
        workspace,
        canary=seeded["canaries"][0],
    )

    report = {
        "profile": config.profile,
        "db_path": str(db_file),
        "workspace_dir": str(workspace),
        "performance_budget": build_performance_budget(config),
        "seed": {
            "seed_count": config.seed_count,
            "scope_count": config.scope_count,
            "latency_ms": seeded["latency_ms"],
        },
        "concurrency": concurrency,
        "corruption_recovery": corruption_recovery,
    }
    report["evaluation"] = evaluate_report(report, config=config)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apocalypse runtime harness for Aegis v7.")
    parser.add_argument("--profile", choices=["quick", "apocalypse", "overload"], default="quick")
    parser.add_argument("--workspace-dir", default=str(REPO_ROOT / ".tmp_apocalypse"))
    parser.add_argument("--db-path", default=str(REPO_ROOT / ".tmp_apocalypse" / "apocalypse_v7.db"))
    parser.add_argument("--report-path", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.getLogger("aegis.runtime.observability").setLevel(logging.CRITICAL)
    logging.getLogger("aegis.sync.metrics").setLevel(logging.CRITICAL)
    config = apply_profile(args)
    report = run_apocalypse(
        db_path=args.db_path,
        workspace_dir=args.workspace_dir,
        config=config,
    )
    report_path = Path(args.report_path) if args.report_path else Path(args.workspace_dir) / f"apocalypse-report-{now_slug()}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "profile": config.profile,
                "concurrency_hard_errors": report["concurrency"]["hard_errors"],
                "concurrency_recall_hit_rate": report["concurrency"]["recall_hit_rate"],
                "concurrency_context_hit_rate": report["concurrency"]["context_hit_rate"],
                "concurrency_retries": report["concurrency"]["retries"],
                "write_p95_ms": report["concurrency"]["write_latency_ms"]["p95_ms"],
                "search_p95_ms": report["concurrency"]["search_latency_ms"]["p95_ms"],
                "context_p95_ms": report["concurrency"]["context_latency_ms"]["p95_ms"],
                "corrupt_snapshot_rejected": report["corruption_recovery"]["corrupt_snapshot_rejected"],
                "corrupt_live_rejected": report["corruption_recovery"]["corrupt_live_rejected"],
                "recovered_health_state": report["corruption_recovery"]["recovered_health_state"],
                "recovered_canary_hit": report["corruption_recovery"]["recovered_canary_hit"],
                "evaluation_passed": report["evaluation"]["passed"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
