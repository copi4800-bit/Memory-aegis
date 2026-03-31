import sqlite3
import sys
import os

def migrate(db_path: str):
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Create new tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS node_identities (
            node_id           TEXT PRIMARY KEY,
            is_local          INTEGER NOT NULL DEFAULT 0 CHECK (is_local IN (0, 1)),
            name              TEXT,
            created_at        TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS replication_audit_log (
            id                TEXT PRIMARY KEY,
            payload_id        TEXT NOT NULL,
            origin_node_id    TEXT NOT NULL,
            entity_type       TEXT NOT NULL,
            entity_id         TEXT NOT NULL,
            action            TEXT NOT NULL,
            applied_at        TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'applied' CHECK (status IN ('applied', 'failed', 'conflict')),
            details_json      TEXT,
            FOREIGN KEY (origin_node_id) REFERENCES node_identities(node_id)
        )
    ''')
    
    # 2. Check if memories table has origin_node_id
    cursor.execute("PRAGMA table_info(memories)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'origin_node_id' not in columns:
        print("Migrating 'memories' table to add origin_node_id and update status CHECK constraint...")
        
        # We need to recreate the table to update the CHECK constraint
        cursor.execute("PRAGMA foreign_keys=off")
        cursor.execute("BEGIN TRANSACTION")
        
        cursor.execute('''
            CREATE TABLE memories_new (
                id                TEXT PRIMARY KEY,
                type              TEXT NOT NULL CHECK (type IN ('working', 'episodic', 'semantic', 'procedural')),
                scope_type        TEXT NOT NULL,
                scope_id          TEXT NOT NULL,
                session_id        TEXT,
                content           TEXT NOT NULL,
                summary           TEXT,
                subject           TEXT,
                source_kind       TEXT NOT NULL,
                source_ref        TEXT,
                origin_node_id    TEXT,
                status            TEXT NOT NULL DEFAULT 'active' CHECK (
                    status IN ('active', 'archived', 'expired', 'conflict_candidate', 'superseded', 'reconcile_required')
                ),
                confidence        REAL NOT NULL DEFAULT 1.0,
                activation_score  REAL NOT NULL DEFAULT 1.0,
                access_count      INTEGER NOT NULL DEFAULT 0,
                created_at        TEXT NOT NULL,
                updated_at        TEXT NOT NULL,
                last_accessed_at  TEXT,
                expires_at        TEXT,
                archived_at       TEXT,
                metadata_json     TEXT,
                FOREIGN KEY (origin_node_id) REFERENCES node_identities(node_id)
            )
        ''')
        
        old_cols = ', '.join(columns)
        insert_cols = old_cols + ', origin_node_id'
        select_cols = old_cols + ', NULL'
        
        cursor.execute(f"INSERT INTO memories_new ({insert_cols}) SELECT {select_cols} FROM memories")
        cursor.execute("DROP TABLE memories")
        cursor.execute("ALTER TABLE memories_new RENAME TO memories")
        
        # Recreate indexes and triggers that might have been dropped
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope_type, scope_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_last_accessed ON memories(last_accessed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_subject ON memories(subject)")
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, summary, subject)
                VALUES (new.rowid, new.content, new.summary, new.subject);
            END;
        ''')
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_bd BEFORE DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, summary, subject)
                VALUES ('delete', old.rowid, old.content, old.summary, old.subject);
            END;
        ''')
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_bu BEFORE UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, content, summary, subject)
                VALUES ('delete', old.rowid, old.content, old.summary, old.subject);
            END;
        ''')
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(rowid, content, summary, subject)
                VALUES (new.rowid, new.content, new.summary, new.subject);
            END;
        ''')
        
        cursor.execute("COMMIT")
        cursor.execute("PRAGMA foreign_keys=on")
        print("Migration complete.")
    else:
        print("Database already up to date with origin_node_id.")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    default_db = os.path.join(os.path.dirname(__file__), '..', 'memory_aegis.db')
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db
    migrate(db_path)
