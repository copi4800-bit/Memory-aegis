import unittest

from aegis_py.conflict.core import ConflictManager
from aegis_py.memory.core import MemoryManager
from aegis_py.memory.models import Memory
from aegis_py.retrieval.benchmark import (
    DEFAULT_THRESHOLDS,
    BenchmarkThresholds,
    QueryCase,
    evaluate_summary,
    render_gate_report,
    run_benchmark,
    run_payload_benchmark,
)
from aegis_py.storage.db import DatabaseManager


class RetrievalBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.db.initialize()
        self.manager = MemoryManager(self.db)
        self.conflicts = ConflictManager(self.db)

    def tearDown(self):
        self.db.close()

    def test_benchmark_summary_reports_quality_and_leakage_across_seeded_shapes(self):
        expected_storage = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Aegis uses SQLite FTS5 for local-first retrieval.",
                summary="SQLite FTS5 retrieval",
                subject="technical.storage",
                source_kind="manual",
                source_ref="spec",
            )
        )
        expected_benchmark = self.manager.store(
            Memory(
                id=None,
                type="procedural",
                scope_type="project",
                scope_id="aegis-v4",
                content="Run benchmark coverage after retrieval scoring changes.",
                summary="Benchmark retrieval workflow",
                subject="workflow.benchmark",
                source_kind="manual",
                source_ref="runbook",
            )
        )
        expected_punctuated = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The release gate is enabled for punctuation-safe retrieval.",
                summary="Release gate state",
                subject="release.gate",
                source_kind="manual",
                source_ref="release-doc",
            )
        )
        expected_neighbor = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Migration markers connect mammoth routes to drought-safe water corridors.",
                summary="Mammoth route neighbor",
                subject="mammoth.routes",
                source_kind="manual",
                source_ref="field-guide",
            )
        )
        expected_seed = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Mammoth route planning depends on remembering migration markers.",
                summary="Mammoth route seed",
                subject="mammoth.routes",
                source_kind="manual",
                source_ref="field-guide-seed",
            )
        )
        conflict_a = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The conflict scan runs before maintenance closeout.",
                summary="Conflict scan enabled",
                subject="workflow.conflict",
                source_kind="manual",
                source_ref="ops-doc",
            )
        )
        conflict_b = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The conflict scan does not run before maintenance closeout.",
                summary="Conflict scan disabled",
                subject="workflow.conflict",
                source_kind="manual",
                source_ref="ops-doc-alt",
            )
        )
        forbidden = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="other-project",
                content="Another project also runs benchmark coverage.",
                summary="Other benchmark workflow",
                subject="workflow.benchmark",
                source_kind="manual",
                source_ref="other-runbook",
            )
        )
        self.conflicts.scan_conflicts("workflow.conflict")

        summary = run_benchmark(
            self.manager,
            [
                QueryCase(
                    query="SQLite retrieval",
                    expected_ids=[expected_storage],
                    scope_type="project",
                    scope_id="aegis-v4",
                    forbidden_ids=[forbidden],
                ),
                QueryCase(
                    query="benchmark retrieval",
                    expected_ids=[expected_benchmark],
                    scope_type="project",
                    scope_id="aegis-v4",
                    forbidden_ids=[forbidden],
                ),
                QueryCase(
                    query="release-gate",
                    expected_ids=[expected_punctuated],
                    scope_type="project",
                    scope_id="aegis-v4",
                ),
                QueryCase(
                    query="migration markers",
                    expected_ids=[expected_seed, expected_neighbor],
                    scope_type="project",
                    scope_id="aegis-v4",
                ),
                QueryCase(
                    query="missing-term",
                    expected_ids=[],
                    scope_type="project",
                    scope_id="aegis-v4",
                ),
                QueryCase(
                    query="conflict scan",
                    expected_ids=[conflict_a, conflict_b],
                    expected_conflict_ids=[conflict_a, conflict_b],
                    scope_type="project",
                    scope_id="aegis-v4",
                ),
            ],
        )

        self.assertEqual(len(summary.queries), 6)
        self.assertGreaterEqual(summary.recall_at_1, 0.5)
        self.assertGreaterEqual(summary.recall_at_5, 1.0)
        self.assertGreaterEqual(summary.recall_at_k, 1.0)
        self.assertGreaterEqual(summary.hit_at_k, 1.0)
        self.assertGreaterEqual(summary.mrr_at_10, 0.5)
        self.assertGreaterEqual(summary.ndcg_at_10, 0.5)
        self.assertEqual(summary.scope_leakage, 0.0)
        self.assertEqual(summary.conflict_leakage, 0.0)
        self.assertGreaterEqual(summary.conflict_visibility, 0.2)
        self.assertEqual(summary.explain_completeness, 1.0)
        self.assertGreaterEqual(summary.latency_p50_ms, 0.0)
        self.assertGreaterEqual(summary.latency_p95_ms, summary.latency_p50_ms)

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
                conflict_visibility_min=0.2,
                latency_p95_ms_max=50.0,
            ),
        )
        self.assertTrue(gate.passed, gate.failures)
        self.assertEqual(gate.failures, [])

    def test_benchmark_gate_report_lists_metric_failures_with_observed_values(self):
        summary = run_benchmark(
            self.manager,
            [
                QueryCase(
                    query="missing-term",
                    expected_ids=["never-returned"],
                    scope_type="project",
                    scope_id="aegis-v4",
                )
            ],
        )

        gate = evaluate_summary(summary, DEFAULT_THRESHOLDS)

        self.assertFalse(gate.passed)
        self.assertTrue(any(failure.startswith("recall_at_1=") for failure in gate.failures))
        self.assertTrue(any(failure.startswith("hit_at_k=") for failure in gate.failures))
        self.assertIn("FAIL:", render_gate_report(gate))

    def test_payload_benchmark_distinguishes_fast_and_explain_modes(self):
        expected_storage = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Aegis uses SQLite FTS5 for local-first retrieval.",
                summary="SQLite FTS5 retrieval",
                subject="technical.storage",
                source_kind="manual",
                source_ref="spec",
            )
        )

        cases = [
            QueryCase(
                query="SQLite retrieval",
                expected_ids=[expected_storage],
                scope_type="project",
                scope_id="aegis-v4",
            )
        ]

        fast_summary = run_payload_benchmark(self.manager, cases, retrieval_mode="fast")
        explain_summary = run_payload_benchmark(self.manager, cases, retrieval_mode="explain")

        self.assertEqual(fast_summary.retrieval_mode, "fast")
        self.assertEqual(explain_summary.retrieval_mode, "explain")
        self.assertEqual(fast_summary.explain_completeness, 0.0)
        self.assertEqual(explain_summary.explain_completeness, 1.0)
        self.assertLess(fast_summary.payload_bytes_p95, explain_summary.payload_bytes_p95)

        fast_gate = evaluate_summary(
            fast_summary,
            BenchmarkThresholds(
                recall_at_1_min=0.5,
                recall_at_5_min=1.0,
                recall_at_k_min=1.0,
                hit_at_k_min=1.0,
                mrr_at_10_min=0.5,
                ndcg_at_10_min=0.5,
                scope_leakage_max=0.0,
                conflict_leakage_max=0.0,
                latency_p95_ms_max=50.0,
                payload_bytes_p95_max=400.0,
            ),
        )
        explain_gate = evaluate_summary(
            explain_summary,
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
                latency_p95_ms_max=50.0,
                payload_bytes_p95_max=800.0,
            ),
        )

        self.assertTrue(fast_gate.passed, fast_gate.failures)
        self.assertTrue(explain_gate.passed, explain_gate.failures)


if __name__ == "__main__":
    unittest.main()
