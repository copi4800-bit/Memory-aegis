from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_node_script(script: str, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=merged_env,
        check=False,
    )


def test_truthkeep_mcp_module_executes_main(tmp_path: Path) -> None:
    db_path = tmp_path / "adapter-smoke.db"
    env = os.environ.copy()
    env["AEGIS_DB_PATH"] = str(db_path)
    result = subprocess.run(
        [sys.executable, "-m", "truthkeep.mcp", "--startup-probe"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["backend"] == "python"
    assert payload["ready"] is True


def test_package_json_uses_native_openclaw_extension_entry() -> None:
    package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
    assert package_json["main"] == "./openclaw/truthkeep-memory.native.cjs"
    assert package_json["openclaw"]["extensions"] == ["./openclaw/truthkeep-memory.native.cjs"]
    assert package_json["openclaw"]["setupEntry"] == "./openclaw/truthkeep-memory.native.cjs"


def test_native_adapter_registers_memory_runtime() -> None:
    script = """
const plugin = require(\"./openclaw/truthkeep-memory.native.cjs\");
let registered = null;
plugin.register({
  registerMemoryRuntime(runtime) {
    registered = runtime;
  },
});
if (!registered) {
  throw new Error(\"memory runtime was not registered\");
}
const backend = registered.resolveMemoryBackendConfig({ cfg: {}, agentId: \"alpha\" });
console.log(JSON.stringify({ id: plugin.id, kind: plugin.kind, backend }));
"""
    result = _run_node_script(script)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["id"] == "truthkeep-memory"
    assert payload["kind"] == "memory"
    assert payload["backend"] == {"backend": "builtin"}


def test_native_adapter_runtime_returns_status_manager(tmp_path: Path) -> None:
    db_path = tmp_path / "native-adapter.db"
    script = """
const plugin = require(\"./openclaw/truthkeep-memory.native.cjs\");
let runtime = null;
plugin.register({
  registerMemoryRuntime(value) {
    runtime = value;
  },
});
(async () => {
  const outcome = await runtime.getMemorySearchManager({ cfg: {}, agentId: \"agent-native\", purpose: \"status\" });
  if (!outcome.manager) {
    throw new Error(outcome.error || \"missing manager\");
  }
  const status = outcome.manager.status();
  const embedding = await outcome.manager.probeEmbeddingAvailability();
  const vector = await outcome.manager.probeVectorAvailability();
  console.log(JSON.stringify({ status, embedding, vector }));
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""
    result = _run_node_script(
        script,
        env={
            "TRUTHKEEP_PYTHON": sys.executable,
            "AEGIS_DB_PATH": str(db_path),
        },
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    status = payload["status"]
    assert status["backend"] == "builtin"
    assert status["provider"] == "truthkeep-memory"
    assert status["fts"] is True
    assert status["vector"] is False
    assert status["dbPath"] == str(db_path)
    assert status["custom"]["ready"] is True
    assert payload["embedding"]["ok"] is False
    assert payload["vector"] is False
