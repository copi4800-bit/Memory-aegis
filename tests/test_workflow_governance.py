import unittest
from pathlib import Path


REPO_ROOT = Path("/home/hali/.openclaw/extensions/memory-aegis-v7")


class WorkflowGovernanceTests(unittest.TestCase):
    def test_repo_documents_gsd_plus_spec_kit_contract(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        claude = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        constitution = (REPO_ROOT / ".specify/memory/constitution.md").read_text(encoding="utf-8")
        codex_config = (REPO_ROOT / ".codex/config.toml").read_text(encoding="utf-8")

        self.assertIn("GSD + Spec Kit", readme)
        self.assertIn("Spec Kit", claude)
        self.assertIn("GSD", claude)
        self.assertIn("specs/*", claude)
        self.assertIn("check the active feature in `specs/*`", readme)
        self.assertIn("Check the active feature in `specs/*`", claude)
        self.assertIn("[agents.gsd-planner]", codex_config)
        self.assertIn("[agents.gsd-executor]", codex_config)
        self.assertIn("GSD + Spec Kit Delivery", constitution)

    def test_planning_artifacts_are_marked_as_coordination_only(self):
        state = (REPO_ROOT / ".planning/STATE.md").read_text(encoding="utf-8")
        conventions = (REPO_ROOT / ".planning/codebase/CONVENTIONS.md").read_text(encoding="utf-8")

        self.assertIn("coordination layer", state)
        self.assertIn("specs/*", conventions)
        self.assertIn("orchestration layer only", conventions)


if __name__ == "__main__":
    unittest.main()
