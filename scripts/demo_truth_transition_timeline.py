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

    with tempfile.TemporaryDirectory(prefix="truthkeep_timeline_") as tmp:
        db_path = str(Path(tmp) / "timeline.db")
        app = AegisApp(db_path)
        try:
            old_stored = app.put_memory("The release owner is Linh.", type="semantic", scope_type="agent", scope_id="timeline_demo", source_kind="manual", source_ref="demo://timeline-old", subject="release.owner", confidence=0.9)
            app.put_memory("Correction: the release owner is Bao.", type="semantic", scope_type="agent", scope_id="timeline_demo", source_kind="manual", source_ref="demo://timeline-new", subject="release.owner", confidence=1.0, metadata={"is_winner": True, "is_correction": True})
            if old_stored is not None:
                app.storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_stored.id,))
                app.storage.record_memory_state_transition(memory_id=old_stored.id, from_state="validated", to_state="invalidated", reason="corrected_by_newer_info", actor="demo", details={"winner_hint": "release.owner"})
                app.storage.record_governance_event(event_kind="truth_superseded_demo", scope_type="agent", scope_id="timeline_demo", memory_id=old_stored.id, payload={"winner_id": "demo-winner", "reason": "newer_correction"})
            app.storage.execute("DELETE FROM memories_fts")
            app.storage.execute("INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories")
            response = app.truth_transition_timeline("release owner", scope_type="agent", scope_id="timeline_demo", intent="correction_lookup")
        finally:
            app.close()

    print("## TruthKeep Truth Transition Timeline")
    print()
    print(response["timeline_text"])
    print()
    print("[JSON]")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
