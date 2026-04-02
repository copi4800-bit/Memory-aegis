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

    with tempfile.TemporaryDirectory(prefix="aegis_conflict_spotlight_") as tmp:
        db_path = str(Path(tmp) / "conflict_spotlight.db")
        storage = StorageManager(db_path)
        manager = MemoryManager(storage)
        pipeline = SearchPipeline(storage)

        try:
            contender = Memory(
                id="conflict_contender",
                type="semantic",
                content="The office is in Hanoi.",
                subject="office_location",
                confidence=0.7,
                source_kind="manual",
                source_ref="demo://contender",
                scope_type="agent",
                scope_id="spotlight_conflict",
            )
            winner = Memory(
                id="conflict_winner",
                type="semantic",
                content="The office moved to Saigon.",
                subject="office_location",
                confidence=0.95,
                source_kind="manual",
                source_ref="demo://winner",
                scope_type="agent",
                scope_id="spotlight_conflict",
                metadata={"is_winner": True},
            )

            manager.store(contender)
            manager.store(winner)
            for index in range(5):
                storage.execute(
                    """
                    INSERT INTO evidence_events (
                        id, scope_type, scope_id, memory_id, source_kind, source_ref, raw_content, created_at
                    ) VALUES (?, 'agent', 'spotlight_conflict', 'conflict_winner', 'manual', 'demo://winner', 'Confirmed office relocation', '2026-04-02T00:00:00+00:00')
                    """,
                    (f"conflict_demo_event_{index}",),
                )
            storage.execute("DELETE FROM memories_fts")
            storage.execute(
                "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
            )

            query = SearchQuery(
                query="office",
                scope_type="agent",
                scope_id="spotlight_conflict",
                include_global=False,
                min_score=-10.0,
            )
            setattr(query, "intent", "correction_lookup")
            results = pipeline.search(query)
            if not results:
                print("Aegis conflict spotlight demo found no results.")
                return 1
            top = results[0]
        finally:
            storage.close()

    print("## Aegis Conflict Spotlight")
    print("This demo shows how Aegis keeps one current winner visible while pushing a weaker alternative into why-not.")
    print()
    print("[Scenario]")
    print("Contender: The office is in Hanoi.")
    print("Winner: The office moved to Saigon.")
    print("Query: office")
    print()
    print(render_spotlight_text(top))
    print()
    print("Takeaway: Aegis did not surface both memories equally. It kept the stronger truth in front and made the losing alternative legible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
