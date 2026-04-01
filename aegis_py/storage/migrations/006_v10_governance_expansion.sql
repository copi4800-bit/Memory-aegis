CREATE TABLE IF NOT EXISTS review_queue (
    id                TEXT PRIMARY KEY,
    memory_id         TEXT NOT NULL,
    reason            TEXT NOT NULL,
    priority          REAL NOT NULL DEFAULT 0,
    status            TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'dismissed')),
    context_json      TEXT NOT NULL DEFAULT '{}',
    created_at        TEXT NOT NULL,
    resolved_at       TEXT,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fact_slots (
    slot_id           TEXT PRIMARY KEY,
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    current_winner_id TEXT,
    status            TEXT NOT NULL DEFAULT 'stable' CHECK (status IN ('stable', 'disputed', 'pending_review')),
    last_resolution_at TEXT,
    metadata_json     TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (current_winner_id) REFERENCES memories(id) ON DELETE SET NULL,
    UNIQUE (slot_id, scope_type, scope_id)
);

CREATE INDEX IF NOT EXISTS idx_review_queue_priority ON review_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_fact_slots_scope ON fact_slots(scope_type, scope_id);
