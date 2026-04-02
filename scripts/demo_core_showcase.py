#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [here.parent, here.parent.parent]
    for candidate in candidates:
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the Aegis repository root.")


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="aegis_core_showcase_") as tmp:
        db_path = str(Path(tmp) / "core_showcase.db")
        app = AegisApp(db_path)
        try:
            old_stored = app.put_memory(
                "The maintenance window is Friday.",
                type="semantic",
                scope_type="agent",
                scope_id="core_showcase_demo",
                source_kind="manual",
                source_ref="demo://old",
                subject="maintenance_window",
                confidence=0.9,
            )
            current_stored = app.put_memory(
                "Correction: the maintenance window moved to Saturday.",
                type="semantic",
                scope_type="agent",
                scope_id="core_showcase_demo",
                source_kind="manual",
                source_ref="demo://new",
                subject="maintenance_window",
                confidence=1.0,
                metadata={"is_winner": True, "is_correction": True},
            )
            if old_stored is not None:
                app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
            app.storage.execute("DELETE FROM memories_fts")
            app.storage.execute(
                "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
            )
            response = app.core_showcase(
                "maintenance window",
                scope_type="agent",
                scope_id="core_showcase_demo",
                intent="correction_lookup",
            )
        finally:
            app.close()

    print("## Aegis Core Showcase")
    print()
    print(response["showcase_text"])
    print()
    print("[JSON]")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
