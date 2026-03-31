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

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="aegis_grounding_demo_") as tmp:
        db_path = str(Path(tmp) / "grounding_demo.db")
        app = AegisApp(db_path=db_path)
        try:
            stored = app.put_memory(
                "The production release checklist lives in docs/release-checklist.md.",
                type="semantic",
                scope_type="project",
                scope_id="DEMO",
                subject="release.checklist",
                source_kind="manual",
                source_ref="docs/release-checklist.md",
                summary="Release checklist location",
            )
            search_payload = app.search_payload(
                "release checklist",
                scope_type="project",
                scope_id="DEMO",
                include_global=False,
                limit=3,
                retrieval_mode="explain",
            )
            context_pack = app.search_context_pack(
                "release checklist",
                scope_type="project",
                scope_id="DEMO",
                include_global=False,
                limit=3,
            )
        finally:
            app.close()

        top = search_payload[0]
        grounded = context_pack["results"][0]

        print("## Aegis Demo: Grounded Recall")
        print()
        print(f"Stored memory: {stored.id if stored else 'unknown'}")
        print()
        print("[1] Provenance")
        print(top["provenance"])
        print()
        print("[2] Trust")
        print(f"Trust state: {top['trust_state']}")
        print(f"Trust reason: {top['trust_reason']}")
        print()
        print("[3] Ranking Reasons")
        print(", ".join(top["reasons"]))
        print()
        print("[4] Context Pack Evidence")
        print(f"Retrieval stage: {grounded['retrieval_stage']}")
        print(f"Scope: {grounded['memory']['scope_type']}/{grounded['memory']['scope_id']}")
        print(f"Source: {grounded['memory']['source_kind']} -> {grounded['memory']['source_ref']}")
        print()
        print("This demo shows why the recall is grounded: Aegis exposes provenance, trust shape, and ranking reasons instead of only returning an answer.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
