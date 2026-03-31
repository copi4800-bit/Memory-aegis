import unittest

from aegis_py.evolve.core import EvolveEngine
from aegis_py.memory.core import MemoryManager
from aegis_py.memory.models import Memory
from aegis_py.storage.db import DatabaseManager


class MemoryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.db.initialize()
        self.manager = MemoryManager(self.db)
        self.evolve = EvolveEngine(self.db)

    def tearDown(self):
        self.db.close()

    def test_session_conclusion_demotes_high_signal_working_memory(self):
        memory_id = self.manager.store(
            Memory(
                id=None,
                type="working",
                scope_type="session",
                scope_id="sess-1",
                session_id="sess-1",
                content="Remember to preserve this session insight.",
                source_kind="message",
                source_ref="msg-1",
                activation_score=1.4,
            )
        )
        summary = self.manager.conclude_session("sess-1", archive_threshold=1.2)
        self.assertEqual(summary["demoted"], 1)
        memory = self.manager.get_by_id(memory_id)
        assert memory is not None
        self.assertEqual(memory.status, "archived")
        self.assertEqual(memory.metadata["lifecycle_events"][-1]["event"], "demoted_from_working_memory")

    def test_session_conclusion_expires_low_signal_working_memory(self):
        memory_id = self.manager.store(
            Memory(
                id=None,
                type="working",
                scope_type="session",
                scope_id="sess-2",
                session_id="sess-2",
                content="Temporary scratch note.",
                source_kind="message",
                source_ref="msg-2",
                activation_score=0.8,
            )
        )
        summary = self.manager.conclude_session("sess-2", archive_threshold=1.2)
        self.assertEqual(summary["expired"], 1)
        memory = self.manager.get_by_id(memory_id)
        assert memory is not None
        self.assertEqual(memory.status, "expired")
        self.assertEqual(memory.metadata["lifecycle_events"][-1]["event"], "expired_on_session_end")

    def test_reinforce_increases_activation_and_access_count(self):
        memory_id = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Reinforcement should increase activation.",
                source_kind="manual",
                source_ref="spec",
                activation_score=1.0,
            )
        )
        self.evolve.reinforce(memory_id)
        row = self.db.fetch_one("SELECT activation_score, access_count FROM memories WHERE id = ?", (memory_id,))
        assert row is not None
        self.assertGreater(row["activation_score"], 1.0)
        self.assertEqual(row["access_count"], 1)

    def test_decay_and_hygiene_archive_then_expire_memories(self):
        archive_id = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="This memory should cool down into archive.",
                source_kind="manual",
                source_ref="spec",
                activation_score=0.35,
            )
        )
        expire_id = self.manager.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="This memory should expire after stronger decay.",
                source_kind="manual",
                source_ref="spec",
                activation_score=0.15,
            )
        )
        self.evolve.apply_decay(2)
        self.evolve.run_hygiene()

        archive_row = self.db.fetch_one("SELECT status FROM memories WHERE id = ?", (archive_id,))
        expire_row = self.db.fetch_one("SELECT status FROM memories WHERE id = ?", (expire_id,))
        assert archive_row is not None and expire_row is not None
        self.assertEqual(archive_row["status"], "archived")
        self.assertEqual(expire_row["status"], "expired")

        archive_memory = self.manager.get_by_id(archive_id)
        expire_memory = self.manager.get_by_id(expire_id)
        assert archive_memory is not None and expire_memory is not None
        self.assertEqual(archive_memory.metadata["lifecycle_events"][-1]["event"], "archived_by_hygiene")
        self.assertEqual(expire_memory.metadata["lifecycle_events"][-1]["event"], "expired_by_hygiene")


if __name__ == "__main__":
    unittest.main()
