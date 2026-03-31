import unittest
from pathlib import Path


REPO_ROOT = Path("/home/hali/.openclaw/extensions/memory-aegis-v7")


class MigrationPlanTests(unittest.TestCase):
    def test_ts_python_adapter_plan_records_completed_python_owned_parity(self):
        plan = (REPO_ROOT / "specs/004-ts-python-adapter/plan.md").read_text(encoding="utf-8")

        self.assertIn("route `memory_search` to the Python engine first", plan)
        self.assertIn("| `memory_search` | Yes | Yes | Yes | Python-backed adapter implemented |", plan)
        self.assertIn("| `memory_get` | Yes | Yes | Yes | Python-backed adapter implemented |", plan)
        self.assertIn("| `memory_backup_preview` | Yes | Yes | Yes | Python-backed adapter implemented |", plan)
        self.assertIn("| `memory_doctor` | Yes | Yes | Yes | Python-backed adapter implemented |", plan)

    def test_readme_states_ts_shell_python_backend_migration_stance(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("keep the TypeScript OpenClaw plugin shell as the adapter surface", readme)
        self.assertIn("treat the Python engine as the canonical local memory backend", readme)
        self.assertIn("specs/004-ts-python-adapter", readme)


if __name__ == "__main__":
    unittest.main()
