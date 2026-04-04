from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any


def _venv_active() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def check_python_version() -> dict[str, Any]:
    ok = sys.version_info >= (3, 11)
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if not ok:
        guidance = "Install Python 3.11 or newer before running TruthKeep."
    elif _venv_active():
        guidance = None
    else:
        guidance = (
            "Prefer a local virtualenv for dependency install: "
            "`python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt`."
        )
    return {
        "id": "python",
        "ok": ok,
        "required": True,
        "version": version,
        "summary": f"Python {version}",
        "guidance": guidance,
    }


def check_command(name: str, *, required_for: str) -> dict[str, Any]:
    executable = shutil.which(name)
    if executable is None:
        return {
            "id": name,
            "ok": False,
            "required": False,
            "version": None,
            "summary": f"{name} not found",
            "guidance": f"Install {name} if you want the OpenClaw plugin/bootstrap path ({required_for}).",
        }

    completed = subprocess.run(
        [executable, "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    version = (completed.stdout or completed.stderr).strip().splitlines()[0] if completed.returncode == 0 else None
    return {
        "id": name,
        "ok": completed.returncode == 0,
        "required": False,
        "version": version,
        "summary": version or f"{name} detected",
        "guidance": None if completed.returncode == 0 else f"{name} is installed but did not report a healthy version.",
    }


def check_sqlite_fts5() -> dict[str, Any]:
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE aegis_fts_probe USING fts5(content)")
        conn.close()
        return {
            "id": "sqlite_fts5",
            "ok": True,
            "required": True,
            "version": sqlite3.sqlite_version,
            "summary": f"SQLite {sqlite3.sqlite_version} with FTS5",
            "guidance": None,
        }
    except sqlite3.Error as exc:
        return {
            "id": "sqlite_fts5",
            "ok": False,
            "required": True,
            "version": sqlite3.sqlite_version,
            "summary": f"SQLite {sqlite3.sqlite_version} without usable FTS5",
            "guidance": f"Install SQLite with FTS5 support. Current error: {exc}",
        }


def build_install_readiness_report(workspace_dir: str | Path) -> dict[str, Any]:
    workspace = Path(workspace_dir)
    checks = {
        "python": check_python_version(),
        "sqlite_fts5": check_sqlite_fts5(),
        "node": check_command("node", required_for="Node-based host bootstrap"),
        "npm": check_command("npm", required_for="plugin build/bootstrap scripts"),
    }

    blocking_failures = [entry for entry in checks.values() if entry["required"] and not entry["ok"]]
    plugin_gaps = [entry for key, entry in checks.items() if key in {"node", "npm"} and not entry["ok"]]

    if blocking_failures:
        readiness = "BLOCKED"
        summary = "Core install prerequisites are missing. TruthKeep cannot run safely yet."
    elif plugin_gaps:
        readiness = "RUNTIME_READY_PLUGIN_INCOMPLETE"
        summary = "TruthKeep runtime prerequisites are ready, but the OpenClaw plugin/bootstrap path is not fully installed yet."
    else:
        readiness = "READY"
        summary = "TruthKeep runtime and plugin prerequisites look ready on this machine."

    guidance = [entry["guidance"] for entry in checks.values() if entry.get("guidance")]

    return {
        "workspace_dir": str(workspace),
        "readiness": readiness,
        "summary": summary,
        "checks": checks,
        "guidance": guidance,
    }


def main() -> int:
    import json

    report = build_install_readiness_report(Path.cwd())
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

