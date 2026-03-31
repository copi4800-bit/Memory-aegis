PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS node_identities (
    node_id           TEXT PRIMARY KEY,
    is_local          INTEGER NOT NULL DEFAULT 0 CHECK (is_local IN (0, 1)),
    name              TEXT,
    created_at        TEXT NOT NULL
);

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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS memories (
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
        status IN ('active', 'archived', 'expired', 'conflict_candidate', 'superseded', 'reconcile_required', 'crystallized')
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
);

CREATE TABLE IF NOT EXISTS memory_links (
    id                TEXT PRIMARY KEY,
    source_id         TEXT NOT NULL,
    target_id         TEXT NOT NULL,
    link_type         TEXT NOT NULL,
    weight            REAL NOT NULL DEFAULT 1.0,
    metadata_json     TEXT,
    created_at        TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES memories(id) ON DELETE CASCADE,
    UNIQUE (source_id, target_id, link_type),
    CHECK (source_id != target_id)
);

CREATE TABLE IF NOT EXISTS conflicts (
    id                TEXT PRIMARY KEY,
    memory_a_id       TEXT NOT NULL,
    memory_b_id       TEXT NOT NULL,
    subject_key       TEXT,
    score             REAL NOT NULL DEFAULT 0,
    reason            TEXT,
    resolution        TEXT,
    status            TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'dismissed', 'suggested')),
    created_at        TEXT NOT NULL,
    resolved_at       TEXT,
    FOREIGN KEY (memory_a_id) REFERENCES memories(id) ON DELETE CASCADE,
    FOREIGN KEY (memory_b_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS style_signals (
    id                TEXT PRIMARY KEY,
    session_id        TEXT,
    scope_id          TEXT,
    scope_type        TEXT,
    signal_key        TEXT,
    signal_value      TEXT,
    agent_id          TEXT,
    signal            TEXT,
    weight            REAL NOT NULL DEFAULT 1.0,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS style_profiles (
    id                TEXT PRIMARY KEY,
    scope_id          TEXT NOT NULL,
    scope_type        TEXT NOT NULL,
    preferences_json  TEXT NOT NULL,
    last_updated      TEXT NOT NULL,
    UNIQUE (scope_id, scope_type)
);

CREATE TABLE IF NOT EXISTS scope_policies (
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    sync_policy       TEXT NOT NULL DEFAULT 'local_only' CHECK (sync_policy IN ('local_only', 'sync_eligible')),
    sync_state        TEXT NOT NULL DEFAULT 'local' CHECK (sync_state IN ('local', 'pending_sync', 'synced', 'sync_error')),
    last_sync_at      TEXT,
    updated_at        TEXT NOT NULL,
    PRIMARY KEY (scope_type, scope_id)
);

CREATE TABLE IF NOT EXISTS scope_revisions (
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    revision          INTEGER NOT NULL DEFAULT 0,
    updated_at        TEXT NOT NULL,
    PRIMARY KEY (scope_type, scope_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    summary,
    subject,
    content='memories',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, summary, subject)
    VALUES (new.rowid, new.content, new.summary, new.subject);
END;

CREATE TRIGGER IF NOT EXISTS memories_bd BEFORE DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, summary, subject)
    VALUES ('delete', old.rowid, old.content, old.summary, old.subject);
END;

CREATE TRIGGER IF NOT EXISTS memories_bu BEFORE UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, summary, subject)
    VALUES ('delete', old.rowid, old.content, old.summary, old.subject);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, summary, subject)
    VALUES (new.rowid, new.content, new.summary, new.subject);
END;

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);
CREATE INDEX IF NOT EXISTS idx_memories_last_accessed ON memories(last_accessed_at);
CREATE INDEX IF NOT EXISTS idx_memories_subject ON memories(subject);
CREATE INDEX IF NOT EXISTS idx_links_source ON memory_links(source_id);
CREATE INDEX IF NOT EXISTS idx_links_target ON memory_links(target_id);
CREATE INDEX IF NOT EXISTS idx_links_type ON memory_links(link_type);
CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(status);
CREATE INDEX IF NOT EXISTS idx_conflicts_subject_key ON conflicts(subject_key);
CREATE INDEX IF NOT EXISTS idx_conflicts_memory_a ON conflicts(memory_a_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_memory_b ON conflicts(memory_b_id);
CREATE INDEX IF NOT EXISTS idx_style_signals_session ON style_signals(session_id);
CREATE INDEX IF NOT EXISTS idx_style_signals_agent ON style_signals(agent_id);
CREATE INDEX IF NOT EXISTS idx_style_profiles_scope ON style_profiles(scope_id, scope_type);
CREATE INDEX IF NOT EXISTS idx_scope_policies_policy ON scope_policies(sync_policy);
CREATE INDEX IF NOT EXISTS idx_scope_revisions_updated ON scope_revisions(updated_at);
