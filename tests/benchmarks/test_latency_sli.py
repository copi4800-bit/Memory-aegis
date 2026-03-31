from __future__ import annotations

from aegis_py.conflict.core import ConflictManager
from aegis_py.memory.core import MemoryManager
from aegis_py.memory.models import Memory
from aegis_py.retrieval.benchmark import BenchmarkThresholds, QueryCase, evaluate_summary, run_benchmark
from aegis_py.storage.db import DatabaseManager


def test_latency_and_trust_visibility_gate_for_python_runtime():
    db = DatabaseManager(":memory:")
    db.initialize()
    manager = MemoryManager(db)
    conflicts = ConflictManager(db)

    try:
        seed = manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="sli",
                content="Aegis keeps latency gates local-first and measurable.",
                summary="Latency gate baseline",
                subject="ops.latency",
                source_kind="manual",
                source_ref="sli-doc",
            )
        )
        neighbor = manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="sli",
                content="Latency gate baselines remain explainable under trust shaping.",
                summary="Trust shaping baseline",
                subject="ops.latency",
                source_kind="manual",
                source_ref="sli-doc-2",
            )
        )
        conflict_a = manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="sli",
                content="The production gate is currently enabled.",
                summary="Gate enabled",
                subject="ops.gate",
                source_kind="manual",
                source_ref="ops-a",
            )
        )
        conflict_b = manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="sli",
                content="The production gate is currently disabled.",
                summary="Gate disabled",
                subject="ops.gate",
                source_kind="manual",
                source_ref="ops-b",
            )
        )
        conflicts.scan_conflicts("ops.gate")

        summary = run_benchmark(
            manager,
            [
                QueryCase(
                    query="latency gate baseline",
                    expected_ids=[seed, neighbor],
                    scope_type="project",
                    scope_id="sli",
                ),
                QueryCase(
                    query="production gate",
                    expected_ids=[conflict_a, conflict_b],
                    expected_conflict_ids=[conflict_a, conflict_b],
                    scope_type="project",
                    scope_id="sli",
                ),
            ],
        )
        gate = evaluate_summary(
            summary,
            BenchmarkThresholds(
                recall_at_1_min=0.5,
                recall_at_5_min=1.0,
                recall_at_k_min=1.0,
                hit_at_k_min=1.0,
                mrr_at_10_min=0.5,
                ndcg_at_10_min=0.5,
                scope_leakage_max=0.0,
                conflict_leakage_max=0.0,
                explain_completeness_min=1.0,
                conflict_visibility_min=0.5,
                latency_p95_ms_max=50.0,
            ),
        )

        assert gate.passed, gate.failures
    finally:
        db.close()
