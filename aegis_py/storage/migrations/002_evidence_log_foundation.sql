CREATE TABLE IF NOT EXISTS evidence_events (
    id                TEXT PRIMARY KEY,
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    session_id        TEXT,
    memory_id         TEXT,
    source_kind       TEXT NOT NULL,
    source_ref        TEXT,
    raw_content       TEXT NOT NULL,
    metadata_json     TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_scope_created
    ON evidence_events(scope_type, scope_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_memory
    ON evidence_events(memory_id, created_at DESC);
