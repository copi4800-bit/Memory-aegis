from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Iterable, Optional


class DatabaseManager:
    """SQLite connection manager for the Python Aegis runtime."""

    def __init__(self, db_path: str = "memory_aegis.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self.conn is None:
            if self.db_path != ":memory:":
                Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def initialize(self) -> None:
        conn = self.connect()
        migrations_dir = Path(__file__).parent / "migrations"
        
        from aegis_py.ops.migration import MigrationManager
        migrator = MigrationManager(conn, str(migrations_dir))
        migrator.run_migrations()

    def execute(self, query: str, params: Iterable = ()) -> sqlite3.Cursor:
        conn = self.connect()
        cursor = conn.execute(query, tuple(params))
        conn.commit()
        return cursor

    def executemany(self, query: str, rows: Iterable[Iterable]) -> None:
        conn = self.connect()
        conn.executemany(query, rows)
        conn.commit()

    def fetch_all(self, query: str, params: Iterable = ()) -> list[sqlite3.Row]:
        conn = self.connect()
        cursor = conn.execute(query, tuple(params))
        return cursor.fetchall()

    def fetch_one(self, query: str, params: Iterable = ()) -> sqlite3.Row | None:
        conn = self.connect()
        cursor = conn.execute(query, tuple(params))
        return cursor.fetchone()

    def put_memory(self, memory) -> str:
        from ..hygiene.transitions import now_iso

        memory_id = getattr(memory, "id", None) or str(uuid.uuid4())
        metadata = dict(getattr(memory, "metadata", {}) or {})
        now = now_iso()
        self.execute(
            """
            INSERT INTO memories (
                id, type, scope_type, scope_id, session_id, content, summary, subject,
                source_kind, source_ref, status, confidence, activation_score, access_count,
                created_at, updated_at, last_accessed_at, expires_at, archived_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                memory.type,
                memory.scope_type,
                memory.scope_id,
                getattr(memory, "session_id", None),
                memory.content,
                getattr(memory, "summary", None),
                getattr(memory, "subject", None),
                memory.source_kind,
                getattr(memory, "source_ref", None),
                getattr(memory, "status", "active"),
                getattr(memory, "confidence", 1.0),
                getattr(memory, "activation_score", 1.0),
                getattr(memory, "access_count", 0),
                now,
                now,
                getattr(memory, "last_accessed_at", None),
                getattr(memory, "expires_at", None),
                getattr(memory, "archived_at", None),
                json.dumps(metadata, ensure_ascii=True),
            ),
        )
        return memory_id

    def record_evidence_artifact(
        self,
        *,
        artifact_kind: str,
        scope_type: str,
        scope_id: str,
        payload: dict,
        memory_id: str | None = None,
        evidence_event_id: str | None = None,
    ) -> str:
        from ..hygiene.transitions import now_iso

        artifact_id = f"art_{uuid.uuid4().hex[:16]}"
        self.execute(
            """
            INSERT INTO evidence_artifacts (
                id, artifact_kind, scope_type, scope_id, memory_id, evidence_event_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                artifact_kind,
                scope_type,
                scope_id,
                memory_id,
                evidence_event_id,
                json.dumps(payload, ensure_ascii=True),
                now_iso(),
            ),
        )
        return artifact_id

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None
