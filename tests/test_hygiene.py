import pytest
import time
from datetime import datetime, timedelta, timezone
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.ingest import IngestEngine
from aegis_py.hygiene.engine import HygieneEngine
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery

@pytest.fixture
def temp_env(tmp_path):
    db_file = tmp_path / "test_aegis_hygiene.db"
    storage = StorageManager(str(db_file))
    ingest = IngestEngine(storage)
    hygiene = HygieneEngine(storage)
    search = SearchPipeline(storage)
    return storage, ingest, hygiene, search

def test_reinforcement(temp_env):
    storage, ingest, hygiene, search = temp_env
    
    mem = ingest.ingest("Important project detail", scope_id="p1")
    assert mem.activation_score == 1.0
    
    # Simulate access via reinforcement method
    storage.reinforce_memory(mem.id)
    
    refetched = storage.get_memory(mem.id)
    assert 1.19 < refetched.activation_score < 1.7
    assert refetched.access_count == 1
    assert refetched.metadata["retention_stage"] == "active"

def test_decay(temp_env):
    storage, ingest, hygiene, search = temp_env
    
    mem = ingest.ingest("Will decay soon", scope_id="p1")
    
    # Artificially set last_accessed_at to 7 days ago
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    with storage._get_connection() as conn:
        conn.execute("UPDATE memories SET last_accessed_at = ? WHERE id = ?", (seven_days_ago, mem.id))
        conn.commit()
    
    # Run hygiene
    hygiene.run_maintenance(half_life_days=7.0)
    
    refetched = storage.get_memory(mem.id)
    # 1.0 * (0.5 ^ (7/7)) = 0.5
    assert 0.49 < refetched.activation_score < 0.51
    assert refetched.metadata["retention_stage"] == "cold"

def test_session_end_archiving(temp_env):
    storage, ingest, hygiene, search = temp_env
    
    # Ingest working memory for session 'S1'
    ingest.ingest("Current task progress", type="working", session_id="S1", scope_id="p1")
    # Ingest episodic memory (should NOT be archived on session end)
    ingest.ingest("Permanent fact", type="episodic", session_id="S1", scope_id="p1")
    
    # End session S1
    hygiene.on_session_end("S1")
    
    with storage._get_connection() as conn:
        mems = conn.execute("SELECT type, status FROM memories WHERE session_id = 'S1'").fetchall()
        for m in mems:
            if m['type'] == 'working':
                assert m['status'] == 'archived'
            else:
                assert m['status'] == 'active'


def test_type_aware_decay_defaults_make_working_decay_faster_than_semantic(temp_env):
    storage, ingest, hygiene, search = temp_env

    working = ingest.ingest("Temporary working thread", type="working", session_id="S-HALF", scope_id="p1")
    semantic = ingest.ingest("Durable semantic fact", type="semantic", scope_id="p1")
    assert working is not None and semantic is not None

    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    with storage._get_connection() as conn:
        conn.execute("UPDATE memories SET last_accessed_at = ? WHERE id = ?", (seven_days_ago, working.id))
        conn.execute("UPDATE memories SET last_accessed_at = ? WHERE id = ?", (seven_days_ago, semantic.id))
        conn.commit()

    hygiene.run_maintenance()

    working_refetched = storage.get_memory(working.id)
    semantic_refetched = storage.get_memory(semantic.id)
    assert working_refetched is not None and semantic_refetched is not None
    assert working_refetched.activation_score < semantic_refetched.activation_score


def test_decay_override_still_applies_uniformly(temp_env):
    storage, ingest, hygiene, search = temp_env

    working = ingest.ingest("Temporary working thread", type="working", session_id="S-OVERRIDE", scope_id="p1")
    semantic = ingest.ingest("Durable semantic fact", type="semantic", scope_id="p1")
    assert working is not None and semantic is not None

    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    with storage._get_connection() as conn:
        conn.execute("UPDATE memories SET last_accessed_at = ? WHERE id = ?", (seven_days_ago, working.id))
        conn.execute("UPDATE memories SET last_accessed_at = ? WHERE id = ?", (seven_days_ago, semantic.id))
        conn.commit()

    hygiene.run_maintenance(half_life_days=7.0)

    working_refetched = storage.get_memory(working.id)
    semantic_refetched = storage.get_memory(semantic.id)
    assert working_refetched is not None and semantic_refetched is not None
    assert abs(working_refetched.activation_score - semantic_refetched.activation_score) < 0.02


def test_archive_first_decay_archives_low_signal_memory_and_marks_stage(temp_env):
    storage, ingest, hygiene, search = temp_env

    mem = ingest.ingest("A volatile thread that should cool into archive.", type="working", scope_id="p1")
    assert mem is not None

    forty_days_ago = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    with storage._get_connection() as conn:
        conn.execute(
            "UPDATE memories SET activation_score = ?, last_accessed_at = ?, updated_at = ? WHERE id = ?",
            (0.22, forty_days_ago, forty_days_ago, mem.id),
        )
        conn.commit()

    hygiene.run_maintenance()

    refetched = storage.get_memory(mem.id)
    assert refetched is not None
    assert refetched.status == "archived"
    assert refetched.metadata["retention_stage"] in {"archive_candidate", "deprecated_candidate"}
    assert refetched.metadata["lifecycle_events"][-1]["event"] == "archived_by_decay_policy"


def test_bounded_reinforcement_does_not_fully_reset_cold_memory(temp_env):
    storage, ingest, hygiene, search = temp_env

    mem = ingest.ingest("Frequently recalled but old semantic memory.", type="semantic", scope_id="p1")
    assert mem is not None

    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    with storage._get_connection() as conn:
        conn.execute(
            "UPDATE memories SET activation_score = ?, access_count = ?, last_accessed_at = ?, updated_at = ? WHERE id = ?",
            (0.52, 3, thirty_days_ago, thirty_days_ago, mem.id),
        )
        conn.commit()

    storage.reinforce_memory(mem.id)

    refetched = storage.get_memory(mem.id)
    assert refetched is not None
    assert 0.72 < refetched.activation_score < 1.0
    assert refetched.access_count == 4
