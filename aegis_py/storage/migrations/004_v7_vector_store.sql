CREATE TABLE IF NOT EXISTS memory_vectors (
    memory_id         TEXT PRIMARY KEY,
    scope_type        TEXT NOT NULL,
    scope_id          TEXT NOT NULL,
    token_count       INTEGER NOT NULL DEFAULT 0,
    embedding_json    TEXT NOT NULL DEFAULT '{}',
    updated_at        TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_vectors_scope
    ON memory_vectors(scope_type, scope_id, updated_at DESC);
