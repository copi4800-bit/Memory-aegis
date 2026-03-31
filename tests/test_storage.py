import pytest
import os
import sqlite3
from aegis_py.storage.manager import StorageManager
from aegis_py.storage.models import Memory, StyleProfile, StyleSignal

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_aegis.db"
    return str(db_file)

def test_storage_init(temp_db):
    manager = StorageManager(temp_db)
    assert os.path.exists(temp_db)

def test_put_get_memory(temp_db):
    manager = StorageManager(temp_db)
    mem = Memory(
        id="mem_1",
        type="semantic",
        scope_type="project",
        scope_id="test_project",
        content="Aegis v4 rebuild in Python is starting.",
        source_kind="manual"
    )
    manager.put_memory(mem)
    
    retrieved = manager.get_memory("mem_1")
    assert retrieved is not None
    assert retrieved.content == mem.content
    assert retrieved.scope_id == "test_project"
    assert "evidence" in retrieved.metadata
    assert retrieved.admission_state == "validated"
    assert retrieved.status == "active"

def test_fts_search(temp_db):
    manager = StorageManager(temp_db)
    mems = [
        Memory(id="m1", type="semantic", scope_type="g", scope_id="v", content="The sky is blue", source_kind="m"),
        Memory(id="m2", type="semantic", scope_type="g", scope_id="v", content="The grass is green", source_kind="m"),
        Memory(id="m3", type="semantic", scope_type="g", scope_id="v", content="Python is a language", source_kind="m"),
    ]
    for m in mems:
        manager.put_memory(m)
    
    results = manager.search_fts("blue", "g", "v")
    assert len(results) == 1
    assert results[0][0].id == "m1"
    
    results = manager.search_fts("is", "g", "v")
    assert len(results) == 3


def test_storage_preserves_metadata_and_status(temp_db):
    manager = StorageManager(temp_db)
    mem = Memory(
        id="mem_2",
        type="working",
        scope_type="session",
        scope_id="sess-1",
        session_id="sess-1",
        content="Temporary memory with provenance.",
        source_kind="message",
        source_ref="msg-1",
        status="conflict_candidate",
        metadata={"trace": "unit-test", "importance": 0.7},
    )
    manager.put_memory(mem)

    retrieved = manager.get_memory("mem_2")
    assert retrieved is not None
    assert retrieved.session_id == "sess-1"
    assert retrieved.source_ref == "msg-1"
    assert retrieved.status == "conflict_candidate"
    assert retrieved.metadata["trace"] == "unit-test"


def test_storage_manager_supports_in_memory_database():
    manager = StorageManager(":memory:")
    mem = Memory(
        id="mem_im_1",
        type="semantic",
        scope_type="project",
        scope_id="in-memory",
        content="In-memory storage should preserve schema across calls.",
        source_kind="manual",
    )
    assert manager.put_memory(mem) is True
    retrieved = manager.get_memory("mem_im_1")
    assert retrieved is not None
    assert retrieved.scope_id == "in-memory"


def test_storage_evidence_events_are_append_only(temp_db):
    manager = StorageManager(temp_db)

    first = manager.create_evidence_event(
        scope_type="project",
        scope_id="append-only",
        raw_content="First raw ingest event.",
        source_kind="manual",
        source_ref="notes#1",
    )
    second = manager.create_evidence_event(
        scope_type="project",
        scope_id="append-only",
        raw_content="Second raw ingest event.",
        source_kind="manual",
        source_ref="notes#1",
    )

    rows = manager.fetch_all(
        "SELECT id, raw_content FROM evidence_events WHERE scope_id = ? ORDER BY created_at ASC, id ASC",
        ("append-only",),
    )

    assert first.id != second.id
    assert [(row["id"], row["raw_content"]) for row in rows] == [
        (first.id, "First raw ingest event."),
        (second.id, "Second raw ingest event."),
    ]


def test_storage_put_memory_backfills_evidence_linkage(temp_db):
    manager = StorageManager(temp_db)
    mem = Memory(
        id="mem_evidence_1",
        type="semantic",
        scope_type="project",
        scope_id="evidence-backfill",
        content="Storage manager should backfill evidence for direct writes.",
        source_kind="manual",
        source_ref="runbook#direct",
    )

    assert manager.put_memory(mem) is True

    persisted = manager.get_memory("mem_evidence_1")
    evidence_rows = manager.list_evidence_events_for_memory("mem_evidence_1")

    assert persisted is not None
    assert "evidence" in persisted.metadata
    assert persisted.metadata["evidence"]["event_id"] == evidence_rows[0].id
    assert len(evidence_rows) == 1
    assert evidence_rows[0].raw_content == mem.content
    assert evidence_rows[0].source_ref == "runbook#direct"


def test_storage_can_resolve_linked_evidence_from_memory_metadata(temp_db):
    manager = StorageManager(temp_db)
    mem = Memory(
        id="mem_linked_evidence_1",
        type="semantic",
        scope_type="project",
        scope_id="evidence-linked",
        content="Linked evidence should resolve through a helper.",
        source_kind="manual",
        source_ref="guide#linked",
    )

    assert manager.put_memory(mem) is True

    linked = manager.get_linked_evidence_for_memory("mem_linked_evidence_1")

    assert len(linked) == 1
    assert linked[0].memory_id == "mem_linked_evidence_1"
    assert linked[0].raw_content == mem.content


def test_storage_can_summarize_evidence_coverage(temp_db):
    manager = StorageManager(temp_db)
    first = Memory(
        id="mem_cov_1",
        type="semantic",
        scope_type="project",
        scope_id="coverage",
        content="Coverage memory one.",
        source_kind="manual",
    )
    second = Memory(
        id="mem_cov_2",
        type="semantic",
        scope_type="project",
        scope_id="coverage",
        content="Coverage memory two.",
        source_kind="manual",
    )

    assert manager.put_memory(first) is True
    assert manager.put_memory(second) is True
    manager.execute("UPDATE memories SET metadata_json = ? WHERE id = ?", ("{}", "mem_cov_2"))

    coverage = manager.summarize_evidence_coverage(scope_type="project", scope_id="coverage")

    assert coverage["memory_records"] == 2
    assert coverage["linked_memories"] == 1
    assert coverage["missing_linkage"] == 1
    assert coverage["linked_event_count"] == 1
    assert coverage["evidence_events"] == 2
    assert coverage["coverage_ratio"] == 0.5


def test_storage_can_report_admission_state_and_state_summary(temp_db):
    manager = StorageManager(temp_db)
    manager.put_memory(
        Memory(
            id="mem_state_validated",
            type="semantic",
            scope_type="project",
            scope_id="states",
            content="Validated memory.",
            source_kind="manual",
        )
    )
    manager.put_memory(
        Memory(
            id="mem_state_superseded",
            type="semantic",
            scope_type="project",
            scope_id="states",
            content="Superseded memory.",
            source_kind="manual",
            status="superseded",
        )
    )

    validated = manager.get_memory_state("mem_state_validated")
    superseded = manager.get_memory_state("mem_state_superseded")
    summary = manager.summarize_memory_states(scope_type="project", scope_id="states")

    assert validated is not None
    assert validated["admission_state"] == "validated"
    assert superseded is not None
    assert superseded["admission_state"] == "invalidated"
    assert summary["state_counts"]["validated"] == 1
    assert summary["state_counts"]["invalidated"] == 1


def test_storage_preserves_non_active_lifecycle_statuses_for_visibility_rules(temp_db):
    manager = StorageManager(temp_db)

    for memory_id, status in [
        ("mem_archived", "archived"),
        ("mem_expired", "expired"),
        ("mem_superseded", "superseded"),
        ("mem_conflict_candidate", "conflict_candidate"),
    ]:
        manager.put_memory(
            Memory(
                id=memory_id,
                type="semantic",
                scope_type="project",
                scope_id="visibility",
                content=f"Stored as {status}",
                source_kind="manual",
                status=status,
            )
        )

    rows = manager.fetch_all(
        "SELECT id, status FROM memories WHERE scope_id = ? ORDER BY id",
        ("visibility",),
    )

    assert [(row["id"], row["status"]) for row in rows] == [
        ("mem_archived", "archived"),
        ("mem_conflict_candidate", "conflict_candidate"),
        ("mem_expired", "expired"),
        ("mem_superseded", "superseded"),
    ]


def test_storage_repairs_legacy_schema_without_resetting_db(tmp_path):
    db_file = tmp_path / "legacy_aegis.db"
    conn = sqlite3.connect(db_file)
    conn.executescript(
        """
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            scope_id TEXT NOT NULL,
            content TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE style_signals (
            id TEXT PRIMARY KEY
        );

        CREATE TABLE style_profiles (
            agent_id TEXT PRIMARY KEY,
            updated_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()

    manager = StorageManager(str(db_file))
    mem = Memory(
        id="legacy_mem",
        type="working",
        scope_type="session",
        scope_id="legacy-scope",
        session_id="legacy-session",
        content="Legacy databases should be repaired in place.",
        source_kind="manual",
    )
    manager.put_memory(mem)
    manager.put_signal(
        StyleSignal(
            id="legacy_sig",
            session_id="legacy-session",
            scope_id="legacy-scope",
            scope_type="session",
            signal_key="tone",
            signal_value="direct",
        )
    )
    manager.upsert_profile(
        StyleProfile(
            id="legacy_profile",
            scope_id="legacy-scope",
            scope_type="session",
            preferences_json={"tone": "direct"},
        )
    )

    columns = manager._table_columns("memories")
    signal_columns = manager._table_columns("style_signals")
    profile_columns = manager._table_columns("style_profiles")
    retrieved = manager.get_memory("legacy_mem")
    profile = manager.get_profile("legacy-scope", "session")

    assert "session_id" in columns
    assert "metadata_json" in columns
    assert "session_id" in signal_columns
    assert "scope_id" in signal_columns
    assert "scope_id" in profile_columns
    assert "scope_type" in profile_columns
    assert retrieved is not None
    assert retrieved.session_id == "legacy-session"
    assert profile is not None
    assert profile.scope_id == "legacy-scope"
