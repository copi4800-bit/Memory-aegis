from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

from aegis_py.app import AegisApp


def test_snapshot_backup_succeeds_while_concurrent_writes_continue(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "backup-concurrent.db"

    app = AegisApp(db_path=str(db_path))
    app.put_memory(
        "Baseline memory survives concurrent backup.",
        type="semantic",
        scope_type="project",
        scope_id="OPS-BACKUP",
        subject="ops.backup",
        source_kind="manual",
    )

    stop_event = threading.Event()
    started_event = threading.Event()
    writer_errors: list[Exception] = []

    def writer() -> None:
        conn = sqlite3.connect(db_path)
        try:
            started_event.set()
            for index in range(25):
                if stop_event.is_set():
                    break
                conn.execute(
                    """
                    INSERT INTO memories (
                        id, type, scope_type, scope_id, content, summary, subject,
                        source_kind, source_ref, origin_node_id, session_id, status,
                        confidence, activation_score, access_count, created_at,
                        updated_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)
                    """,
                    (
                        f"writer-{index}",
                        "semantic",
                        "project",
                        "OPS-BACKUP",
                        f"Concurrent write {index}",
                        f"Concurrent write {index}",
                        "ops.backup",
                        "manual",
                        None,
                        None,
                        None,
                        "active",
                        1.0,
                        1.0,
                        0,
                        json.dumps({}, ensure_ascii=False),
                    ),
                )
                conn.commit()
                time.sleep(0.005)
        except Exception as exc:  # pragma: no cover - captured by assertion below
            writer_errors.append(exc)
        finally:
            conn.close()

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    started_event.wait(timeout=1.0)

    snapshot = app.create_backup(mode="snapshot", workspace_dir=str(workspace_dir))

    stop_event.set()
    thread.join(timeout=1.0)

    assert writer_errors == []
    assert snapshot["mode"] == "snapshot"

    snapshot_path = Path(snapshot["path"])
    assert snapshot_path.exists()
    assert snapshot_path.stat().st_size > 0

    with sqlite3.connect(snapshot_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM memories WHERE scope_type = 'project' AND scope_id = 'OPS-BACKUP'"
        ).fetchone()
    assert row is not None
    assert row[0] >= 1

    app.close()


def test_backup_script_can_create_preview_and_restore(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    db_path = tmp_path / "backup-script.db"

    app = AegisApp(db_path=str(db_path))
    app.put_memory(
        "Backup helper script should operate on Python-owned runtime flows.",
        type="semantic",
        scope_type="project",
        scope_id="OPS-SCRIPT",
        subject="ops.script",
        source_kind="manual",
    )

    created = app.create_backup(mode="snapshot", workspace_dir=str(workspace_dir))
    listed = app.list_backups(workspace_dir=str(workspace_dir))
    preview = app.preview_restore(created["path"])
    restored = app.restore_backup(created["path"])

    assert created["mode"] == "snapshot"
    assert listed["backups"]
    assert preview["dry_run"] is True
    assert restored["restored"] is True

    app.close()
