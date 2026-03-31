CREATE TABLE IF NOT EXISTS evidence_artifacts (
    id                TEXT PRIMARY KEY,
    artifact_kind     TEXT NOT NULL,
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    memory_id         TEXT,
    evidence_event_id TEXT,
    payload_json      TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_scope
    ON evidence_artifacts(scope_type, scope_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_artifacts_memory
    ON evidence_artifacts(memory_id, created_at DESC);
