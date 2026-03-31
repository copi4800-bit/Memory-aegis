import unittest

from aegis_py.hygiene.engine import HygieneEngine
from aegis_py.memory.core import MemoryManager
from aegis_py.memory.models import Memory
from aegis_py.storage.manager import StorageManager


class HygieneEngineTests(unittest.TestCase):
    def setUp(self):
        self.storage = StorageManager(":memory:")
        self.hygiene = HygieneEngine(self.storage)
        self.memory = MemoryManager(self.storage)

    def tearDown(self):
        self.storage.close()

    def test_on_session_end_only_archives_working_memory(self):
        working_id = self.memory.store(
            Memory(
                id=None,
                type="working",
                scope_type="session",
                scope_id="sess-1",
                session_id="sess-1",
                content="Current task progress",
                source_kind="message",
            )
        )
        episodic_id = self.memory.store(
            Memory(
                id=None,
                type="episodic",
                scope_type="session",
                scope_id="sess-1",
                session_id="sess-1",
                content="Permanent session fact",
                source_kind="message",
            )
        )

        self.hygiene.on_session_end("sess-1")

        working = self.storage.get_memory(working_id)
        episodic = self.storage.get_memory(episodic_id)
        assert working is not None and episodic is not None
        self.assertEqual(working.status, "archived")
        self.assertEqual(episodic.status, "active")
        self.assertEqual(working.metadata["lifecycle_events"][-1]["event"], "archived_on_session_end")
        self.assertFalse(episodic.metadata.get("lifecycle_events"))

    def test_run_maintenance_is_non_destructive_for_high_signal_memory(self):
        memory_id = self.memory.store(
            Memory(
                id=None,
                type="semantic",
                scope_type="project",
                scope_id="aegis-v4",
                content="Keep this durable fact active.",
                source_kind="manual",
                activation_score=1.5,
            )
        )

        self.hygiene.run_maintenance(half_life_days=30.0)

        memory = self.storage.get_memory(memory_id)
        assert memory is not None
        self.assertEqual(memory.status, "active")


if __name__ == "__main__":
    unittest.main()
