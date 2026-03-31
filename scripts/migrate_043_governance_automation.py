import sqlite3
import sys
import os

def migrate(db_path: str):
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create new tables for Tranche B: Governance Automation
    
    print("Creating policy_matrix table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS policy_matrix (
            id                TEXT PRIMARY KEY,
            scope_type        TEXT NOT NULL,
            scope_id          TEXT NOT NULL,
            auto_resolve      INTEGER NOT NULL DEFAULT 0 CHECK (auto_resolve IN (0, 1)),
            auto_archive      INTEGER NOT NULL DEFAULT 0 CHECK (auto_archive IN (0, 1)),
            auto_consolidate  INTEGER NOT NULL DEFAULT 0 CHECK (auto_consolidate IN (0, 1)),
            auto_escalate     INTEGER NOT NULL DEFAULT 0 CHECK (auto_escalate IN (0, 1)),
            updated_at        TEXT NOT NULL,
            UNIQUE (scope_type, scope_id)
        )
    ''')
    
    print("Creating autonomous_audit_log table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_audit_log (
            id                TEXT PRIMARY KEY,
            action_type       TEXT NOT NULL,
            entity_type       TEXT NOT NULL,
            entity_id         TEXT NOT NULL,
            explanation       TEXT NOT NULL,
            confidence_score  REAL,
            applied_at        TEXT NOT NULL,
            status            TEXT NOT NULL DEFAULT 'applied' CHECK (status IN ('applied', 'rolled_back', 'failed')),
            details_json      TEXT,
            rolled_back_at    TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    default_db = os.path.join(os.path.dirname(__file__), '..', 'memory_aegis.db')
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db
    migrate(db_path)
