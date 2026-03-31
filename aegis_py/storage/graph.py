from __future__ import annotations

import json
from typing import Any

from ..hygiene.transitions import now_iso
from .models import RETRIEVABLE_MEMORY_STATUS_SQL
from ..v7.graph_taxonomy import canonical_edge_type


class GraphRepository:
    """Explicit memory-link and neighbor expansion helpers."""

    def __init__(self, storage: Any):
        self.storage = storage

    def upsert_memory_link(
        self,
        *,
        source_id: str,
        target_id: str,
        link_type: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
        bump_revision: bool = True,
    ) -> dict[str, Any]:
        if source_id == target_id:
            raise ValueError("Self-links are not allowed.")
        source = self.storage.fetch_one(
            "SELECT id, scope_type, scope_id FROM memories WHERE id = ?",
            (source_id,),
        )
        target = self.storage.fetch_one(
            "SELECT id, scope_type, scope_id FROM memories WHERE id = ?",
            (target_id,),
        )
        if source is None or target is None:
            missing = source_id if source is None else target_id
            raise ValueError(f"Memory not found for relation endpoint: {missing}")
        if source["scope_type"] != target["scope_type"] or source["scope_id"] != target["scope_id"]:
            raise ValueError("Cross-scope memory links are not allowed.")

        link_id = f"{source_id}:{link_type}:{target_id}"
        final_metadata = dict(metadata or {})
        final_metadata.setdefault("canonical_edge_type", canonical_edge_type(link_type))
        created_at = now_iso()
        conn = self.storage._get_connection()
        conn.execute(
            """
            INSERT INTO memory_links (
                id, source_id, target_id, link_type, weight, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, target_id, link_type) DO UPDATE SET
                weight=excluded.weight,
                metadata_json=excluded.metadata_json
            """,
            (
                link_id,
                source_id,
                target_id,
                link_type,
                weight,
                json.dumps(final_metadata, ensure_ascii=False),
                created_at,
            ),
        )
        if bump_revision:
            self.storage.bump_scope_revision(source["scope_type"], source["scope_id"], commit=False)
        if commit:
            conn.commit()
        return {
            "id": link_id,
            "source_id": source_id,
            "target_id": target_id,
            "link_type": link_type,
            "weight": weight,
            "metadata": final_metadata,
            "scope_type": source["scope_type"],
            "scope_id": source["scope_id"],
            "created_at": created_at,
        }

    def list_memory_neighbors(
        self,
        *,
        memory_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        rows = self.storage.fetch_all(
            f"""
            SELECT
                l.id AS link_id,
                l.link_type,
                l.weight,
                l.metadata_json,
                l.source_id,
                l.target_id,
                m.id AS memory_id,
                m.type,
                m.scope_type,
                m.scope_id,
                m.subject,
                m.content,
                m.summary,
                m.source_kind,
                m.source_ref,
                m.status
            FROM memory_links l
            JOIN memories m
              ON m.id = CASE
                WHEN l.source_id = ? THEN l.target_id
                ELSE l.source_id
              END
            WHERE (l.source_id = ? OR l.target_id = ?)
              AND m.status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
            ORDER BY l.weight DESC, m.updated_at DESC
            LIMIT ?
            """,
            (memory_id, memory_id, memory_id, limit),
        )
        neighbors: list[dict[str, Any]] = []
        for row in rows:
            metadata = row["metadata_json"]
            neighbors.append(
                {
                    "link": {
                        "id": row["link_id"],
                        "link_type": row["link_type"],
                        "weight": row["weight"],
                        "source_id": row["source_id"],
                        "target_id": row["target_id"],
                        "metadata": json.loads(metadata) if isinstance(metadata, str) else metadata or {},
                    },
                    "memory": {
                        "id": row["memory_id"],
                        "type": row["type"],
                        "scope_type": row["scope_type"],
                        "scope_id": row["scope_id"],
                        "subject": row["subject"],
                        "content": row["content"],
                        "summary": row["summary"],
                        "source_kind": row["source_kind"],
                        "source_ref": row["source_ref"],
                        "status": row["status"],
                    },
                }
            )
        return neighbors

    def list_link_expansions(
        self,
        *,
        seed_ids: list[str],
        scope_type: str,
        scope_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not seed_ids:
            return []
        placeholders = ",".join("?" for _ in seed_ids)
        rows = self.storage.fetch_all(
            f"""
            SELECT
                l.link_type,
                l.weight,
                l.source_id,
                l.target_id,
                m.*
            FROM memory_links l
            JOIN memories m
              ON m.id = CASE
                WHEN l.source_id IN ({placeholders}) THEN l.target_id
                ELSE l.source_id
              END
            WHERE (l.source_id IN ({placeholders}) OR l.target_id IN ({placeholders}))
              AND m.scope_type = ?
              AND m.scope_id = ?
              AND m.status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
            ORDER BY l.weight DESC, m.activation_score DESC, m.updated_at DESC
            LIMIT ?
            """,
            (*seed_ids, *seed_ids, *seed_ids, scope_type, scope_id, limit),
        )
        return [dict(row) for row in rows]

    def count_links_by_type(self, *, link_type: str) -> int:
        row = self.storage.fetch_one(
            "SELECT COUNT(*) AS count FROM memory_links WHERE link_type = ?",
            (link_type,),
        )
        return row["count"] if row else 0
