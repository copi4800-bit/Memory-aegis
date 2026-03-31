import unittest

from aegis_py.conflict.core import ConflictManager
from aegis_py.memory.core import MemoryManager
from aegis_py.memory.models import Memory
from aegis_py.storage.db import DatabaseManager


class MemoryCoreTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.db.initialize()
        self.manager = MemoryManager(self.db)
        self.conflicts = ConflictManager(self.db)

    def tearDown(self):
        self.db.close()

    def test_store_and_fetch_memory(self):
        memory_id = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Aegis uses SQLite FTS5 for local-first retrieval.",
                summary="SQLite retrieval",
                subject="technical.storage",
                source_kind="manual",
                source_ref="spec",
            )
        )
        memory = self.manager.get_by_id(memory_id)
        self.assertIsNotNone(memory)
        assert memory is not None
        self.assertEqual(memory.scope_type, "project")
        self.assertEqual(memory.source_kind, "manual")
        self.assertEqual(memory.subject, "technical.storage")

    def test_search_returns_explainable_results(self):
        self.manager.store(
            Memory(
                id=None,
                type="procedural",
                scope_type="project",
                scope_id="aegis-v4",
                content="Run benchmark coverage after changing retrieval scoring.",
                summary="Retrieval benchmark rule",
                subject="workflow.benchmark",
                source_kind="manual",
                source_ref="runbook",
            )
        )
        results = self.manager.search("benchmark retrieval", scope_type="project", scope_id="aegis-v4", limit=5)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertGreater(result.score, 0)
        self.assertEqual(result.scope_id, "aegis-v4")
        self.assertEqual(result.source_kind, "manual")
        self.assertIn("scope_exact_match", result.reasons)
        self.assertIn("procedural_bonus", result.reasons)

    def test_memory_core_can_read_linked_evidence(self):
        memory_id = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Evidence helpers should resolve raw content.",
                summary="Evidence helper",
                subject="technical.evidence",
                source_kind="manual",
                source_ref="spec#evidence",
            )
        )

        evidence = self.manager.get_evidence(memory_id)

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["memory_id"], memory_id)
        self.assertEqual(evidence[0]["source_ref"], "spec#evidence")
        self.assertEqual(evidence[0]["raw_content"], "Evidence helpers should resolve raw content.")

    def test_scope_filter_blocks_cross_scope_leakage(self):
        self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Conflict scan belongs to Aegis maintenance.",
                summary="Aegis conflict scan",
                subject="workflow.conflict",
                source_kind="manual",
                source_ref="aegis-doc",
            )
        )
        self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="other-project",
                content="Conflict scan belongs to another project.",
                summary="Other conflict scan",
                subject="workflow.conflict",
                source_kind="manual",
                source_ref="other-doc",
            )
        )
        results = self.manager.search("conflict scan", scope_type="project", scope_id="aegis-v4", limit=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].scope_id, "aegis-v4")

    def test_search_marks_conflict_visibility_in_result_contract(self):
        self.manager.store(
            Memory(
                id=None,
                type="episodic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The rollout gate is enabled for aegis.",
                subject="rollout.gate",
                source_kind="manual",
            )
        )
        self.manager.store(
            Memory(
                id=None,
                type="episodic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The rollout gate is not enabled for aegis.",
                subject="rollout.gate",
                source_kind="manual",
            )
        )
        self.conflicts.scan_conflicts("rollout.gate")

        results = self.manager.search("rollout gate", scope_type="project", scope_id="aegis-v4", limit=5)

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.conflict_status == "open" for result in results))
        self.assertTrue(all("conflict_visible" in result.reasons for result in results))
        self.assertIn("Conflict visible.", results[0].reason)

    def test_search_excludes_non_active_statuses_from_visibility(self):
        self.manager.store(
            Memory(
                id="active-memory",
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The active memory should remain searchable.",
                subject="visibility.active",
                source_kind="manual",
                status="active",
            )
        )
        for memory_id, status in [
            ("archived-memory", "archived"),
            ("expired-memory", "expired"),
            ("superseded-memory", "superseded"),
            ("conflict-candidate-memory", "conflict_candidate"),
        ]:
            self.manager.store(
                Memory(
                    id=memory_id,
                    type="semantic",
                    scope_type="project",
                    scope_id="aegis-v4",
                    content=f"The {status} memory should not be returned.",
                    subject="visibility.filtered",
                    source_kind="manual",
                    status=status,
                )
            )

        results = self.manager.search("memory", scope_type="project", scope_id="aegis-v4", limit=10)

        self.assertEqual([result.id for result in results], ["active-memory"])


if __name__ == "__main__":
    unittest.main()
