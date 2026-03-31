CREATE TABLE IF NOT EXISTS memory_state_transitions (
    id                TEXT PRIMARY KEY,
    memory_id         TEXT NOT NULL,
    from_state        TEXT,
    to_state          TEXT NOT NULL,
    reason            TEXT NOT NULL,
    actor             TEXT NOT NULL DEFAULT 'system',
    policy_name       TEXT,
    evidence_event_id TEXT,
    details_json      TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS governance_events (
    id                TEXT PRIMARY KEY,
    event_kind        TEXT NOT NULL,
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    memory_id         TEXT,
    evidence_event_id TEXT,
    payload_json      TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS background_intelligence_runs (
    id                TEXT PRIMARY KEY,
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    worker_kind       TEXT NOT NULL,
    mode              TEXT NOT NULL DEFAULT 'working_copy',
    status            TEXT NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'shadowed', 'applied', 'discarded')),
    proposal_json     TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_state_transitions_memory
    ON memory_state_transitions(memory_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_governance_events_scope
    ON governance_events(scope_type, scope_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_governance_events_memory
    ON governance_events(memory_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_background_intelligence_scope
    ON background_intelligence_runs(scope_type, scope_id, created_at DESC);
