import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path("/home/hali/.openclaw/extensions/memory-aegis-v7")


class ReleaseWorkflowTests(unittest.TestCase):
    def test_python_ci_workflow_runs_canonical_validation_command(self):
        workflow = (REPO_ROOT / ".github/workflows/aegis-python-validation.yml").read_text(encoding="utf-8")

        self.assertIn("actions/setup-python", workflow)
        self.assertIn("python-version: \"3.13\"", workflow)
        self.assertIn("python -m pip install -r requirements.txt", workflow)
        self.assertIn("python -m pytest -q tests", workflow)

    def test_release_packaging_script_creates_python_bundle(self):
        output_dir = Path(tempfile.mkdtemp(prefix="aegis-release-"))
        script = REPO_ROOT / "scripts/release-python-package.sh"

        subprocess.run([str(script), str(output_dir)], check=True, cwd=REPO_ROOT)

        bundle = output_dir / "aegis-python-vnext.tar.gz"
        self.assertTrue(bundle.exists())

        with tarfile.open(bundle, "r:gz") as archive:
            names = archive.getnames()

        self.assertIn("aegis-python-vnext/README.md", names)
        self.assertIn("aegis-python-vnext/requirements.txt", names)
        self.assertIn("aegis-python-vnext/openclaw.plugin.json", names)
        self.assertIn("aegis-python-vnext/bin/aegis-setup", names)
        self.assertIn("aegis-python-vnext/scripts/demo_first_memory.py", names)
        self.assertIn("aegis-python-vnext/scripts/demo_integration_boundary.py", names)
        self.assertIn("aegis-python-vnext/scripts/demo_grounded_recall.py", names)
        self.assertIn("aegis-python-vnext/RELEASE_NOTES.txt", names)
        self.assertIn("aegis-python-vnext/QUICKSTART.txt", names)
        self.assertTrue(any(name.startswith("aegis-python-vnext/aegis_py/") for name in names))


if __name__ == "__main__":
    unittest.main()
