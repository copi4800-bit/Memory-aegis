import pytest
import uuid
from datetime import datetime, timezone

from aegis_py.storage.db import DatabaseManager
from aegis_py.replication.identity import IdentityManager
from aegis_py.replication.sync import SyncManager, ReplicationPayload, Mutation

@pytest.fixture
def db():
    db_manager = DatabaseManager(":memory:")
    db_manager.initialize()
    yield db_manager
    db_manager.close()

@pytest.fixture
def identity_manager(db):
    return IdentityManager(db)

@pytest.fixture
def sync_manager(db, identity_manager):
    return SyncManager(db, identity_manager)

def test_apply_payload_idempotency(db, sync_manager):
    remote_node_id = str(uuid.uuid4())
    payload_id = str(uuid.uuid4())
    
    memory_id = str(uuid.uuid4())
    
    mutation = Mutation(
        action="upsert",
        entity_type="memory",
        entity_id=memory_id,
        data={
            "id": memory_id,
            "type": "semantic",
            "content": "Hello world",
            "status": "active"
        },
        timestamp=datetime.now(timezone.utc)
    )
    
    payload = ReplicationPayload(
        payload_id=payload_id,
        origin_node_id=remote_node_id,
        scope_type="global",
        scope_id="global",
        mutations=[mutation]
    )
    
    # First apply
    stats1 = sync_manager.apply_payload(payload)
    assert stats1["applied"] == 1
    assert stats1["skipped"] == 0
    assert stats1["errors"] == 0
    
    # Verify memory exists
    row = db.fetch_one("SELECT content, origin_node_id FROM memories WHERE id = ?", (memory_id,))
    assert row is not None
    assert row["content"] == "Hello world"
    assert row["origin_node_id"] == remote_node_id
    
    # Verify audit log exists
    audit_row = db.fetch_one("SELECT status FROM replication_audit_log WHERE payload_id = ?", (payload_id,))
    assert audit_row is not None
    assert audit_row["status"] == "applied"
    
    # Second apply (replay)
    stats2 = sync_manager.apply_payload(payload)
    assert stats2["applied"] == 0
    assert stats2["skipped"] == 1
    assert stats2["errors"] == 0
    
    # Verify no duplicate records
    count = db.fetch_one("SELECT count(*) as c FROM memories WHERE id = ?", (memory_id,))
    assert count["c"] == 1
    
    audit_count = db.fetch_one("SELECT count(*) as c FROM replication_audit_log WHERE payload_id = ?", (payload_id,))
    assert audit_count["c"] == 1

def test_apply_payload_multiple_mutations(db, sync_manager):
    remote_node_id = str(uuid.uuid4())
    payload_id = str(uuid.uuid4())
    
    mem1_id = str(uuid.uuid4())
    mem2_id = str(uuid.uuid4())
    
    mut1 = Mutation("upsert", "memory", mem1_id, {"id": mem1_id, "content": "Mem 1"}, datetime.now(timezone.utc))
    mut2 = Mutation("upsert", "memory", mem2_id, {"id": mem2_id, "content": "Mem 2"}, datetime.now(timezone.utc))
    
    payload = ReplicationPayload(payload_id, remote_node_id, "global", "global", [mut1, mut2])
    
    stats = sync_manager.apply_payload(payload)
    assert stats["applied"] == 2
    
    assert db.fetch_one("SELECT count(*) as c FROM memories")["c"] == 2
    
    # Partial replay: Create new payload with same payload_id and one new mutation (simulating interrupted batch or something)
    # Wait, idempotency is checked by payload_id AND entity_id.
    mem3_id = str(uuid.uuid4())
    mut3 = Mutation("upsert", "memory", mem3_id, {"id": mem3_id, "content": "Mem 3"}, datetime.now(timezone.utc))
    
    payload_interrupted = ReplicationPayload(payload_id, remote_node_id, "global", "global", [mut1, mut2, mut3])
    stats2 = sync_manager.apply_payload(payload_interrupted)
    
    assert stats2["skipped"] == 2  # mut1, mut2 already applied
    assert stats2["applied"] == 1  # mut3 is new
    
    assert db.fetch_one("SELECT count(*) as c FROM memories")["c"] == 3

def test_apply_payload_with_conflict(db, sync_manager):
    # Simulate an existing local memory created by local node
    memory_id = str(uuid.uuid4())
    local_origin = "local-node-1"
    
    # We must register the local node if we are setting it directly
    db.execute("INSERT INTO node_identities (node_id, is_local, name, created_at) VALUES (?, 1, 'local', '2023-01-01')", (local_origin,))
    
    db.execute(
        "INSERT INTO memories (id, type, scope_type, scope_id, content, source_kind, status, origin_node_id, created_at, updated_at) "
        "VALUES (?, 'semantic', 'global', 'global', 'Local content', 'user', 'active', ?, '2023-01-01', '2023-01-01')",
        (memory_id, local_origin)
    )
    
    remote_node_id = str(uuid.uuid4())
    payload_id = str(uuid.uuid4())
    
    mut1 = Mutation("upsert", "memory", memory_id, {"id": memory_id, "content": "Remote content"}, datetime.now(timezone.utc))
    payload = ReplicationPayload(payload_id, remote_node_id, "global", "global", [mut1])
    
    stats = sync_manager.apply_payload(payload)
    
    # Check stats
    assert stats["conflicts"] == 1
    
    # Verify memory is in reconcile_required status
    row = db.fetch_one("SELECT content, status FROM memories WHERE id = ?", (memory_id,))
    assert row["status"] == "reconcile_required"
    # Content still gets updated to incoming (for now, as per simple upsert logic) but marked as conflict
    assert row["content"] == "Remote content"
    
    # Verify audit log shows conflict
    audit_row = db.fetch_one("SELECT status FROM replication_audit_log WHERE payload_id = ?", (payload_id,))
    assert audit_row["status"] == "conflict"
