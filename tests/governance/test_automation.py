import pytest
import sqlite3

from aegis_py.storage.db import DatabaseManager
from aegis_py.governance.policy import PolicyManager, PolicyMatrix
from aegis_py.governance.automation import AutonomousExecutor, AutonomousAction, GovernanceException

@pytest.fixture
def db():
    db_manager = DatabaseManager(":memory:")
    db_manager.initialize()
    yield db_manager
    db_manager.close()

@pytest.fixture
def policy_manager(db):
    return PolicyManager(db)

@pytest.fixture
def executor(db, policy_manager):
    return AutonomousExecutor(db, policy_manager)

def test_blocked_by_policy(executor, policy_manager):
    # Default policy is all False
    action = AutonomousAction(
        action_type="archive",
        entity_type="memory",
        entity_id="mem-1",
        explanation="Test archive"
    )
    
    with pytest.raises(GovernanceException, match="is disabled by policy"):
        executor.execute("global", "global", action, lambda d: None)

def test_blocked_by_confidence_gate(executor, policy_manager):
    policy = PolicyMatrix(id="p1", scope_type="global", scope_id="global", auto_resolve=True)
    policy_manager.save_policy(policy)
    
    action = AutonomousAction(
        action_type="resolve",
        entity_type="memory",
        entity_id="mem-1",
        explanation="Test resolve",
        confidence_score=0.89  # Gate is 0.90
    )
    
    with pytest.raises(GovernanceException, match="is below the required gate"):
        executor.execute("global", "global", action, lambda d: None)

def test_successful_execution_and_audit(executor, policy_manager, db):
    policy = PolicyMatrix(id="p1", scope_type="global", scope_id="global", auto_archive=True)
    policy_manager.save_policy(policy)
    
    # We'll create a dummy memory to "archive"
    db.execute("INSERT INTO memories (id, type, scope_type, scope_id, content, source_kind, status, created_at, updated_at) VALUES ('mem-1', 'semantic', 'global', 'global', 'content', 'user', 'active', '2023-01-01', '2023-01-01')")
    
    action = AutonomousAction(
        action_type="archive",
        entity_type="memory",
        entity_id="mem-1",
        explanation="Memory reached expiration",
        details={"reason": "expired"}
    )
    
    def mutation(database: DatabaseManager):
        database.execute("UPDATE memories SET status = 'archived' WHERE id = 'mem-1'")
    
    audit_id = executor.execute("global", "global", action, mutation)
    assert audit_id is not None
    
    # Check memory was mutated
    mem = db.fetch_one("SELECT status FROM memories WHERE id = 'mem-1'")
    assert mem["status"] == "archived"
    
    # Check audit log was written
    audit = db.fetch_one("SELECT * FROM autonomous_audit_log WHERE id = ?", (audit_id,))
    assert audit is not None
    assert audit["action_type"] == "archive"
    assert audit["explanation"] == "Memory reached expiration"
    assert "expired" in audit["details_json"]
