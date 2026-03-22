PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ============================================================
-- Schema Version Tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL,
    applied_at TEXT NOT NULL,
    description TEXT
);

INSERT OR IGNORE INTO schema_version(version, applied_at, description)
VALUES (4, datetime('now'), 'Memory Aegis v4 schema');

CREATE TABLE IF NOT EXISTS memory_nodes (
    id TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    canonical_subject TEXT,
    scope TEXT,
    tier TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    importance REAL NOT NULL DEFAULT 0,
    salience REAL NOT NULL DEFAULT 0,
    activation_score REAL NOT NULL DEFAULT 0,
    base_decay_rate REAL NOT NULL DEFAULT 0,
    stability_score REAL NOT NULL DEFAULT 0,
    interference_score REAL NOT NULL DEFAULT 0,
    override_priority INTEGER NOT NULL DEFAULT 0,
    memory_state TEXT NOT NULL DEFAULT 'volatile',
    recall_count INTEGER NOT NULL DEFAULT 0,
    frequency_count INTEGER NOT NULL DEFAULT 0,
    reusability_score REAL NOT NULL DEFAULT 0,
    approval_score REAL NOT NULL DEFAULT 0,
    raw_hash TEXT,
    normalized_hash TEXT,
    structure_hash TEXT,
    fingerprint_version TEXT,
    drift_status TEXT,
    ttl_expires_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    first_seen_at TEXT,
    last_seen_at TEXT,
    last_access_at TEXT,
    crystallized_at TEXT,
    extension_json TEXT,
    -- Episodic Memory (Scrub Jay)
    episode_id TEXT,
    -- Source tracking for OpenClaw compatibility
    source_path TEXT,
    source_start_line INTEGER,
    source_end_line INTEGER,
    CHECK (memory_state IN ('volatile', 'stable', 'crystallized', 'suppressed', 'archived')),
    CHECK (status IN ('active', 'expired', 'merged', 'deleted', 'superseded')),
    CHECK (importance >= 0 AND importance <= 1),
    CHECK (salience >= 0 AND salience <= 1),
    CHECK (base_decay_rate >= 0),
    CHECK (stability_score >= 0 AND stability_score <= 1),
    CHECK (interference_score >= 0 AND interference_score <= 1),
    CHECK (override_priority >= 0)
);

CREATE INDEX IF NOT EXISTS idx_memory_nodes_type ON memory_nodes(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_scope ON memory_nodes(scope);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_subject ON memory_nodes(canonical_subject);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_state ON memory_nodes(memory_state);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_status ON memory_nodes(status);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_normalized_hash ON memory_nodes(normalized_hash);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_last_access ON memory_nodes(last_access_at);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_ttl ON memory_nodes(ttl_expires_at);

CREATE TABLE IF NOT EXISTS memory_edges (
    id TEXT PRIMARY KEY,
    src_node_id TEXT NOT NULL,
    dst_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 0,
    confidence REAL NOT NULL DEFAULT 0,
    scope TEXT,
    tier TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    coactivation_count INTEGER NOT NULL DEFAULT 0,
    last_activated_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    extension_json TEXT,
    FOREIGN KEY(src_node_id) REFERENCES memory_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(dst_node_id) REFERENCES memory_nodes(id) ON DELETE CASCADE,
    CHECK (status IN ('active', 'weakened', 'pruned')),
    CHECK (weight >= 0 AND weight <= 1),
    CHECK (confidence >= 0 AND confidence <= 1),
    CHECK (coactivation_count >= 0)
);

CREATE INDEX IF NOT EXISTS idx_memory_edges_src ON memory_edges(src_node_id);
CREATE INDEX IF NOT EXISTS idx_memory_edges_dst ON memory_edges(dst_node_id);
CREATE INDEX IF NOT EXISTS idx_memory_edges_type ON memory_edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_memory_edges_src_type ON memory_edges(src_node_id, edge_type);
CREATE INDEX IF NOT EXISTS idx_memory_edges_dst_type ON memory_edges(dst_node_id, edge_type);

CREATE VIRTUAL TABLE IF NOT EXISTS memory_nodes_fts USING fts5(
    content,
    canonical_subject,
    scope,
    memory_type,
    content='memory_nodes',
    content_rowid='rowid',
    tokenize="porter unicode61"
);

-- ============================================================
-- FTS5 Sync Triggers (CRITICAL — without these, FTS index goes stale)
-- ============================================================

-- After INSERT: add new content to FTS index
CREATE TRIGGER IF NOT EXISTS trg_memory_nodes_ai AFTER INSERT ON memory_nodes BEGIN
    INSERT INTO memory_nodes_fts(rowid, content, canonical_subject, scope, memory_type)
    VALUES (new.rowid, new.content, new.canonical_subject, new.scope, new.memory_type);
END;

-- Before DELETE: remove old content from FTS index
CREATE TRIGGER IF NOT EXISTS trg_memory_nodes_bd BEFORE DELETE ON memory_nodes BEGIN
    INSERT INTO memory_nodes_fts(memory_nodes_fts, rowid, content, canonical_subject, scope, memory_type)
    VALUES ('delete', old.rowid, old.content, old.canonical_subject, old.scope, old.memory_type);
END;

-- Before UPDATE: remove old, then after update re-add new
CREATE TRIGGER IF NOT EXISTS trg_memory_nodes_bu BEFORE UPDATE ON memory_nodes BEGIN
    INSERT INTO memory_nodes_fts(memory_nodes_fts, rowid, content, canonical_subject, scope, memory_type)
    VALUES ('delete', old.rowid, old.content, old.canonical_subject, old.scope, old.memory_type);
END;

CREATE TRIGGER IF NOT EXISTS trg_memory_nodes_au AFTER UPDATE ON memory_nodes BEGIN
    INSERT INTO memory_nodes_fts(rowid, content, canonical_subject, scope, memory_type)
    VALUES (new.rowid, new.content, new.canonical_subject, new.scope, new.memory_type);
END;

CREATE TABLE IF NOT EXISTS fingerprints (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    raw_hash TEXT,
    normalized_hash TEXT,
    structure_hash TEXT,
    fingerprint_version TEXT NOT NULL,
    normalization_profile TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES memory_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_fingerprints_node ON fingerprints(node_id);
CREATE INDEX IF NOT EXISTS idx_fingerprints_raw ON fingerprints(raw_hash);
CREATE INDEX IF NOT EXISTS idx_fingerprints_normalized ON fingerprints(normalized_hash);
CREATE INDEX IF NOT EXISTS idx_fingerprints_structure ON fingerprints(structure_hash);

CREATE TABLE IF NOT EXISTS drift_events (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    baseline_fingerprint_id TEXT NOT NULL,
    current_fingerprint_id TEXT NOT NULL,
    drift_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    diff_required INTEGER NOT NULL DEFAULT 0,
    resolved INTEGER NOT NULL DEFAULT 0,
    detected_at TEXT NOT NULL,
    resolved_at TEXT,
    extension_json TEXT,
    FOREIGN KEY(node_id) REFERENCES memory_nodes(id),
    FOREIGN KEY(baseline_fingerprint_id) REFERENCES fingerprints(id),
    FOREIGN KEY(current_fingerprint_id) REFERENCES fingerprints(id)
);

CREATE INDEX IF NOT EXISTS idx_drift_events_node ON drift_events(node_id);
CREATE INDEX IF NOT EXISTS idx_drift_events_resolved ON drift_events(resolved);

CREATE TABLE IF NOT EXISTS dedup_routes (
    id TEXT PRIMARY KEY,
    fingerprint_id TEXT NOT NULL,
    scope TEXT,
    source_event_id TEXT,
    target_node_id TEXT NOT NULL,
    reuse_action TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(fingerprint_id) REFERENCES fingerprints(id),
    FOREIGN KEY(target_node_id) REFERENCES memory_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_dedup_routes_fingerprint ON dedup_routes(fingerprint_id);
CREATE INDEX IF NOT EXISTS idx_dedup_routes_target ON dedup_routes(target_node_id);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    scope TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    extension_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(canonical_name);

CREATE TABLE IF NOT EXISTS entity_aliases (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    alias_text TEXT NOT NULL,
    alias_kind TEXT,
    confidence REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(entity_id) REFERENCES entities(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_entity_aliases_entity_text ON entity_aliases(entity_id, alias_text);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_entity ON entity_aliases(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_text ON entity_aliases(alias_text);

CREATE TABLE IF NOT EXISTS concept_nodes (
    id TEXT PRIMARY KEY,
    concept_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    override_policy TEXT,
    valid_from TEXT,
    valid_to TEXT,
    confidence REAL NOT NULL DEFAULT 0,
    rule_payload_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concept_inheritance (
    id TEXT PRIMARY KEY,
    src_kind TEXT NOT NULL,
    src_id TEXT NOT NULL,
    dst_kind TEXT NOT NULL,
    dst_id TEXT NOT NULL,
    inheritance_type TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_concept_inheritance_src ON concept_inheritance(src_kind, src_id);
CREATE INDEX IF NOT EXISTS idx_concept_inheritance_dst ON concept_inheritance(dst_kind, dst_id);

CREATE TABLE IF NOT EXISTS derived_relations (
    id TEXT PRIMARY KEY,
    src_node_id TEXT NOT NULL,
    dst_node_id TEXT NOT NULL,
    derivation_type TEXT NOT NULL,
    derivation_path_json TEXT NOT NULL,
    derivation_depth INTEGER NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    expires_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(src_node_id) REFERENCES memory_nodes(id),
    FOREIGN KEY(dst_node_id) REFERENCES memory_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_derived_relations_src ON derived_relations(src_node_id);
CREATE INDEX IF NOT EXISTS idx_derived_relations_dst ON derived_relations(dst_node_id);
CREATE INDEX IF NOT EXISTS idx_derived_relations_type ON derived_relations(derivation_type);

CREATE TABLE IF NOT EXISTS temporal_patterns (
    id TEXT PRIMARY KEY,
    scope TEXT,
    entity_anchor TEXT,
    pattern_type TEXT NOT NULL,
    cadence_json TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    next_expected_at TEXT,
    last_triggered_at TEXT,
    prewarm_policy TEXT,
    suppression_policy TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS procedures (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    subject TEXT,
    scope TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    trigger_text TEXT,
    trigger_kind TEXT,
    reusability_score REAL NOT NULL DEFAULT 0,
    approval_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    extension_json TEXT
);

CREATE TABLE IF NOT EXISTS procedure_steps (
    id TEXT PRIMARY KEY,
    procedure_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    step_text TEXT NOT NULL,
    step_kind TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(procedure_id) REFERENCES procedures(id)
);

CREATE INDEX IF NOT EXISTS idx_procedure_steps_procedure ON procedure_steps(procedure_id, step_index);

CREATE TABLE IF NOT EXISTS tool_artifacts (
    id TEXT PRIMARY KEY,
    node_id TEXT,
    artifact_type TEXT NOT NULL,
    language TEXT,
    entry_command TEXT,
    source_text TEXT NOT NULL,
    input_contract_json TEXT,
    output_contract_json TEXT,
    sandbox_profile TEXT,
    timeout_policy TEXT,
    approval_required INTEGER NOT NULL DEFAULT 1,
    reusability_score REAL NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES memory_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_tool_artifacts_type ON tool_artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_tool_artifacts_last_used ON tool_artifacts(last_used_at);

CREATE TABLE IF NOT EXISTS correction_traces (
    id TEXT PRIMARY KEY,
    scope TEXT,
    context_snapshot TEXT NOT NULL,
    agent_proposal TEXT,
    user_correction TEXT NOT NULL,
    final_accepted_form TEXT,
    correction_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    applies_to_json TEXT,
    created_at TEXT NOT NULL,
    last_reused_at TEXT
);

CREATE TABLE IF NOT EXISTS interaction_states (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE,
    frustration_index REAL NOT NULL DEFAULT 0,
    brevity_preference REAL NOT NULL DEFAULT 0,
    exploration_preference REAL NOT NULL DEFAULT 0,
    correction_pressure REAL NOT NULL DEFAULT 0,
    formality_preference REAL NOT NULL DEFAULT 0,
    last_updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_interaction_states_session ON interaction_states(session_id);

CREATE TABLE IF NOT EXISTS context_textures (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scope TEXT,
    tone_profile TEXT,
    format_profile TEXT,
    verbosity_profile TEXT,
    tooling_bias TEXT,
    guardrail_profile TEXT,
    activation_rules_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subgraph_partitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    scope TEXT,
    partition_type TEXT NOT NULL,
    activation_policy TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subgraph_memberships (
    id TEXT PRIMARY KEY,
    partition_id TEXT NOT NULL,
    member_kind TEXT NOT NULL,
    member_id TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(partition_id) REFERENCES subgraph_partitions(id)
);

CREATE INDEX IF NOT EXISTS idx_subgraph_memberships_partition ON subgraph_memberships(partition_id);
CREATE INDEX IF NOT EXISTS idx_subgraph_memberships_member ON subgraph_memberships(member_kind, member_id);

CREATE TABLE IF NOT EXISTS memory_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    node_id TEXT,
    scope TEXT,
    session_id TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES memory_nodes(id)
);

CREATE INDEX IF NOT EXISTS idx_memory_events_type ON memory_events(event_type);
CREATE INDEX IF NOT EXISTS idx_memory_events_node ON memory_events(node_id);
CREATE INDEX IF NOT EXISTS idx_memory_events_session ON memory_events(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_events_created ON memory_events(created_at);

-- ============================================================
-- Composite Indexes for Retrieval Pipeline Performance
-- ============================================================

-- Reranking: filter active nodes then sort by score signals
CREATE INDEX IF NOT EXISTS idx_memory_nodes_active_rerank
    ON memory_nodes(status, memory_state, importance DESC, salience DESC)
    WHERE status = 'active';

-- Source path lookup (for readFile and OpenClaw compatibility)
CREATE INDEX IF NOT EXISTS idx_memory_nodes_source_path
    ON memory_nodes(source_path)
    WHERE source_path IS NOT NULL;

-- Elephant override fast lookup
CREATE INDEX IF NOT EXISTS idx_memory_nodes_override
    ON memory_nodes(memory_type, override_priority DESC)
    WHERE memory_type IN ('trauma', 'invariant') AND status = 'active';

-- TTL expiry scan (Nutcracker maintenance)
CREATE INDEX IF NOT EXISTS idx_memory_nodes_ttl_active
    ON memory_nodes(ttl_expires_at)
    WHERE ttl_expires_at IS NOT NULL AND status = 'active';

-- Session-scoped nodes for session key boosting
CREATE INDEX IF NOT EXISTS idx_memory_nodes_scope_session
    ON memory_nodes(scope, created_at DESC)
    WHERE scope IS NOT NULL;

-- ============================================================
-- Scrub Jay — Episodic Memory
-- ============================================================

CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    goal TEXT,
    context_summary TEXT,
    start_at TEXT NOT NULL,
    end_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(parent_id) REFERENCES episodes(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_episodes_type ON episodes(type);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status);
CREATE INDEX IF NOT EXISTS idx_episodes_start ON episodes(start_at);
CREATE INDEX IF NOT EXISTS idx_memory_nodes_episode ON memory_nodes(episode_id);

-- ============================================================
-- Honeybee Telemetry View
-- ============================================================

CREATE VIEW IF NOT EXISTS v_aegis_telemetry AS
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

-- ============================================================
-- Leafcutter Archive Log
-- ============================================================

CREATE TABLE IF NOT EXISTS archive_log (
    id TEXT PRIMARY KEY,
    archive_kind TEXT NOT NULL,
    file_path TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    compressed_bytes INTEGER,
    checksum TEXT,
    from_timestamp TEXT NOT NULL,
    to_timestamp TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_archive_log_kind ON archive_log(archive_kind);
CREATE INDEX IF NOT EXISTS idx_archive_log_created ON archive_log(created_at);
