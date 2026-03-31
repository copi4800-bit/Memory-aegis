#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent,
        here.parent.parent,
    ]
    for candidate in candidates:
        if (candidate / "aegis_py" / "cli.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="aegis_demo_") as tmp:
        workspace_dir = Path(tmp)
        db_path = workspace_dir / ".aegis_py" / "demo_memory.db"
        os.environ["AEGIS_DB_PATH"] = str(db_path)

        app = AegisApp(db_path=str(db_path))
        try:
            setup = app.onboarding(workspace_dir=str(workspace_dir))
            remember = app.memory_remember("My favorite drink is jasmine tea.")
            recall = app.memory_recall("What is my favorite drink?")
            status = app.status_summary()
        finally:
            app.close()

        print("## Aegis Demo: First Memory")
        print()
        print(f"Workspace: {workspace_dir}")
        print(f"Database: {db_path}")
        print()
        print("[1] Setup")
        print(setup["summary"])
        print()
        print("[2] Remember")
        print(remember)
        print()
        print("[3] Recall")
        print(recall)
        print()
        print("[4] Status")
        print(status)
        print()
        print("This demo proves the shortest local-first success path: setup, remember, recall, status.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
