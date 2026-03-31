import pytest
import json
import sqlite3
from datetime import datetime, timezone
import uuid

from aegis_py.storage.db import DatabaseManager
from aegis_py.governance.rollback import RollbackManager, RollbackException

@pytest.fixture
def db():
    db_manager = DatabaseManager(":memory:")
    db_manager.initialize()
    yield db_manager
    db_manager.close()

@pytest.fixture
def rollback_manager(db):
    return RollbackManager(db)

def test_rollback_memory_mutation(db, rollback_manager):
    # Setup initial state
    db.execute(
        "INSERT INTO memories (id, type, scope_type, scope_id, content, source_kind, status, created_at, updated_at) "
        "VALUES ('mem-1', 'semantic', 'global', 'global', 'Initial content', 'user', 'active', '2023-01-01', '2023-01-01')"
    )
    
    # Simulate a mutation and audit log
    db.execute("UPDATE memories SET content = 'Auto updated', status = 'archived' WHERE id = 'mem-1'")
    
    audit_id = str(uuid.uuid4())
    previous_state = {
        "id": "mem-1",
        "type": "semantic",
        "scope_type": "global",
        "scope_id": "global",
        "session_id": None,
        "content": "Initial content",
        "summary": None,
        "subject": None,
        "source_kind": "user",
        "source_ref": None,
        "origin_node_id": None,
        "status": "active",
        "confidence": 1.0,
        "activation_score": 1.0,
        "access_count": 0,
        "created_at": "2023-01-01",
        "updated_at": "2023-01-01",
        "last_accessed_at": None,
        "expires_at": None,
        "archived_at": None,
        "metadata_json": {}
    }
    
    db.execute(
        """
        INSERT INTO autonomous_audit_log (
            id, action_type, entity_type, entity_id, explanation, applied_at, status, details_json
        ) VALUES (?, 'archive', 'memory', 'mem-1', 'Test', '2023-01-02', 'applied', ?)
        """,
        (audit_id, json.dumps({"previous_state": previous_state}))
    )
    
    # Perform rollback
    rollback_manager.rollback(audit_id)
    
    # Verify state restored
    mem = db.fetch_one("SELECT content, status FROM memories WHERE id = 'mem-1'")
    assert mem["content"] == "Initial content"
    assert mem["status"] == "active"
    
    # Verify audit status
    audit = db.fetch_one("SELECT status, rolled_back_at FROM autonomous_audit_log WHERE id = ?", (audit_id,))
    assert audit["status"] == "rolled_back"
    assert audit["rolled_back_at"] is not None

def test_rollback_missing_audit(rollback_manager):
    with pytest.raises(RollbackException, match="not found"):
        rollback_manager.rollback("missing-id")

def test_rollback_missing_state(db, rollback_manager):
    audit_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO autonomous_audit_log (
            id, action_type, entity_type, entity_id, explanation, applied_at, status, details_json
        ) VALUES (?, 'archive', 'memory', 'mem-1', 'Test', '2023-01-02', 'applied', '{}')
        """,
        (audit_id,)
    )
    
    with pytest.raises(RollbackException, match="missing 'previous_state'"):
        rollback_manager.rollback(audit_id)

def test_rollback_already_rolled_back(db, rollback_manager):
    audit_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO autonomous_audit_log (
            id, action_type, entity_type, entity_id, explanation, applied_at, status, details_json
        ) VALUES (?, 'archive', 'memory', 'mem-1', 'Test', '2023-01-02', 'rolled_back', '{}')
        """,
        (audit_id,)
    )
    
    with pytest.raises(RollbackException, match="Cannot rollback action in status"):
        rollback_manager.rollback(audit_id)
