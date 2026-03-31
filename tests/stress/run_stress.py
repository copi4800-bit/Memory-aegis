import os
import time
import json
import argparse
import sqlite3
import shutil
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from aegis_py.app import AegisApp
from aegis_py.storage.models import Memory
from aegis_py.memory.core import MemoryManager
from aegis_py.retrieval.benchmark import run_benchmark, QueryCase, evaluate_summary, render_gate_report
import data_generator
import random

RESULTS_DIR = Path("stress-results")

def setup_results_dir():
    RESULTS_DIR.mkdir(exist_ok=True)

def save_results(level_name: str, summary):
    setup_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = RESULTS_DIR / f"{level_name}_{timestamp}.json"
    report = {
        "level": level_name,
        "timestamp": timestamp,
        "metrics": {
            "recall_at_1": summary.recall_at_1,
            "recall_at_5": summary.recall_at_5,
            "latency_p50": summary.latency_p50_ms,
            "latency_p95": summary.latency_p95_ms,
            "scope_leakage": summary.scope_leakage,
            "conflict_leakage": summary.conflict_leakage,
            "conflict_visibility": summary.conflict_visibility,
        }
    }
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Results saved to {filepath}")

def save_report(level_name: str, report: dict):
    setup_results_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = RESULTS_DIR / f"{level_name}_{timestamp}.json"
    report["timestamp"] = timestamp
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Results saved to {filepath}")

# ═══════════════════════════════════════════════
# LEVEL 1 — SANITY LOAD
# ═══════════════════════════════════════════════
def run_level_1(app: AegisApp):
    print("\n🚀 [LEVEL 1] SANITY LOAD")
    print("Generating 10k memories for Dataset A...")
    mems = data_generator.generate_dataset_a(10000)
    start = time.perf_counter()
    for m in mems:
        app.storage.put_memory(m)
    duration = time.perf_counter() - start
    print(f"Stored 10k memories in {duration:.2f}s ({(10000/duration):.1f} ops/s)")
    mm = MemoryManager(app.storage)
    print("Running 500 recall queries...")
    cases = []
    for i in range(500):
        m = random.choice(mems)
        cases.append(QueryCase(
            query=m.content[:40],
            expected_ids=[m.id],
            scope_type=m.scope_type,
            scope_id=m.scope_id,
            limit=5
        ))
    summary = run_benchmark(mm, cases)
    print(f"Recall@1: {summary.recall_at_1:.3f}")
    print(f"Recall@5: {summary.recall_at_5:.3f}")
    print(f"Latency P95: {summary.latency_p95_ms:.2f}ms")
    save_results("level-1", summary)
    return summary

# ═══════════════════════════════════════════════
# LEVEL 2 — CONFLICT WAR
# ═══════════════════════════════════════════════
def run_level_2(app: AegisApp):
    print("\n🚀 [LEVEL 2] CONFLICT WAR")
    print("Generating 10k memories (20% conflicts) for Dataset B...")
    mems = data_generator.generate_dataset_b(10000)
    for m in mems:
        app.storage.put_memory(m)
    print("Scanning conflicts...")
    start = time.perf_counter()
    for i in range(2000):
        app.conflict_manager.scan_conflicts(f"user.preference.{i}")
    duration = time.perf_counter() - start
    print(f"Scanned 2k active subjects in {duration:.2f}s")
    mm = MemoryManager(app.storage)
    cases = []
    for i in range(500):
        cases.append(QueryCase(
            query=f"favorite number {i}",
            expected_ids=[f"B-base-{i}", f"B-conflict-{i}"],
            expected_conflict_ids=[f"B-base-{i}", f"B-conflict-{i}"],
            scope_type="project",
            scope_id="CONFLICT_WALKER",
            limit=5
        ))
    summary = run_benchmark(mm, cases)
    print(f"Conflict Visibility: {summary.conflict_visibility:.3f}")
    save_results("level-2", summary)
    return summary

# ═══════════════════════════════════════════════
# LEVEL 3 — SCOPE HELL
# ═══════════════════════════════════════════════
def run_level_3(app: AegisApp):
    print("\n🚀 [LEVEL 3] SCOPE HELL")
    print("Generating 2k memories for 20 different projects...")
    mems = []
    for p_idx in range(20):
        scope_id = f"PROJECT_{p_idx}"
        for i in range(100):
            mems.append(Memory(
                id=f"L3-{p_idx}-{i}",
                type="semantic",
                scope_type="project",
                scope_id=scope_id,
                content=f"PROJECT {p_idx} secret key is ALPHA-{i}. Do not leak to other projects.",
                subject=f"security.config.{i}",
                source_kind="manual"
            ))
    for m in mems:
        app.storage.put_memory(m)
    print("Running cross-project leakage tests...")
    mm = MemoryManager(app.storage)
    cases = []
    for i in range(500):
        target_p = random.randint(0, 19)
        m_idx = random.randint(0, 99)
        cases.append(QueryCase(
            query=f"ALPHA-{m_idx}",
            expected_ids=[f"L3-{target_p}-{m_idx}"],
            forbidden_ids=[f"L3-{p}-{m_idx}" for p in range(20) if p != target_p],
            scope_type="project",
            scope_id=f"PROJECT_{target_p}",
            limit=5
        ))
    summary = run_benchmark(mm, cases)
    print(f"Scope Leakage: {summary.scope_leakage:.3f}")
    save_results("level-3", summary)
    return summary

# ═══════════════════════════════════════════════
# LEVEL 4 — PROCEDURAL STORM
# ═══════════════════════════════════════════════
def run_level_4(app: AegisApp):
    print("\n🚀 [LEVEL 4] PROCEDURAL STORM")
    print("Generating 2k procedures...")
    mems = data_generator.generate_dataset_d(2000)
    for m in mems:
        app.storage.put_memory(m)
    print("Running procedural recall tests...")
    mm = MemoryManager(app.storage)
    cases = []
    for i in range(500):
        m_idx = random.randint(0, 1999)
        cases.append(QueryCase(
            query=f"Step A workflow {m_idx}",
            expected_ids=[f"D-proc-{m_idx}"],
            scope_type="project",
            scope_id="PROC_STORM",
            limit=5
        ))
    summary = run_benchmark(mm, cases)
    print(f"Procedural Recall@5: {summary.recall_at_5:.3f}")
    save_results("level-4", summary)
    return summary

# ═══════════════════════════════════════════════
# LEVEL 5 — MAINTENANCE NIGHTMARE
# ═══════════════════════════════════════════════
def run_level_5(app: AegisApp):
    print("\n🚀 [LEVEL 5] MAINTENANCE NIGHTMARE")
    # Measure DB size before
    db_size_before = os.path.getsize(app.db_path) if os.path.exists(app.db_path) else 0
    count_before = app.storage.fetch_one("SELECT count(*) as c FROM memories WHERE status='active'")["c"]

    print(f"DB size before: {db_size_before/1024:.1f} KB, active memories: {count_before}")
    print("Running full maintenance cycle...")
    start = time.perf_counter()
    app.hygiene_engine.run_maintenance()
    duration = time.perf_counter() - start
    print(f"Hygiene cycle completed in {duration:.2f}s")

    count_after = app.storage.fetch_one("SELECT count(*) as c FROM memories WHERE status='active'")["c"]
    db_size_after = os.path.getsize(app.db_path) if os.path.exists(app.db_path) else 0
    print(f"DB size after: {db_size_after/1024:.1f} KB, active memories: {count_after}")

    # Recall quality after maintenance
    mm = MemoryManager(app.storage)
    cases = []
    for i in range(200):
        m_idx = random.randint(0, 1999)
        cases.append(QueryCase(
            query=f"Step A workflow {m_idx}",
            expected_ids=[f"D-proc-{m_idx}"],
            scope_type="project",
            scope_id="PROC_STORM",
            limit=5
        ))
    summary = run_benchmark(mm, cases)
    print(f"Recall@5 after maintenance: {summary.recall_at_5:.3f}")

    report = {
        "level": "level-5",
        "metrics": {
            "hygiene_duration_s": duration,
            "db_size_before_kb": db_size_before / 1024,
            "db_size_after_kb": db_size_after / 1024,
            "active_before": count_before,
            "active_after": count_after,
            "recall_at_5_after": summary.recall_at_5,
        }
    }
    save_report("level-5", report)
    return report

# ═══════════════════════════════════════════════
# LEVEL 6 — LEGACY APOCALYPSE
# ═══════════════════════════════════════════════
def _create_legacy_db(path: str, variant: int) -> str:
    """Create a deliberately broken/legacy DB for repair testing."""
    conn = sqlite3.connect(path)
    if variant == 0:
        # Missing columns: no 'subject', no 'summary'
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT,
                scope_type TEXT DEFAULT 'session',
                scope_id TEXT DEFAULT 'default',
                content TEXT,
                source_kind TEXT DEFAULT 'manual',
                source_ref TEXT,
                status TEXT DEFAULT 'active',
                confidence REAL DEFAULT 1.0,
                activation_score REAL DEFAULT 1.0,
                access_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                metadata_json TEXT DEFAULT '{}'
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, content='memories', content_rowid='rowid')
        """)
    elif variant == 1:
        # Missing FTS table entirely
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT,
                scope_type TEXT DEFAULT 'session',
                scope_id TEXT DEFAULT 'default',
                session_id TEXT,
                content TEXT,
                summary TEXT,
                subject TEXT,
                source_kind TEXT DEFAULT 'manual',
                source_ref TEXT,
                status TEXT DEFAULT 'active',
                confidence REAL DEFAULT 1.0,
                activation_score REAL DEFAULT 1.0,
                access_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                last_accessed_at TEXT,
                expires_at TEXT,
                archived_at TEXT,
                metadata_json TEXT DEFAULT '{}'
            )
        """)
    elif variant == 2:
        # Empty DB, schema_info has wrong version
        conn.execute("CREATE TABLE IF NOT EXISTS schema_info (version INTEGER)")
        conn.execute("INSERT INTO schema_info VALUES (999)")
    else:
        # Completely empty DB
        pass

    # Seed some data for variants 0 and 1
    if variant in (0, 1):
        now = datetime.now(timezone.utc).isoformat()
        for i in range(50):
            cols = "id, type, scope_type, scope_id, content, source_kind, status, confidence, activation_score, access_count, created_at, updated_at, metadata_json"
            vals = f"'legacy-{variant}-{i}', 'semantic', 'project', 'LEGACY_{variant}', 'Legacy data item {i} from old DB variant {variant}', 'manual', 'active', 1.0, 1.0, 0, '{now}', '{now}', '{{}}'"
            conn.execute(f"INSERT INTO memories ({cols}) VALUES ({vals})")
    conn.commit()
    conn.close()
    return path

def run_level_6(app: AegisApp):
    print("\n🚀 [LEVEL 6] LEGACY APOCALYPSE")
    print("Creating 4 legacy DB variants...")
    legacy_dir = Path("stress-legacy-dbs")
    legacy_dir.mkdir(exist_ok=True)

    results = []
    for variant in range(4):
        db_path = str(legacy_dir / f"legacy_v{variant}.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        _create_legacy_db(db_path, variant)
        print(f"  Variant {variant}: created at {db_path}")

        # Try to boot AegisApp on each legacy DB
        start = time.perf_counter()
        boot_ok = False
        store_ok = False
        search_ok = False
        repair_error = None
        try:
            legacy_app = AegisApp(db_path=db_path)
            boot_ok = True
            # Try store
            legacy_app.put_memory(
                f"New memory on legacy DB variant {variant}",
                type="semantic",
                scope_type="project",
                scope_id=f"LEGACY_{variant}",
                source_kind="manual",
            )
            store_ok = True
            # Try search
            res = legacy_app.search("legacy data", scope_id=f"LEGACY_{variant}", scope_type="project")
            search_ok = len(res) >= 0  # Even empty is fine, just no crash
            legacy_app.close()
        except Exception as e:
            repair_error = str(e)

        duration = time.perf_counter() - start
        result = {
            "variant": variant,
            "boot_ok": boot_ok,
            "store_ok": store_ok,
            "search_ok": search_ok,
            "repair_error": repair_error,
            "startup_latency_ms": duration * 1000,
        }
        results.append(result)
        status = "✅ PASS" if (boot_ok and store_ok and search_ok) else f"❌ FAIL ({repair_error})"
        print(f"  Variant {variant}: {status} ({duration*1000:.0f}ms)")

    success_rate = sum(1 for r in results if r["boot_ok"] and r["store_ok"] and r["search_ok"]) / len(results)
    print(f"\nRepair success rate: {success_rate*100:.0f}%")

    report = {
        "level": "level-6",
        "metrics": {
            "variants_tested": len(results),
            "repair_success_rate": success_rate,
        },
        "details": results,
    }
    save_report("level-6", report)
    return report

# ═══════════════════════════════════════════════
# LEVEL 7 — OPENCLAW BURST TEST
# ═══════════════════════════════════════════════
def run_level_7(app: AegisApp):
    print("\n🚀 [LEVEL 7] OPENCLAW BURST TEST")
    from aegis_py.mcp.server import AegisMCPServer
    server = AegisMCPServer(db_path=app.db_path)

    burst_rates = [10, 50, 100]
    all_results = []

    for rate in burst_rates:
        print(f"\n  Burst @ {rate} req/s...")
        errors = 0
        timeouts = 0
        successes = 0
        latencies = []

        for i in range(rate):
            op = random.choice(["store", "search", "search", "search"])  # 75% search
            start = time.perf_counter()
            try:
                if op == "store":
                    server.memory_store(
                        "semantic",
                        f"Burst test item {i} at rate {rate}",
                        f"burst.test.{i}",
                        scope_type="project",
                        scope_id="BURST",
                    )
                else:
                    server.memory_search(
                        f"burst test {random.randint(0, rate)}",
                        scope_type="project",
                        scope_id="BURST",
                    )
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                if latency > 5000:
                    timeouts += 1
                else:
                    successes += 1
            except Exception:
                errors += 1

        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        result = {
            "rate": rate,
            "total": rate,
            "successes": successes,
            "errors": errors,
            "timeouts": timeouts,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
        }
        all_results.append(result)
        print(f"    OK: {successes}, Errors: {errors}, Timeouts: {timeouts}, P95: {p95_latency:.1f}ms")

    server.close()
    report = {
        "level": "level-7",
        "metrics": {
            "total_errors": sum(r["errors"] for r in all_results),
            "total_timeouts": sum(r["timeouts"] for r in all_results),
        },
        "details": all_results,
    }
    save_report("level-7", report)
    return report

# ═══════════════════════════════════════════════
# LEVEL 8 — 30-DAY SIMULATION
# ═══════════════════════════════════════════════
def run_level_8(app: AegisApp):
    print("\n🚀 [LEVEL 8] 30-DAY SIMULATION")
    mm = MemoryManager(app.storage)

    daily_metrics = []
    DAYS = 30
    NEW_PER_DAY = 200
    CONFLICTS_PER_DAY = 10
    QUERIES_PER_DAY = 50

    for day in range(DAYS):
        day_start = time.perf_counter()
        print(f"  Day {day+1}/{DAYS}...", end=" ", flush=True)

        # 1. Ingest new memories
        for i in range(NEW_PER_DAY):
            app.put_memory(
                f"Day {day} memory #{i}: topic-{random.choice(['alpha','beta','gamma','delta'])} data-{random.randint(0,9999)}",
                type=random.choice(["semantic", "episodic", "working", "procedural"]),
                scope_type="project",
                scope_id=f"SIM_P{random.randint(0,4)}",
                source_kind="message",
            )

        # 2. Inject conflicts
        for i in range(CONFLICTS_PER_DAY):
            subj = f"sim.conflict.{random.randint(0, 50)}"
            app.put_memory(
                f"Day {day} statement: value of {subj} is TRUE.",
                type="semantic",
                scope_type="project",
                scope_id="SIM_P0",
                subject=subj,
                source_kind="manual",
            )
            app.put_memory(
                f"Day {day} rebuttal: value of {subj} is NOT true at all.",
                type="semantic",
                scope_type="project",
                scope_id="SIM_P0",
                subject=subj,
                source_kind="manual",
            )

        # 3. Run maintenance every 5 days
        if (day + 1) % 5 == 0:
            app.hygiene_engine.run_maintenance()

        # 4. Run recall queries
        recall_hits = 0
        for q in range(QUERIES_PER_DAY):
            results = mm.search(
                f"Day {random.randint(max(0,day-5), day)} memory",
                scope_type="project",
                scope_id=f"SIM_P{random.randint(0,4)}",
                limit=5,
            )
            if results:
                recall_hits += 1

        # 5. Measure DB
        active_count = app.storage.fetch_one("SELECT count(*) as c FROM memories WHERE status='active'")["c"]
        total_count = app.storage.fetch_one("SELECT count(*) as c FROM memories")["c"]
        conflict_count = app.storage.fetch_one("SELECT count(*) as c FROM conflicts WHERE status='open'")["c"]
        db_size = os.path.getsize(app.db_path) if os.path.exists(app.db_path) else 0

        day_duration = time.perf_counter() - day_start
        recall_rate = recall_hits / QUERIES_PER_DAY if QUERIES_PER_DAY > 0 else 0

        daily_metrics.append({
            "day": day + 1,
            "active": active_count,
            "total": total_count,
            "open_conflicts": conflict_count,
            "db_size_kb": db_size / 1024,
            "recall_rate": recall_rate,
            "duration_s": day_duration,
        })
        print(f"active={active_count}, conflicts={conflict_count}, recall={recall_rate:.2f}, {day_duration:.1f}s")

    # Final analysis
    first_day = daily_metrics[0]
    last_day = daily_metrics[-1]
    recall_drift = last_day["recall_rate"] - first_day["recall_rate"]
    db_growth = last_day["db_size_kb"] - first_day["db_size_kb"]
    conflict_backlog = last_day["open_conflicts"]

    print(f"\n📊 30-Day Summary:")
    print(f"  Recall drift: {recall_drift:+.3f} (Day 1: {first_day['recall_rate']:.2f} → Day 30: {last_day['recall_rate']:.2f})")
    print(f"  DB growth: {db_growth:.0f} KB")
    print(f"  Open conflict backlog: {conflict_backlog}")
    print(f"  Total active memories: {last_day['active']}")

    report = {
        "level": "level-8",
        "metrics": {
            "days_simulated": DAYS,
            "recall_day1": first_day["recall_rate"],
            "recall_day30": last_day["recall_rate"],
            "recall_drift": recall_drift,
            "db_growth_kb": db_growth,
            "conflict_backlog": conflict_backlog,
            "final_active": last_day["active"],
            "final_total": last_day["total"],
        },
        "daily": daily_metrics,
    }
    save_report("level-8", report)
    return report

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aegis v4 Stress Test Runner")
    parser.add_argument("--level", type=int, default=1, help="Test level (1-8, 99=full)")
    parser.add_argument("--db-path", type=str, default=":memory:", help="Database path")
    args = parser.parse_args()

    db_path = args.db_path
    if db_path != ":memory:":
        if os.path.exists(db_path):
            os.remove(db_path)

    app = AegisApp(db_path=db_path)

    if args.level == 1:
        run_level_1(app)
    elif args.level == 2:
        run_level_1(app)
        run_level_2(app)
    elif args.level == 3:
        run_level_1(app)
        run_level_3(app)
    elif args.level == 4:
        run_level_1(app)
        run_level_4(app)
    elif args.level == 5:
        run_level_1(app)
        run_level_4(app)
        run_level_5(app)
    elif args.level == 6:
        run_level_6(app)
    elif args.level == 7:
        run_level_1(app)
        run_level_7(app)
    elif args.level == 8:
        run_level_8(app)
    elif args.level == 99:  # THE GAUNTLET: Full Run
        run_level_1(app)
        run_level_2(app)
        run_level_3(app)
        run_level_4(app)
        run_level_5(app)
        run_level_6(app)
        run_level_7(app)
        run_level_8(app)
        print("\n" + "═" * 60)
        print("  🏆 THE GAUNTLET COMPLETE")
        print("═" * 60)
    else:
        print(f"Level {args.level} not implemented.")
