import json
import time
from uuid import uuid4

from aegis_py.app import AegisApp
from aegis_py.storage.models import Memory


def test_implicit_contradiction_resolution_prefers_newer_memory(tmp_path):
    app = AegisApp(db_path=str(tmp_path / "contradiction-resolve.db"))

    older = Memory(
        id=str(uuid4()),
        type="semantic",
        scope_type="project",
        scope_id="PX1",
        content="Project X is not active.",
        source_kind="manual",
        subject="project.x.state",
    )
    assert app.storage.put_memory(older) is True

    time.sleep(0.1)

    newer = Memory(
        id=str(uuid4()),
        type="semantic",
        scope_type="project",
        scope_id="PX1",
        content="Project X is active.",
        source_kind="manual",
        subject="project.x.state",
    )
    assert app.storage.put_memory(newer) is True

    app.maintenance()

    older_row = app.storage.fetch_one(
        "SELECT status, metadata_json FROM memories WHERE id = ?",
        (older.id,),
    )
    newer_row = app.storage.fetch_one(
        "SELECT status, metadata_json FROM memories WHERE id = ?",
        (newer.id,),
    )
    conflict_row = app.storage.fetch_one(
        """
        SELECT status, reason, resolution
        FROM conflicts
        WHERE (memory_a_id = ? AND memory_b_id = ?)
           OR (memory_a_id = ? AND memory_b_id = ?)
        LIMIT 1
        """,
        (older.id, newer.id, newer.id, older.id),
    )

    assert older_row is not None and newer_row is not None and conflict_row is not None
    assert older_row["status"] == "superseded"
    assert newer_row["status"] == "active"
    assert conflict_row["reason"] == "Potential logical contradiction"
    assert conflict_row["status"] == "resolved"
    assert conflict_row["resolution"] == "auto_correction_by_recency"

    older_meta = json.loads(older_row["metadata_json"])
    newer_meta = json.loads(newer_row["metadata_json"])
    assert older_meta["lifecycle_events"][-1]["event"] == "corrected_by_newer_info"
    assert older.id in newer_meta.get("corrected_from", [])

    results = app.search("Project X active", scope_id="PX1", scope_type="project")
    assert len(results) == 1
    assert results[0].memory.id == newer.id

    app.close()
