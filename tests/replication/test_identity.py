import pytest
import sqlite3
import os
from aegis_py.storage.db import DatabaseManager
from aegis_py.replication.identity import IdentityManager

@pytest.fixture
def temp_db():
    db = DatabaseManager(":memory:")
    db.initialize()
    # Ensure our new schema tables are created in the memory db
    # We added them to schema.sql, so initialize() will create them.
    yield db
    db.close()

def test_get_local_identity(temp_db):
    identity_manager = IdentityManager(temp_db)
    
    # First call generates it
    ident1 = identity_manager.get_local_identity()
    assert ident1.is_local is True
    assert ident1.node_id is not None
    assert len(ident1.node_id) > 0
    
    # Second call retrieves it
    ident2 = identity_manager.get_local_identity()
    assert ident1.node_id == ident2.node_id
    assert ident1.created_at == ident2.created_at

def test_register_remote_identity(temp_db):
    identity_manager = IdentityManager(temp_db)
    remote_id = "remote-node-123"
    remote_name = "test-remote"
    
    # First call registers it
    ident1 = identity_manager.register_remote_identity(remote_id, remote_name)
    assert ident1.is_local is False
    assert ident1.node_id == remote_id
    assert ident1.name == remote_name
    
    # Second call retrieves it
    ident2 = identity_manager.register_remote_identity(remote_id, "different-name")
    assert ident1.node_id == ident2.node_id
    assert ident1.created_at == ident2.created_at
    # The name should remain the original registered name
    assert ident2.name == remote_name

def test_migration_script(tmp_path):
    db_file = tmp_path / "test_migration.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create an old schema
    cursor.execute('''
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            scope_id TEXT NOT NULL,
            session_id TEXT,
            content TEXT NOT NULL,
            summary TEXT,
            subject TEXT,
            source_kind TEXT NOT NULL,
            source_ref TEXT,
            status TEXT NOT NULL DEFAULT 'active' CHECK (
                status IN ('active', 'archived', 'expired', 'conflict_candidate', 'superseded')
            ),
            confidence REAL NOT NULL DEFAULT 1.0,
            activation_score REAL NOT NULL DEFAULT 1.0,
            access_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_accessed_at TEXT,
            expires_at TEXT,
            archived_at TEXT,
            metadata_json TEXT
        )
    ''')
    cursor.execute("INSERT INTO memories (id, type, scope_type, scope_id, content, source_kind, created_at, updated_at) VALUES ('1', 'semantic', 'global', 'global', 'test content', 'user', '2023-01-01', '2023-01-01')")
    conn.commit()
    conn.close()
    
    # Run migration script
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))
    from migrate_042_managed_scope_replication import migrate
    migrate(str(db_file))
    
    # Verify migration
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Check new tables exist
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='node_identities'")
    assert cursor.fetchone()[0] == 1
    
    # Check memories has new column
    cursor.execute("PRAGMA table_info(memories)")
    columns = [row[1] for row in cursor.fetchall()]
    assert 'origin_node_id' in columns
    
    # Data is preserved
    cursor.execute("SELECT id, origin_node_id FROM memories WHERE id='1'")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == '1'
    assert row[1] is None
    
    conn.close()
