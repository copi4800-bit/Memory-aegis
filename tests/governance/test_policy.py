import pytest
import uuid

from aegis_py.storage.db import DatabaseManager
from aegis_py.governance.policy import PolicyManager, PolicyMatrix

@pytest.fixture
def db():
    db_manager = DatabaseManager(":memory:")
    db_manager.initialize()
    yield db_manager
    db_manager.close()

@pytest.fixture
def policy_manager(db):
    return PolicyManager(db)

def test_default_policy_is_restrictive(policy_manager):
    policy = policy_manager.get_policy("global", "global")
    assert policy.auto_resolve is False
    assert policy.auto_archive is False
    assert policy.auto_consolidate is False
    assert policy.auto_escalate is False

def test_save_and_retrieve_policy(policy_manager):
    policy = PolicyMatrix(
        id=str(uuid.uuid4()),
        scope_type="global",
        scope_id="global",
        auto_resolve=True,
        auto_archive=False,
        auto_consolidate=True,
        auto_escalate=False
    )
    
    policy_manager.save_policy(policy)
    
    retrieved = policy_manager.get_policy("global", "global")
    assert retrieved.auto_resolve is True
    assert retrieved.auto_archive is False
    assert retrieved.auto_consolidate is True
    assert retrieved.auto_escalate is False

def test_update_existing_policy(policy_manager):
    policy = PolicyMatrix(
        id=str(uuid.uuid4()),
        scope_type="global",
        scope_id="global",
        auto_resolve=True
    )
    policy_manager.save_policy(policy)
    
    policy.auto_resolve = False
    policy.auto_archive = True
    policy_manager.save_policy(policy)
    
    retrieved = policy_manager.get_policy("global", "global")
    assert retrieved.auto_resolve is False
    assert retrieved.auto_archive is True

def test_convenience_methods(policy_manager):
    policy = PolicyMatrix(
        id=str(uuid.uuid4()),
        scope_type="global",
        scope_id="global",
        auto_resolve=True,
        auto_archive=False
    )
    policy_manager.save_policy(policy)
    
    assert policy_manager.can_auto_resolve("global", "global") is True
    assert policy_manager.can_auto_archive("global", "global") is False
    
    # Non-existent scope should default to False
    assert policy_manager.can_auto_resolve("user", "user-1") is False
