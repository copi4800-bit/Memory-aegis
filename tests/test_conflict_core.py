import unittest

from aegis_py.conflict.core import ConflictManager
from aegis_py.memory.core import MemoryManager
from aegis_py.memory.models import Memory
from aegis_py.storage.db import DatabaseManager


class ConflictManagerTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.db.initialize()
        self.memory = MemoryManager(self.db)
        self.conflicts = ConflictManager(self.db)

    def tearDown(self):
        self.db.close()

    def test_scan_conflicts_logs_once_and_preserves_active_status(self):
        self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The deployment flag is enabled for project aegis.",
                subject="deploy.flag",
                source_kind="manual",
            )
        )
        self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The deployment flag is not enabled for project aegis.",
                subject="deploy.flag",
                source_kind="manual",
            )
        )

        first = self.conflicts.scan_conflicts("deploy.flag")
        second = self.conflicts.scan_conflicts("deploy.flag")

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)
        row = self.db.fetch_one("SELECT COUNT(*) AS count FROM conflicts", ())
        assert row is not None
        self.assertEqual(row["count"], 1)

    def test_auto_resolve_suggests_for_ambiguous_pairs(self):
        id_a = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The feature is enabled for the release.",
                subject="release.toggle",
                source_kind="manual",
                activation_score=1.1,
            )
        )
        id_b = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The feature is not enabled for the release.",
                subject="release.toggle",
                source_kind="manual",
                activation_score=1.0,
            )
        )

        self.conflicts.scan_conflicts("release.toggle")
        conflict = self.db.fetch_one("SELECT id, status FROM conflicts LIMIT 1", ())
        assert conflict is not None

        resolved = self.conflicts.auto_resolve(conflict["id"])
        self.assertTrue(resolved)

        conflict_after = self.db.fetch_one("SELECT status, resolution FROM conflicts WHERE id = ?", (conflict["id"],))
        assert conflict_after is not None
        self.assertEqual(conflict_after["status"], "suggested")
        self.assertEqual(conflict_after["resolution"], "user_resolution_required")

        prompt = self.conflicts.get_resolution_prompt(conflict["id"])
        assert prompt is not None
        self.assertEqual(prompt["classification"], "user_resolution_required")
        self.assertEqual(prompt["recommended_action"], "keep_newer")
        self.assertEqual(prompt["memories"]["older"]["id"], id_a)
        self.assertEqual(prompt["memories"]["newer"]["id"], id_b)

        memories = self.db.fetch_all("SELECT id, status FROM memories WHERE id IN (?, ?)", (id_a, id_b))
        self.assertEqual({row["status"] for row in memories}, {"active"})

    def test_auto_resolve_supersedes_lower_signal_memory_with_trace(self):
        id_a = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The rollout is enabled for the project.",
                subject="rollout.state",
                source_kind="manual",
                activation_score=2.0,
            )
        )
        id_b = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The rollout is not enabled for the project.",
                subject="rollout.state",
                source_kind="manual",
                activation_score=1.0,
            )
        )

        self.conflicts.scan_conflicts("rollout.state")
        conflict = self.db.fetch_one("SELECT id FROM conflicts LIMIT 1", ())
        assert conflict is not None

        resolved = self.conflicts.auto_resolve(conflict["id"])
        self.assertTrue(resolved)

        loser = self.db.fetch_one("SELECT status, metadata_json FROM memories WHERE id = ?", (id_b,))
        assert loser is not None
        self.assertEqual(loser["status"], "superseded")
        self.assertIn("superseded_by_conflict", loser["metadata_json"])

    def test_user_resolution_can_keep_both_as_exception_with_audit_trace(self):
        id_a = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The review cadence is weekly for this project.",
                subject="review.cadence",
                source_kind="manual",
                activation_score=1.0,
            )
        )
        id_b = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="The review cadence is not weekly for this project.",
                subject="review.cadence",
                source_kind="manual",
                activation_score=1.0,
            )
        )

        self.conflicts.scan_conflicts("review.cadence")
        conflict = self.db.fetch_one("SELECT id FROM conflicts LIMIT 1", ())
        assert conflict is not None
        self.conflicts.auto_resolve(conflict["id"])

        result = self.conflicts.resolve_with_user_decision(
            conflict["id"],
            action="mark_exception",
            rationale="Both statements are valid for different operating conditions.",
        )

        self.assertEqual(result["resolution"], "resolved_by_user_exception")
        states = self.db.fetch_all("SELECT id, status, metadata_json FROM memories WHERE id IN (?, ?)", (id_a, id_b))
        self.assertEqual({row["status"] for row in states}, {"active"})
        self.assertTrue(all("exception_confirmed_by_user" in row["metadata_json"] for row in states))


if __name__ == "__main__":
    unittest.main()
