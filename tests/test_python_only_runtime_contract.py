import json
import re
from pathlib import Path

from aegis_py.mcp.server import AegisMCPServer
from aegis_py.surface import ADVANCED_OPERATIONS, DEFAULT_OPERATIONS
from aegis_py.tool_registry import TOOL_REGISTRY, adapter_tool_targets, host_bridge_for_tool, registry_tool_names

REPO_ROOT = Path("/home/hali/.openclaw/extensions/memory-aegis-v7")


def test_package_json_marks_python_artifacts_as_shippable_contract():
    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))

    assert "aegis_py" in package_json["files"]
    assert "bin" in package_json["files"]
    assert "requirements.txt" in package_json["files"]
    assert "scripts/demo_first_memory.py" in package_json["files"]
    assert "scripts/demo_integration_boundary.py" in package_json["files"]
    assert "scripts/demo_grounded_recall.py" in package_json["files"]
    assert "src" not in package_json["files"]

    assert "test:python" in package_json["scripts"]
    assert "package:python" in package_json["scripts"]
    assert package_json["openclaw"]["extensions"] == ["./dist/index.js"]


def test_python_only_manifest_matches_bootstrap_tool_surface():
    manifest = json.loads((REPO_ROOT / "openclaw.plugin.json").read_text(encoding="utf-8"))
    tool_names = {tool["name"] for tool in manifest["tools"]}

    assert "memory_search" in tool_names
    assert "memory_store" in tool_names
    assert "memory_stats" in tool_names
    assert "memory_setup" in tool_names
    assert "memory_clean" in tool_names
    assert "memory_profile" in tool_names

    assert "memory_backup_upload" in tool_names
    assert "memory_backup_download" in tool_names
    assert "memory_rebuild" in tool_names
    assert "memory_scan" in tool_names
    assert "memory_visualize" in tool_names
    assert "memory_taxonomy_clean" in tool_names
    assert "memory_doctor" in tool_names

    assert manifest["healthContract"]["states"] == ["HEALTHY", "DEGRADED_SYNC", "BROKEN"]
    assert "optional_sync" in manifest["healthContract"]["capabilities"]
    assert manifest["healthContract"]["tools"] == ["memory_stats", "memory_doctor", "memory_surface"]
    assert manifest["consumerSurface"]["defaultTools"] == DEFAULT_OPERATIONS
    assert manifest["consumerSurface"]["advancedTools"] == ADVANCED_OPERATIONS
    assert manifest["consumerSurface"]["onboardingCommand"] == "aegis-setup"
    assert manifest["consumerSurface"]["onboardingRuntime"] == "python"

    setup_prompt = next(skill["prompt"] for skill in manifest["skills"] if skill["name"] == "memory-setup")
    assert "Python-first setup flow" in setup_prompt


def test_runtime_tool_registry_is_fully_shipped_in_plugin_manifest():
    manifest = json.loads((REPO_ROOT / "openclaw.plugin.json").read_text(encoding="utf-8"))
    tool_names = {tool["name"] for tool in manifest["tools"]}

    assert set(registry_tool_names()).issubset(tool_names)
    assert len(TOOL_REGISTRY) >= len(DEFAULT_OPERATIONS)
    assert len(TOOL_REGISTRY) >= len(ADVANCED_OPERATIONS)


def test_mcp_registry_surface_round_trips_runtime_registry():
    server = AegisMCPServer(db_path=":memory:")
    try:
        payload = json.loads(server.memory_registry())
    finally:
        server.close()

    assert payload["backend"] == "python"
    assert payload["tools"] == TOOL_REGISTRY


def test_index_tool_registrations_match_runtime_registry_without_extra_public_tools():
    index_ts = (REPO_ROOT / "index.ts").read_text(encoding="utf-8")
    published_names = set(re.findall(r'name:\s+"(memory_[a-z_]+)"', index_ts))

    assert published_names == set(registry_tool_names())


def test_python_adapter_covers_registry_bridge_targets_and_setup_cli_path():
    adapter_ts = (REPO_ROOT / "src" / "python-adapter.ts").read_text(encoding="utf-8")
    adapter_tool_names = set(re.findall(r'tool:\s+"(memory_[a-z_]+)"', adapter_ts))

    assert set(adapter_tool_targets()).issubset(adapter_tool_names)
    assert host_bridge_for_tool("memory_stats") == "tool:memory_status"
    assert '"memory_status"' in adapter_ts
    assert host_bridge_for_tool("memory_setup") == "cli:onboarding"
    assert 'command: "onboarding"' in adapter_ts


def test_setup_cli_is_a_python_bootstrap_not_a_typescript_engine_entry():
    setup_cli = (REPO_ROOT / "src" / "cli" / "setup.ts").read_text(encoding="utf-8")

    assert '"-m", "aegis_py.cli"' in setup_cli
    assert '"onboarding"' in setup_cli
    assert "AegisMemoryManager" not in setup_cli
    assert "Running Python onboarding checks" in setup_cli


def test_typescript_onboarding_module_is_an_explicit_legacy_stub():
    onboarding_ts = (REPO_ROOT / "src" / "ux" / "onboarding.ts").read_text(encoding="utf-8")

    assert "Legacy compatibility stub" in onboarding_ts
    assert "TypeScript onboarding has been retired" in onboarding_ts
    assert "python -m aegis_py.cli onboarding" in onboarding_ts


def test_typescript_hook_modules_are_explicit_legacy_stubs():
    message_hook = (REPO_ROOT / "src" / "hooks" / "message-hook.ts").read_text(encoding="utf-8")
    session_hook = (REPO_ROOT / "src" / "hooks" / "session-hook.ts").read_text(encoding="utf-8")
    tool_hook = (REPO_ROOT / "src" / "hooks" / "tool-hook.ts").read_text(encoding="utf-8")

    assert "Legacy compatibility stub" in message_hook
    assert "TypeScript message hooks have been retired" in message_hook
    assert "Legacy compatibility stub" in session_hook
    assert "TypeScript session hooks have been retired" in session_hook
    assert "Legacy compatibility stub" in tool_hook
    assert "TypeScript tool hooks have been retired" in tool_hook


def test_readme_publishes_use_both_quickstart():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "If you want both the Python runtime and the current OpenClaw plugin/bootstrap path" in readme
    assert "python3 -m venv .venv" in readme
    assert ".venv/bin/python -m pip install -r requirements.txt" in readme
    assert "npm install" in readme
    assert "python3 ./bin/aegis-setup" in readme


def test_readme_publishes_release_bundle_story():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Release Packaging" in readme
    assert "- `bin/aegis-setup`" in readme
    assert "- `scripts/demo_first_memory.py`" in readme
    assert "- `scripts/demo_integration_boundary.py`" in readme
    assert "- `scripts/demo_grounded_recall.py`" in readme
    assert "- `openclaw.plugin.json`" in readme
    assert "- `QUICKSTART.txt`" in readme
    assert "The release bundle is now meant to be unpack-and-try friendly" in readme
    assert "- run `bin/aegis-setup`" in readme
    assert "- run `scripts/demo_first_memory.py`" in readme
    assert "- run `scripts/demo_integration_boundary.py`" in readme
    assert "- run `scripts/demo_grounded_recall.py`" in readme


def test_readme_publishes_integration_quickstart_story():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Integration Quickstart" in readme
    assert "python -m aegis_py.mcp.server --service-info" in readme
    assert "python -m aegis_py.mcp.server --startup-probe" in readme
    assert 'python -m aegis_py.mcp.server --tool memory_setup --args-json' in readme
    assert 'python -m aegis_py.mcp.server --tool memory_recall --args-json' in readme
    assert "- inspect `--service-info`" in readme
    assert "- gate on `--startup-probe`" in readme
    assert "- call `--tool <name> --args-json" in readme
    assert ".venv/bin/python scripts/demo_integration_boundary.py" in readme


def test_readme_publishes_grounding_story():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Why You Can Trust A Recall" in readme
    assert "`provenance`" in readme
    assert "`reasons`" in readme
    assert "`trust_state` and `trust_reason`" in readme
    assert "`context-pack` evidence" in readme
    assert ".venv/bin/python scripts/demo_grounded_recall.py" in readme
    assert "- a memory is stored with explicit provenance" in readme
    assert "- explain-mode search returns provenance and ranking reasons" in readme
    assert "- trust is shown explicitly instead of being implied" in readme


def test_readme_publishes_five_minute_first_memory_path():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## 5-Minute First Memory" in readme
    assert '- run `aegis-setup`' in readme
    assert '- use `remember`' in readme
    assert '- use `recall`' in readme
    assert "You do not need backup, sync, graph, rebuild, or conflict tools to reach first value." in readme
    assert 'aegis_py.cli remember "My favorite drink is jasmine tea."' in readme
    assert 'aegis_py.cli recall "What is my favorite drink?"' in readme


def test_readme_publishes_product_storytelling_sections():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Product Overview" in readme
    assert "## Why Aegis" in readme
    assert "## What Makes It Different" in readme
    assert "## Non-Goals" in readme
    assert "scope isolation is a product feature" in readme
    assert "conflict-aware retrieval is visible" in readme
    assert "local-first control remains the default" in readme
    assert "- a managed-only cloud dependency" in readme


def test_readme_publishes_demo_and_benchmark_story():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Demo Path" in readme
    assert ".venv/bin/python scripts/demo_first_memory.py" in readme
    assert "- setup succeeds" in readme
    assert "- a memory is stored" in readme
    assert "- the same memory is recalled" in readme
    assert "- the runtime stays healthy afterward" in readme
    assert "It is the easiest script to point at when someone asks" in readme
    assert "## Benchmark Snapshot" in readme
    assert "grounded retrieval" in readme
    assert "visible trust and conflict handling" in readme
    assert "Recall@1" in readme
    assert "scope leakage" in readme
    assert "latency p95" in readme
    assert "scripts/benchmark_dragonfly.ts" in readme
    assert "scripts/benchmark_weaver.ts" in readme


def test_readme_and_adapter_publish_local_service_boundary():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    adapter = (REPO_ROOT / "src" / "python-adapter.ts").read_text(encoding="utf-8")

    assert "local sidecar/service boundary" in readme
    assert "--service-info" in readme
    assert "--startup-probe" in readme
    assert "serviceInfoViaPython" in adapter
    assert "startupProbeViaPython" in adapter


def test_agent_skills_match_current_python_owned_default_surface():
    skills_root = Path("/home/hali/.openclaw/skills")

    remember = (skills_root / "remember" / "SKILL.md").read_text(encoding="utf-8")
    recall = (skills_root / "recall" / "SKILL.md").read_text(encoding="utf-8")
    status = (skills_root / "memory-status" / "SKILL.md").read_text(encoding="utf-8")
    clean = (skills_root / "memory-clean" / "SKILL.md").read_text(encoding="utf-8")
    backup = (skills_root / "memory-backup" / "SKILL.md").read_text(encoding="utf-8")
    profile = (skills_root / "memory-profile" / "SKILL.md").read_text(encoding="utf-8")
    setup = (skills_root / "memory-setup" / "SKILL.md").read_text(encoding="utf-8")

    assert "memory_remember" in remember
    assert "memory_recall" in recall
    assert "memory_stats()" in status
    assert "memory_doctor()" in status
    assert "memory_clean()" in clean
    assert "memory_backup_upload(mode=\"snapshot\")" in backup
    assert "memory_profile()" in profile
    assert "memory_setup()" in setup
