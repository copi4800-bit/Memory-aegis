import type Database from "better-sqlite3";

export function getSchemaVersion(db: Database.Database): number {
  try {
    const row = db.prepare("SELECT MAX(version) as version FROM schema_version").get() as any;
    return row?.version ?? 0;
  } catch { return 0; }
}

function recordVersion(db: Database.Database, version: number, description: string): void {
  db.prepare("INSERT INTO schema_version (version, applied_at, description) VALUES (?, datetime('now'), ?)").run(version, description);
}

export function runMigrations(db: Database.Database): void {
  const current = getSchemaVersion(db);
  const migrations: Array<{ version: number; description: string; up: (db: Database.Database) => void; }> = [
    {
      version: 2,
      description: "Rebuild FTS5 index",
      up: (db) => {
        db.exec(`DROP TABLE IF EXISTS memory_nodes_fts; CREATE VIRTUAL TABLE memory_nodes_fts USING fts5(content, canonical_subject, scope, memory_type, content='memory_nodes', content_rowid='rowid', tokenize="porter unicode61"); INSERT INTO memory_nodes_fts(memory_nodes_fts) VALUES('rebuild');`);
      },
    },
    {
      version: 3,
      description: "Scrub Jay support",
      up: (db) => {
        db.exec(`CREATE TABLE IF NOT EXISTS episodes (id TEXT PRIMARY KEY, parent_id TEXT, type TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', goal TEXT, context_summary TEXT, start_at TEXT NOT NULL, end_at TEXT, created_at TEXT NOT NULL, FOREIGN KEY(parent_id) REFERENCES episodes(id) ON DELETE SET NULL); CREATE INDEX IF NOT EXISTS idx_episodes_type ON episodes(type); CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status); CREATE INDEX IF NOT EXISTS idx_episodes_start ON episodes(start_at); ALTER TABLE memory_nodes ADD COLUMN episode_id TEXT; CREATE INDEX IF NOT EXISTS idx_memory_nodes_episode ON memory_nodes(episode_id);`);
      },
    },
    {
      version: 4,
      description: "Zebra Finch — Enable 'superseded' status",
      up: (db) => {
        // Drop view that depends on memory_nodes
        db.exec("DROP VIEW IF EXISTS v_aegis_telemetry;");
        
        db.exec(`
          CREATE TABLE memory_nodes_new (
              id TEXT PRIMARY KEY, memory_type TEXT NOT NULL, content TEXT NOT NULL,
              canonical_subject TEXT, scope TEXT, tier TEXT,
              status TEXT NOT NULL DEFAULT 'active', importance REAL NOT NULL DEFAULT 0,
              salience REAL NOT NULL DEFAULT 0, activation_score REAL NOT NULL DEFAULT 0,
              base_decay_rate REAL NOT NULL DEFAULT 0, stability_score REAL NOT NULL DEFAULT 0,
              interference_score REAL NOT NULL DEFAULT 0, override_priority INTEGER NOT NULL DEFAULT 0,
              memory_state TEXT NOT NULL DEFAULT 'volatile', recall_count INTEGER NOT NULL DEFAULT 0,
              frequency_count INTEGER NOT NULL DEFAULT 0, reusability_score REAL NOT NULL DEFAULT 0,
              approval_score REAL NOT NULL DEFAULT 0, raw_hash TEXT, normalized_hash TEXT,
              structure_hash TEXT, fingerprint_version TEXT, drift_status TEXT,
              ttl_expires_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              first_seen_at TEXT, last_seen_at TEXT, last_access_at TEXT,
              crystallized_at TEXT, extension_json TEXT, episode_id TEXT,
              source_path TEXT, source_start_line INTEGER, source_end_line INTEGER,
              CHECK (memory_state IN ('volatile', 'stable', 'crystallized', 'suppressed', 'archived')),
              CHECK (status IN ('active', 'expired', 'merged', 'deleted', 'superseded')),
              CHECK (importance >= 0 AND importance <= 1), CHECK (salience >= 0 AND salience <= 1),
              CHECK (base_decay_rate >= 0), CHECK (stability_score >= 0 AND stability_score <= 1),
              CHECK (interference_score >= 0 AND interference_score <= 1), CHECK (override_priority >= 0)
          );
          INSERT INTO memory_nodes_new SELECT * FROM memory_nodes;
          DROP TABLE memory_nodes;
          ALTER TABLE memory_nodes_new RENAME TO memory_nodes;
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_type ON memory_nodes(memory_type);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_scope ON memory_nodes(scope);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_subject ON memory_nodes(canonical_subject);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_state ON memory_nodes(memory_state);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_status ON memory_nodes(status);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_normalized_hash ON memory_nodes(normalized_hash);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_last_access ON memory_nodes(last_access_at);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_ttl ON memory_nodes(ttl_expires_at);
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_active_rerank ON memory_nodes(status, memory_state, importance DESC, salience DESC) WHERE status = 'active';
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_source_path ON memory_nodes(source_path) WHERE source_path IS NOT NULL;
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_override ON memory_nodes(memory_type, override_priority DESC) WHERE memory_type IN ('trauma', 'invariant') AND status = 'active';
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_ttl_active ON memory_nodes(ttl_expires_at) WHERE ttl_expires_at IS NOT NULL AND status = 'active';
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_scope_session ON memory_nodes(scope, created_at DESC) WHERE scope IS NOT NULL;
          CREATE INDEX IF NOT EXISTS idx_memory_nodes_episode ON memory_nodes(episode_id);
        `);

        // Recreate view
        db.exec(`
          CREATE VIEW v_aegis_telemetry AS
          SELECT
              (SELECT COUNT(*) FROM memory_nodes WHERE status = 'active') as node_count_active,
              (SELECT COUNT(*) FROM memory_nodes WHERE status = 'superseded') as node_count_superseded,
              (SELECT COUNT(*) FROM memory_nodes WHERE memory_state = 'archived') as node_count_archived,
              (SELECT COUNT(*) FROM memory_edges WHERE status = 'active') as edge_count,
              (SELECT COUNT(*) FROM entities) as entity_count,
              (SELECT COUNT(*) FROM memory_events) as event_count,
              (SELECT COUNT(*) FROM dedup_routes) as dedup_hit_count,
              (SELECT COUNT(*) FROM derived_relations) as derived_relation_count,
              (SELECT COUNT(*) FROM interaction_states) as interaction_state_count,
              (SELECT COUNT(*) FROM drift_events WHERE resolved = 0) as unresolved_contradictions,
              (SELECT MAX(created_at) FROM memory_events WHERE event_type = 'backup_completed') as latest_backup_at,
              (SELECT MAX(created_at) FROM memory_events WHERE event_type = 'archive_completed') as latest_archive_at;
        `);
      },
    },
    {
      version: 5,
      description: "Dragonfly — Semantic-lite Synonym Expansion",
      up: (db) => {
        db.exec(`
          CREATE TABLE IF NOT EXISTS dragonfly_synonyms (
            word TEXT NOT NULL,
            synonym TEXT NOT NULL,
            category TEXT,
            confidence REAL NOT NULL DEFAULT 1.0,
            PRIMARY KEY (word, synonym)
          );
          CREATE INDEX IF NOT EXISTS idx_dragonfly_synonyms_word ON dragonfly_synonyms(word);
          
          -- Seed basic synonyms
          INSERT OR IGNORE INTO dragonfly_synonyms (word, synonym, category) VALUES
            ('setup', 'cài đặt', 'technical'),
            ('cài đặt', 'setup', 'technical'),
            ('start', 'khởi động', 'technical'),
            ('khởi động', 'start', 'technical'),
            ('dev', 'phát triển', 'technical'),
            ('phát triển', 'dev', 'technical'),
            ('update', 'cập nhật', 'technical'),
            ('cập nhật', 'update', 'technical'),
            ('fix', 'sửa lỗi', 'technical'),
            ('sửa lỗi', 'fix', 'technical'),
            ('delete', 'xóa', 'general'),
            ('xóa', 'delete', 'general'),
            ('login', 'đăng nhập', 'technical'),
            ('đăng nhập', 'login', 'technical');
        `);
      },
    },
    {
      version: 6,
      description: "Phase 3 Hardening — Bowerbird confidence + Weaver Bird versioning",
      up: (db) => {
        db.exec(`
          -- Bowerbird: taxonomy confidence per node
          ALTER TABLE memory_nodes ADD COLUMN taxonomy_confidence REAL;

          -- Weaver Bird: blueprint versioning
          ALTER TABLE memory_nodes ADD COLUMN blueprint_version INTEGER DEFAULT 0;
          ALTER TABLE memory_nodes ADD COLUMN blueprint_success_count INTEGER DEFAULT 0;
          ALTER TABLE memory_nodes ADD COLUMN blueprint_fail_count INTEGER DEFAULT 0;
        `);
      },
    },
  ];

  db.exec("PRAGMA foreign_keys = OFF;");
  try {
    for (const migration of migrations) {
      if (migration.version <= current) continue;
      const run = db.transaction(() => {
        migration.up(db);
        recordVersion(db, migration.version, migration.description);
      });
      run();
    }
  } finally {
    db.exec("PRAGMA foreign_keys = ON;");
  }
}

export function migrateFromBuiltin(aegisDb: Database.Database, builtinDbPath: string): number {
  aegisDb.exec(`ATTACH DATABASE '${builtinDbPath}' AS builtin`);
  let count = 0;
  try {
    const hasChunks = aegisDb.prepare("SELECT name FROM builtin.sqlite_master WHERE type='table' AND name='chunks'").get();
    if (!hasChunks) return 0;
    const chunks = aegisDb.prepare("SELECT id, path, start_line, end_line, text, source, updated_at FROM builtin.chunks WHERE text IS NOT NULL AND length(text) > 0").all() as any[];
    const now = new Date().toISOString();
    const insertNode = aegisDb.prepare("INSERT OR IGNORE INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, salience, memory_state, created_at, updated_at, first_seen_at, source_path, source_start_line, source_end_line) VALUES (?, 'semantic_fact', ?, NULL, ?, 'active', 0.3, 0.3, 'stable', ?, ?, ?, ?, ?, ?)");
    const migrate = aegisDb.transaction(() => {
      for (const chunk of chunks) {
        const scope = chunk.source === "sessions" ? "session" : "user";
        insertNode.run(chunk.id, chunk.text, scope, chunk.updated_at || now, chunk.updated_at || now, chunk.updated_at || now, chunk.path, chunk.start_line, chunk.end_line);
        count++;
      }
    });
    migrate();
  } finally { aegisDb.exec("DETACH DATABASE builtin"); }
  return count;
}
