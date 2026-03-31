from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .models import Memory, SearchResult
from ..hygiene.transitions import transition_memory, now_iso
from ..retrieval.engine import run_scoped_search


def _dt_to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class MemoryManager:
    """Core storage and retrieval manager for the Python Aegis baseline."""

    def __init__(self, db_manager):
        self.db = db_manager

    def store(self, memory: Memory) -> str:
        memory_id = memory.id or str(uuid.uuid4())
        now = now_iso()
        metadata = dict(memory.metadata or {})
        if "evidence" not in metadata and self._table_exists("evidence_events"):
            event_id = f"evt_{uuid.uuid4().hex[:16]}"
            self.db.execute(
                """
                INSERT INTO evidence_events (
                    id, scope_type, scope_id, session_id, memory_id, source_kind,
                    source_ref, raw_content, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    memory.scope_type,
                    memory.scope_id,
                    memory.session_id,
                    memory_id,
                    memory.source_kind,
                    memory.source_ref,
                    memory.content,
                    json.dumps(
                        {
                            "capture_stage": "memory_core_store",
                            "memory_type": memory.type,
                        },
                        ensure_ascii=True,
                    ),
                    now,
                ),
            )
            metadata["evidence"] = {
                "event_id": event_id,
                "kind": "raw_ingest",
                "source_kind": memory.source_kind,
                "source_ref": memory.source_ref,
                "captured_at": now,
            }
        self.db.execute(
            """
            INSERT INTO memories (
                id, type, scope_type, scope_id, session_id, content, summary, subject,
                source_kind, source_ref, status, confidence, activation_score, access_count,
                created_at, updated_at, last_accessed_at, expires_at, archived_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                type=excluded.type,
                scope_type=excluded.scope_type,
                scope_id=excluded.scope_id,
                session_id=excluded.session_id,
                content=excluded.content,
                summary=excluded.summary,
                subject=excluded.subject,
                source_kind=excluded.source_kind,
                source_ref=excluded.source_ref,
                status=excluded.status,
                confidence=excluded.confidence,
                activation_score=excluded.activation_score,
                updated_at=excluded.updated_at,
                expires_at=excluded.expires_at,
                archived_at=excluded.archived_at,
                metadata_json=excluded.metadata_json
            """,
            (
                memory_id,
                memory.type,
                memory.scope_type,
                memory.scope_id,
                memory.session_id,
                memory.content,
                memory.summary,
                memory.subject,
                memory.source_kind,
                memory.source_ref,
                memory.status,
                memory.confidence,
                memory.activation_score,
                memory.access_count,
                _dt_to_iso(memory.created_at) or now,
                _dt_to_iso(memory.updated_at) or now,
                _dt_to_iso(memory.last_accessed_at),
                _dt_to_iso(memory.expires_at),
                _dt_to_iso(memory.archived_at),
                json.dumps(metadata, ensure_ascii=True),
            ),
        )
        return memory_id

    def get_by_id(self, memory_id: str) -> Memory | None:
        row = self.db.fetch_one("SELECT * FROM memories WHERE id = ?", (memory_id,))
        if row is None:
            return None
        return self._map_row_to_memory(row)

    def search(
        self,
        query: str,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        canonical = run_scoped_search(
            self.db,
            query,
            scope_type=scope_type,
            scope_id=scope_id,
            limit=limit,
            include_global=False,
        )
        return [
            SearchResult(
                id=result.id,
                type=result.type,
                content=result.content,
                summary=result.summary,
                subject=result.subject,
                score=result.score,
                reasons=result.reasons,
                source_kind=result.source_kind,
                source_ref=result.source_ref,
                scope_type=result.scope_type,
                scope_id=result.scope_id,
                conflict_status=result.conflict_status,
            )
            for result in canonical
        ]

    def get_evidence(self, memory_id: str) -> list[dict[str, Any]]:
        if not hasattr(self.db, "get_linked_evidence_for_memory"):
            row = self.db.fetch_one("SELECT metadata_json FROM memories WHERE id = ?", (memory_id,))
            if row is None:
                return []
            metadata = json.loads(row["metadata_json"] or "{}")
            evidence = metadata.get("evidence") if isinstance(metadata, dict) else None
            event_id = evidence.get("event_id") if isinstance(evidence, dict) else None
            if not event_id or not self._table_exists("evidence_events"):
                return []
            event_row = self.db.fetch_one("SELECT * FROM evidence_events WHERE id = ?", (event_id,))
            if event_row is None:
                return []
            event = dict(event_row)
            event["metadata"] = json.loads(event.pop("metadata_json") or "{}")
            return [event]
        events = self.db.get_linked_evidence_for_memory(memory_id)
        return [
            {
                "id": event.id,
                "memory_id": event.memory_id,
                "source_kind": event.source_kind,
                "source_ref": event.source_ref,
                "raw_content": event.raw_content,
                "metadata": event.metadata,
            }
            for event in events
        ]

    def _table_exists(self, table_name: str) -> bool:
        row = self.db.fetch_one(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return row is not None

    def delete(self, memory_id: str) -> bool:
        self.db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return True

    def expire_working_memory(self, session_id: str) -> int:
        now = now_iso()
        rows = self.db.fetch_all(
            """
            SELECT id, expires_at
            FROM memories
            WHERE type = 'working'
              AND session_id = ?
              AND status = 'active'
            """,
            (session_id,),
        )
        for row in rows:
            transition_memory(
                self.db,
                row["id"],
                status="expired",
                event="expired_on_session_end",
                expires_at=row["expires_at"] or now,
                details={"session_id": session_id},
            )
        return len(rows)

    def demote_working_memory(self, session_id: str, *, archive_threshold: float = 1.2) -> int:
        now = now_iso()
        rows = self.db.fetch_all(
            """
            SELECT id, archived_at
            FROM memories
            WHERE type = 'working'
              AND session_id = ?
              AND status = 'active'
              AND activation_score >= ?
            """,
            (session_id, archive_threshold),
        )
        for row in rows:
            transition_memory(
                self.db,
                row["id"],
                status="archived",
                event="demoted_from_working_memory",
                archived_at=row["archived_at"] or now,
                details={"session_id": session_id, "archive_threshold": archive_threshold},
            )
        return len(rows)

    def conclude_session(self, session_id: str, *, archive_threshold: float = 1.2) -> dict[str, int]:
        demoted = self.demote_working_memory(session_id, archive_threshold=archive_threshold)
        expired = self.expire_working_memory(session_id)
        return {"demoted": demoted, "expired": expired}

    def _map_row_to_memory(self, row: Any) -> Memory:
        payload = dict(row)
        return Memory(
            id=payload["id"],
            type=payload["type"],
            scope_type=payload["scope_type"],
            scope_id=payload["scope_id"],
            session_id=payload["session_id"],
            content=payload["content"],
            summary=payload["summary"],
            subject=payload["subject"],
            source_kind=payload["source_kind"],
            source_ref=payload["source_ref"],
            status=payload["status"],
            confidence=payload["confidence"],
            activation_score=payload["activation_score"],
            access_count=payload["access_count"],
            metadata=json.loads(payload["metadata_json"] or "{}"),
        )
