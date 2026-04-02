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


def build_demo_showcase():
    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="aegis_core_showcase_html_") as tmp:
        db_path = str(Path(tmp) / "core_showcase_html.db")
        app = AegisApp(db_path)
        try:
            old_stored = app.put_memory(
                "The maintenance window is Friday.",
                type="semantic",
                scope_type="agent",
                scope_id="core_showcase_html",
                source_kind="manual",
                source_ref="html://old",
                subject="maintenance_window",
                confidence=0.9,
            )
            current_stored = app.put_memory(
                "Correction: the maintenance window moved to Saturday.",
                type="semantic",
                scope_type="agent",
                scope_id="core_showcase_html",
                source_kind="manual",
                source_ref="html://new",
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
            return app.core_showcase(
                "maintenance window",
                scope_type="agent",
                scope_id="core_showcase_html",
                intent="correction_lookup",
            )
        finally:
            app.close()


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.core_showcase_report import render_core_showcase_html

    response = build_demo_showcase()
    payload = response["result"]
    if payload is None:
        raise RuntimeError("Unable to render HTML showcase without a core showcase result.")

    html_text = render_core_showcase_html(payload, title="Aegis Core Showcase")
    output_path = repo_root / ".planning" / "benchmarks" / "core_showcase_report.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
