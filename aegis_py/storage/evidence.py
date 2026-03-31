from __future__ import annotations

import json
import uuid
from typing import Any

from .models import EvidenceEvent


class EvidenceRepository:
    """Evidence-event and evidence-artifact storage helpers."""

    def __init__(self, storage: Any):
        self.storage = storage

    def put_evidence_event(self, event: EvidenceEvent) -> EvidenceEvent:
        data = event.model_dump(by_alias=True)
        data["created_at"] = data["created_at"].isoformat()
        data["metadata_json"] = json.dumps(data["metadata_json"], ensure_ascii=True)
        existing_columns = self.storage._table_columns("evidence_events")
        filtered = {
            key: value for key, value in data.items()
            if key in existing_columns
        }
        keys = ", ".join(filtered.keys())
        placeholders = ", ".join(["?" for _ in filtered])
        self.storage.execute(
            f"INSERT INTO evidence_events ({keys}) VALUES ({placeholders})",
            tuple(filtered.values()),
        )
        return event

    def create_evidence_event(
        self,
        *,
        scope_type: str,
        scope_id: str,
        raw_content: str,
        source_kind: str,
        session_id: str | None = None,
        source_ref: str | None = None,
        memory_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceEvent:
        event = EvidenceEvent(
            id=f"evt_{uuid.uuid4().hex[:16]}",
            scope_type=scope_type,
            scope_id=scope_id,
            session_id=session_id,
            memory_id=memory_id,
            source_kind=source_kind,
            source_ref=source_ref,
            raw_content=raw_content,
            metadata=metadata or {},
        )
        return self.put_evidence_event(event)

    def get_evidence_event(self, event_id: str) -> EvidenceEvent | None:
        row = self.storage.fetch_one("SELECT * FROM evidence_events WHERE id = ?", (event_id,))
        if row is None:
            return None
        return self.storage._row_to_evidence_event(row)

    def list_evidence_events_for_memory(self, memory_id: str) -> list[EvidenceEvent]:
        rows = self.storage.fetch_all(
            """
            SELECT * FROM evidence_events
            WHERE memory_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (memory_id,),
        )
        return [self.storage._row_to_evidence_event(row) for row in rows]

    def get_linked_evidence_for_memory(self, memory_id: str) -> list[EvidenceEvent]:
        row = self.storage.fetch_one(
            "SELECT metadata_json FROM memories WHERE id = ?",
            (memory_id,),
        )
        if row is None:
            return []
        metadata = self.storage._coerce_metadata(row["metadata_json"])
        evidence = metadata.get("evidence")
        event_id = evidence.get("event_id") if isinstance(evidence, dict) else None
        if event_id:
            linked = self.get_evidence_event(event_id)
            if linked is not None:
                return [linked]
        return self.list_evidence_events_for_memory(memory_id)

    def summarize_evidence_coverage(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        where_clauses: list[str] = []
        params: list[Any] = []
        if scope_type is not None:
            where_clauses.append("scope_type = ?")
            params.append(scope_type)
        if scope_id is not None:
            where_clauses.append("scope_id = ?")
            params.append(scope_id)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        rows = self.storage.fetch_all(
            f"""
            SELECT id, metadata_json
            FROM memories
            {where_sql}
            """,
            tuple(params),
        )
        total = len(rows)
        with_linkage = 0
        missing_linkage = 0
        linked_event_ids: set[str] = set()
        for row in rows:
            metadata = self.storage._coerce_metadata(row["metadata_json"])
            evidence = metadata.get("evidence")
            event_id = evidence.get("event_id") if isinstance(evidence, dict) else None
            if event_id:
                with_linkage += 1
                linked_event_ids.add(str(event_id))
            else:
                missing_linkage += 1

        evidence_where = []
        evidence_params: list[Any] = []
        if scope_type is not None:
            evidence_where.append("scope_type = ?")
            evidence_params.append(scope_type)
        if scope_id is not None:
            evidence_where.append("scope_id = ?")
            evidence_params.append(scope_id)
        evidence_where_sql = ""
        if evidence_where:
            evidence_where_sql = "WHERE " + " AND ".join(evidence_where)
        event_row = self.storage.fetch_one(
            f"SELECT COUNT(*) AS count FROM evidence_events {evidence_where_sql}",
            tuple(evidence_params),
        )
        evidence_events = int(event_row["count"] if event_row else 0)

        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "memory_records": total,
            "linked_memories": with_linkage,
            "missing_linkage": missing_linkage,
            "coverage_ratio": (with_linkage / total) if total else 1.0,
            "linked_event_count": len(linked_event_ids),
            "evidence_events": evidence_events,
        }

    def record_evidence_artifact(
        self,
        *,
        artifact_kind: str,
        scope_type: str,
        scope_id: str,
        payload: dict[str, Any],
        memory_id: str | None = None,
        evidence_event_id: str | None = None,
    ) -> str:
        artifact_id = f"art_{uuid.uuid4().hex[:16]}"
        self.storage.execute(
            """
            INSERT INTO evidence_artifacts (
                id, artifact_kind, scope_type, scope_id, memory_id, evidence_event_id, payload_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                artifact_kind,
                scope_type,
                scope_id,
                memory_id,
                evidence_event_id,
                json.dumps(payload, ensure_ascii=True),
                self.storage._now_iso(),
            ),
        )
        return artifact_id

    def list_evidence_artifacts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if scope_type is not None:
            where.append("scope_type = ?")
            params.append(scope_type)
        if scope_id is not None:
            where.append("scope_id = ?")
            params.append(scope_id)
        if memory_id is not None:
            where.append("memory_id = ?")
            params.append(memory_id)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        rows = self.storage.fetch_all(
            f"""
            SELECT id, artifact_kind, scope_type, scope_id, memory_id, evidence_event_id, payload_json, created_at
            FROM evidence_artifacts
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (*params, limit),
        )
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["payload"] = self.storage._coerce_metadata(payload.pop("payload_json", "{}"))
            results.append(payload)
        return results
