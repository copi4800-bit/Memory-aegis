#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "mcp" / "server.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


def run_server_flag(
    server_module: Path,
    *,
    env: dict[str, str],
    workspace_dir: Path,
    flag: str | None = None,
    tool: str | None = None,
    args: dict[str, object] | None = None,
) -> str:
    command = [sys.executable, str(server_module), "--workspace-dir", str(workspace_dir)]
    if flag is not None:
        command.append(flag)
    if tool is not None:
        command.extend(["--tool", tool, "--args-json", json.dumps(args or {})])

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return completed.stdout.strip()


def main() -> int:
    repo_root = resolve_repo_root()
    server_module = repo_root / "aegis_py" / "mcp" / "server.py"

    with tempfile.TemporaryDirectory(prefix="aegis_integration_demo_") as tmp:
        workspace_dir = Path(tmp)
        db_path = workspace_dir / ".aegis_py" / "integration_demo.db"
        env = {
            **os.environ,
            "PYTHONPATH": str(repo_root),
            "AEGIS_DB_PATH": str(db_path),
        }

        service_info = json.loads(
            run_server_flag(
                server_module,
                env=env,
                workspace_dir=workspace_dir,
                flag="--service-info",
            )
        )
        startup_probe = json.loads(
            run_server_flag(
                server_module,
                env=env,
                workspace_dir=workspace_dir,
                flag="--startup-probe",
            )
        )
        setup = json.loads(
            run_server_flag(
                server_module,
                env=env,
                workspace_dir=workspace_dir,
                tool="memory_setup",
            )
        )
        remember = run_server_flag(
            server_module,
            env=env,
            workspace_dir=workspace_dir,
            tool="memory_remember",
            args={"content": "My laptop bag is navy blue."},
        )
        recall = run_server_flag(
            server_module,
            env=env,
            workspace_dir=workspace_dir,
            tool="memory_recall",
            args={"query": "What color is my laptop bag?"},
        )

        print("## Aegis Demo: Integration Boundary")
        print()
        print(f"Workspace: {workspace_dir}")
        print(f"Database: {db_path}")
        print()
        print("[1] Service Info")
        print(f"Deployment: {service_info['service']['deployment_model']}")
        print(f"Transport: {service_info['service']['preferred_transport']}")
        print()
        print("[2] Startup Probe")
        print(f"Service state: {startup_probe['service_state']}")
        print(f"Health state: {startup_probe['health_state']}")
        print()
        print("[3] Setup Tool")
        print(setup["summary"])
        print()
        print("[4] Remember Tool")
        print(remember)
        print()
        print("[5] Recall Tool")
        print(recall)
        print()
        print("This demo shows the thin-host path: inspect service info, gate on startup probe, then call tools through Python.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
