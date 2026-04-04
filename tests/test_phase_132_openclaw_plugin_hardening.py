from __future__ import annotations

import json
from pathlib import Path

from truthkeep import install_check as truthkeep_install_check
from truthkeep import mcp as truthkeep_mcp
from truthkeep import setup as truthkeep_setup


def test_truthkeep_public_entry_modules_expose_main():
    assert callable(truthkeep_install_check.main)
    assert callable(truthkeep_mcp.main)
    assert callable(truthkeep_setup.main)


def test_pyproject_exposes_truthkeep_plugin_commands():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'truthkeep-mcp = "truthkeep.mcp:main"' in pyproject
    assert 'truthkeep-check = "truthkeep.install_check:main"' in pyproject
    assert 'truthkeep-setup = "truthkeep.setup:main"' in pyproject
    assert 'aegis-setup = "truthkeep.setup:main"' in pyproject


def test_package_json_declares_openclaw_extension_and_bins():
    package_json = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package_json["bin"]["truthkeep-setup"] == "./bin/truthkeep-setup"
    assert package_json["bin"]["truthkeep-check"] == "./bin/truthkeep-check"
    assert package_json["bin"]["truthkeep-mcp"] == "./bin/truthkeep-mcp"

    extensions = package_json["openclaw"]["extensions"]
    assert extensions == ["./openclaw/truthkeep-memory.native.cjs"]
    assert package_json["openclaw"]["setupEntry"] == "./openclaw/truthkeep-memory.native.cjs"
    assert package_json["main"] == "./openclaw/truthkeep-memory.native.cjs"


def test_manifest_onboarding_command_has_real_bin_wrapper():
    manifest = json.loads(Path("openclaw.plugin.json").read_text(encoding="utf-8"))
    onboarding = manifest["consumerSurface"]["onboardingCommand"]

    assert onboarding == "truthkeep-setup"
    assert Path("bin", onboarding).exists()


def test_readme_and_quickstart_reference_real_public_plugin_commands():
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("QUICKSTART.md").read_text(encoding="utf-8")

    assert "truthkeep-mcp" in readme
    assert "truthkeep-setup" in readme
    assert "truthkeep-check" in readme
    assert "truthkeep-mcp" in quickstart
    assert "truthkeep-setup" in quickstart
    assert "truthkeep-check" in quickstart
