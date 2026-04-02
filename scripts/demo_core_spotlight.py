#!/usr/bin/env python3
from __future__ import annotations

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

    from aegis_py.memory.core import MemoryManager
    from aegis_py.retrieval.models import SearchQuery
    from aegis_py.retrieval.search import SearchPipeline
    from aegis_py.spotlight_surface import render_spotlight_text
    from aegis_py.storage.manager import StorageManager
    from aegis_py.storage.models import Memory

    with tempfile.TemporaryDirectory(prefix="aegis_core_spotlight_") as tmp:
        db_path = str(Path(tmp) / "core_spotlight.db")
        storage = StorageManager(db_path)
        manager = MemoryManager(storage)
        pipeline = SearchPipeline(storage)

        try:
            old_fact = Memory(
                id="old_fact",
                type="semantic",
                content="The launch date is April 10.",
                subject="launch_date",
                confidence=0.9,
                source_kind="manual",
                source_ref="demo://original",
                scope_type="agent",
                scope_id="spotlight",
            )
            current_fact = Memory(
                id="current_fact",
                type="semantic",
                content="Correction: the launch date moved to April 24.",
                subject="launch_date",
                confidence=1.0,
                source_kind="manual",
                source_ref="demo://correction",
                scope_type="agent",
                scope_id="spotlight",
                metadata={
                    "is_winner": True,
                    "is_correction": True,
                    "corrected_from": ["old_fact"],
                },
            )

            manager.store(old_fact)
            manager.store(current_fact)
            storage.execute("UPDATE memories SET status = 'superseded' WHERE id = 'old_fact'")
            storage.execute("DELETE FROM memories_fts")
            storage.execute(
                "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
            )

            query = SearchQuery(
                query="launch date",
                scope_type="agent",
                scope_id="spotlight",
                include_global=False,
                min_score=-10.0,
            )
            setattr(query, "intent", "correction_lookup")
            results = pipeline.search(query)
            if not results:
                print("Aegis spotlight demo found no results.")
                return 1

            top = results[0]
        finally:
            storage.close()

    print("## Aegis Core Spotlight")
    print("This demo shows the current-truth advantage of the Aegis memory core.")
    print()
    print("[Scenario]")
    print("Old fact: The launch date is April 10.")
    print("Correction: The launch date moved to April 24.")
    print("Query: launch date")
    print()
    print(render_spotlight_text(top))

    print()
    print("Takeaway: Aegis did not only retrieve a memory. It selected the current truth and showed why the older fact lost.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
