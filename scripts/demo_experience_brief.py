#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here.parent.parent):
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate the TruthKeep repository root.")


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="truthkeep_experience_brief_") as tmp:
        db_path = str(Path(tmp) / "experience_brief.db")
        app = AegisApp(db_path)
        try:
            old_stored = app.put_memory(
                "The release checkpoint owner is Linh.",
                type="semantic",
                scope_type="agent",
                scope_id="experience_brief_demo",
                source_kind="manual",
                source_ref="demo://old-owner",
                subject="release.owner",
                confidence=0.9,
            )
            current_stored = app.put_memory(
                "Correction: the release checkpoint owner is Bao.",
                type="semantic",
                scope_type="agent",
                scope_id="experience_brief_demo",
                source_kind="manual",
                source_ref="demo://new-owner",
                subject="release.owner",
                confidence=1.0,
                metadata={"is_winner": True, "is_correction": True},
            )
            assert current_stored is not None
            if old_stored is not None:
                app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
            app.storage.execute("DELETE FROM memories_fts")
            app.storage.execute(
                "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
            )
            response = app.experience_brief(
                "release checkpoint owner",
                scope_type="agent",
                scope_id="experience_brief_demo",
                intent="correction_lookup",
            )
        finally:
            app.close()

    print("## TruthKeep Experience Brief")
    print()
    print(response["brief_text"])
    print()
    print("[JSON]")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
