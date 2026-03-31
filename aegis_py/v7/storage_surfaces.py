from __future__ import annotations

from typing import Any

from ..storage.manager import StorageManager
from ..storage.models import Memory


class SpecializedStorageSurfaces:
    """Thin v7 storage facades over the existing SQLite runtime."""

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def persist_fact_memory(self, memory: Memory) -> bool:
        return self.storage.put_memory(memory)

    def get_fact_memory(self, memory_id: str) -> Memory | None:
        return self.storage.get_memory(memory_id)

    def list_vector_candidates(
        self,
        *,
        scope_type: str,
        scope_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        rows = self.storage.fetch_all(
            """
            SELECT id, type, content, summary, subject, status, metadata_json
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND status = 'active'
            ORDER BY activation_score DESC, updated_at DESC
            LIMIT ?
            """,
            (scope_type, scope_id, limit),
        )
        candidates: list[dict[str, Any]] = []
        for row in rows:
            metadata = self.storage._coerce_metadata(row["metadata_json"])
            candidates.append(
                {
                    "memory_id": row["id"],
                    "type": row["type"],
                    "content": row["content"],
                    "summary": row["summary"],
                    "subject": row["subject"],
                    "memory_state": metadata.get("memory_state", "validated"),
                    "evidence": metadata.get("evidence", {}),
                }
            )
        return candidates

    def search_vector_store(
        self,
        *,
        query: str,
        scope_type: str,
        scope_id: str,
        include_global: bool = False,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self.storage.search_memory_vectors(
            query=query,
            scope_type=scope_type,
            scope_id=scope_id,
            include_global=include_global,
            limit=limit,
        )

    def list_graph_neighbors(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self.storage.list_link_expansions(
            seed_ids=[memory_id],
            scope_type=scope_type,
            scope_id=scope_id,
            limit=limit,
        )
