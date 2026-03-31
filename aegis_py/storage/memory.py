from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .models import Memory, RETRIEVABLE_MEMORY_STATUS_SQL
from ..hygiene.transitions import now_iso, transition_memory


class MemoryRepository:
    """Memory-row and retention/query helpers behind StorageManager."""

    def __init__(self, storage: Any):
        self.storage = storage

    def put_memory(self, memory: Memory) -> bool:
        conn = self.storage._get_connection()
        existing = conn.execute(
            "SELECT id FROM memories WHERE content = ? AND scope_id = ? AND scope_type = ? LIMIT 1",
            (memory.content, memory.scope_id, memory.scope_type),
        ).fetchone()
        if existing:
            return False

        data = memory.model_dump(by_alias=True)
        evidence_link = self.storage._ensure_memory_evidence(memory)
        normalized_metadata = self.storage._ensure_admission_state(
            metadata=evidence_link["metadata"],
            status=memory.status,
        )
        normalized_metadata = self.storage._ensure_memory_state(
            metadata=normalized_metadata,
            status=memory.status,
        )
        memory.metadata = normalized_metadata
        data["metadata_json"] = json.dumps(normalized_metadata)
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        if data["last_accessed_at"]:
            data["last_accessed_at"] = data["last_accessed_at"].isoformat()
        if data["expires_at"]:
            data["expires_at"] = data["expires_at"].isoformat()
        if data["archived_at"]:
            data["archived_at"] = data["archived_at"].isoformat()
        existing_columns = self.storage._table_columns("memories")
        filtered = {key: value for key, value in data.items() if key in existing_columns}
        keys = ", ".join(filtered.keys())
        placeholders = ", ".join(["?" for _ in filtered])

        conn.execute(
            f"INSERT OR REPLACE INTO memories ({keys}) VALUES ({placeholders})",
            tuple(filtered.values()),
        )
        self.index_memory_vector(memory.id, commit=False)
        self.storage.bump_scope_revision(memory.scope_type, memory.scope_id, commit=False)
        conn.commit()
        return True

    def get_memory_state(self, memory_id: str) -> dict[str, Any] | None:
        row = self.storage.fetch_one(
            "SELECT id, status, metadata_json FROM memories WHERE id = ?",
            (memory_id,),
        )
        if row is None:
            return None
        metadata = self.storage._coerce_metadata(row["metadata_json"])
        admission_state = self.storage._ensure_admission_state(
            metadata=metadata,
            status=row["status"],
        )["admission_state"]
        memory_state = self.storage._ensure_memory_state(
            metadata=metadata,
            status=row["status"],
        )["memory_state"]
        return {
            "memory_id": row["id"],
            "status": row["status"],
            "admission_state": admission_state,
            "memory_state": memory_state,
        }

    def summarize_memory_states(
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
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        rows = self.storage.fetch_all(
            f"SELECT id, status, metadata_json FROM memories {where_sql}",
            tuple(params),
        )
        counts: dict[str, int] = {}
        for row in rows:
            metadata = self.storage._coerce_metadata(row["metadata_json"])
            memory_state = self.storage._ensure_memory_state(
                metadata=metadata,
                status=row["status"],
            )["memory_state"]
            counts[memory_state] = counts.get(memory_state, 0) + 1
        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "memory_records": len(rows),
            "state_counts": counts,
        }

    def get_memory(self, memory_id: str) -> Memory | None:
        row = self.storage.fetch_one("SELECT * FROM memories WHERE id = ?", (memory_id,))
        if row:
            return self.storage._row_to_memory(row)
        return None

    def index_memory_vector(self, memory_id: str, *, commit: bool = True) -> None:
        row = self.storage.fetch_one(
            """
            SELECT id, scope_type, scope_id, content, summary, subject
            FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )
        if row is None:
            return
        text = " ".join(part for part in (row["content"], row["summary"], row["subject"]) if part)
        embedding = self.storage._embed_text(text)
        conn = self.storage._get_connection()
        conn.execute(
            """
            INSERT INTO memory_vectors (
                memory_id, scope_type, scope_id, token_count, embedding_json, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
                scope_type=excluded.scope_type,
                scope_id=excluded.scope_id,
                token_count=excluded.token_count,
                embedding_json=excluded.embedding_json,
                updated_at=excluded.updated_at
            """,
            (
                memory_id,
                row["scope_type"],
                row["scope_id"],
                len(embedding),
                json.dumps(embedding, ensure_ascii=True),
                now_iso(),
            ),
        )
        if commit:
            conn.commit()

    def search_memory_vectors(
        self,
        *,
        query: str,
        scope_type: str,
        scope_id: str,
        include_global: bool = False,
        limit: int = 10,
        min_similarity: float = 0.12,
    ) -> list[dict[str, Any]]:
        query_embedding = self.storage._embed_text(query)
        if not query_embedding:
            return []
        where = (
            "((v.scope_type = ? AND v.scope_id = ?) OR v.scope_type = 'global')"
            if include_global
            else "(v.scope_type = ? AND v.scope_id = ?)"
        )
        rows = self.storage.fetch_all(
            f"""
            SELECT v.memory_id, v.embedding_json, m.*
            FROM memory_vectors v
            JOIN memories m ON m.id = v.memory_id
            WHERE {where}
              AND m.status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
            ORDER BY m.updated_at DESC
            LIMIT ?
            """,
            (scope_type, scope_id, max(limit * 6, 25)),
        )
        ranked: list[dict[str, Any]] = []
        for row in rows:
            embedding = self.storage._coerce_metadata(row["embedding_json"])
            similarity = self.storage._cosine_similarity(query_embedding, embedding)
            if similarity < min_similarity:
                continue
            payload = dict(row)
            payload["vector_similarity"] = round(similarity, 6)
            ranked.append(payload)
        ranked.sort(
            key=lambda item: (
                item["vector_similarity"],
                float(item["activation_score"] or 0.0),
                item["updated_at"],
            ),
            reverse=True,
        )
        return ranked[:limit]

    def search_fts(
        self,
        query: str,
        scope_type: str,
        scope_id: str,
        limit: int = 10,
        include_global: bool = True,
    ) -> list[tuple[Memory, float]]:
        scope_sql = "(m.scope_type = ? AND m.scope_id = ?)"
        if include_global:
            scope_sql = f"({scope_sql} OR m.scope_type = 'global')"

        chars_to_strip = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        fts_query = query.translate(str.maketrans("", "", chars_to_strip))

        if not fts_query:
            sql = f"""
                SELECT *, 0.0 as rank FROM memories m
                WHERE {scope_sql} AND status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
                ORDER BY activation_score DESC
                LIMIT ?
            """
            params = (scope_type, scope_id, limit)
        else:
            sql = f"""
                SELECT m.*, fts.rank
                FROM memories_fts(?) fts
                JOIN memories m ON m.rowid = fts.rowid
                WHERE {scope_sql}
                  AND m.status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
                ORDER BY fts.rank
                LIMIT ?
            """
            params = (fts_query, scope_type, scope_id, limit)

        results: list[tuple[Memory, float]] = []
        conn = self.storage._get_connection()
        cursor = conn.execute(sql, params)
        for row in cursor:
            data = dict(row)
            rank = data.pop("rank")
            results.append((self.storage._row_to_memory(data), rank))
        return results

    def reinforce_memory(self, memory_id: str, increment: float = 1.0, max_score: float = 10.0) -> None:
        now = datetime.now(timezone.utc).isoformat()
        conn = self.storage._get_connection()
        row = conn.execute(
            "SELECT activation_score, access_count, metadata_json FROM memories WHERE id = ?",
            (memory_id,),
        ).fetchone()
        if row is None:
            return
        current_score = float(row["activation_score"] or 0.0)
        access_count = int(row["access_count"] or 0)
        metadata = self.storage._coerce_metadata(row["metadata_json"])
        bounded_increment = min(increment, max(0.2, 0.6 / (1 + (access_count * 0.5))))
        next_score = min(max_score, current_score + bounded_increment)
        metadata["retention_stage"] = "active"
        metadata["retention_recovery_mode"] = "bounded_reinforcement"
        conn.execute(
            """
            UPDATE memories
            SET activation_score = ?,
                access_count = access_count + 1,
                last_accessed_at = ?,
                updated_at = ?,
                metadata_json = ?
            WHERE id = ?
            """,
            (next_score, now, now, json.dumps(metadata, ensure_ascii=True), memory_id),
        )
        conn.commit()

    def apply_decay(
        self,
        half_life_days: float = 7.0,
        type_half_lives: dict[str, float] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        conn = self.storage._get_connection()
        mems = conn.execute(
            """
            SELECT id, type, activation_score, confidence, access_count, metadata_json,
                   last_accessed_at, updated_at
            FROM memories
            WHERE status = 'active'
            """
        ).fetchall()
        updates = []
        for row in mems:
            last_ref = row["last_accessed_at"] or row["updated_at"]
            last_time = datetime.fromisoformat(last_ref)
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)

            delta_days = (now - last_time).total_seconds() / 86400.0
            if delta_days <= 0.1:
                continue
            effective_half_life = (
                type_half_lives.get(row["type"], half_life_days)
                if type_half_lives is not None
                else half_life_days
            )
            metadata = self.storage._coerce_metadata(row["metadata_json"])
            explicit_salience = float(metadata.get("salience", 0.0) or 0.0)
            inferred_salience = max(0.0, float(row["confidence"] or 1.0) - 1.0)
            salience = max(explicit_salience, inferred_salience)
            reinforcement_count = int(row["access_count"] or 0)
            effective_half_life = effective_half_life * (
                1.0 + (0.35 * min(salience, 1.0)) + min(1.2, reinforcement_count * 0.08)
            )
            new_score = row["activation_score"] * (0.5 ** (delta_days / effective_half_life))
            updates.append((new_score, now.isoformat(), row["id"]))

        if updates:
            conn.executemany("UPDATE memories SET activation_score = ?, updated_at = ? WHERE id = ?", updates)
            conn.commit()

    def apply_retention_policy(
        self,
        *,
        thresholds: dict[str, tuple[float, float, float]],
    ) -> dict[str, int]:
        now = now_iso()
        rows = self.storage.fetch_all(
            """
            SELECT id, type, status, activation_score, archived_at, metadata_json
            FROM memories
            WHERE status IN ('active', 'archived')
            """
        )
        summary = {
            "cold": 0,
            "archive_candidate": 0,
            "deprecated_candidate": 0,
            "archived_now": 0,
        }
        for row in rows:
            thresholds_for_type = thresholds.get(row["type"], thresholds["episodic"])
            cold_min, archive_min, deprecated_min = thresholds_for_type
            score = float(row["activation_score"] or 0.0)
            if score > cold_min:
                stage = "active"
            elif score > archive_min:
                stage = "cold"
            elif score > deprecated_min:
                stage = "archive_candidate"
            else:
                stage = "deprecated_candidate"
            self.storage._set_retention_stage(
                row["id"],
                stage=stage,
                current_status=row["status"],
                archived_at=row["archived_at"],
                at=now,
                score=score,
            )
            if stage in summary:
                summary[stage] += 1
            if row["status"] == "active" and stage in {"archive_candidate", "deprecated_candidate"}:
                summary["archived_now"] += 1
        return summary

    def archive_expired(self, session_id: str | None = None) -> None:
        now = now_iso()
        seen: set[str] = set()

        expired_rows = self.storage.fetch_all(
            """
            SELECT id, archived_at
            FROM memories
            WHERE status = 'active'
              AND expires_at IS NOT NULL
              AND expires_at < ?
            """,
            (now,),
        )
        for row in expired_rows:
            transition_memory(
                self.storage,
                row["id"],
                status="archived",
                event="archived_by_expiry",
                archived_at=row["archived_at"] or now,
                details={"reason": "hard_expiry"},
            )
            seen.add(row["id"])

        if session_id:
            session_rows = self.storage.fetch_all(
                """
                SELECT id, archived_at
                FROM memories
                WHERE status = 'active'
                  AND type = 'working'
                  AND session_id = ?
                """,
                (session_id,),
            )
            for row in session_rows:
                if row["id"] in seen:
                    continue
                transition_memory(
                    self.storage,
                    row["id"],
                    status="archived",
                    event="archived_on_session_end",
                    archived_at=row["archived_at"] or now,
                    details={"session_id": session_id},
                )

    def find_same_subject_peers(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        subject: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.storage.fetch_all(
                f"""
                SELECT id, scope_type, scope_id, subject
                FROM memories
                WHERE id != ?
                  AND status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
                  AND scope_type = ?
                  AND scope_id = ?
                  AND subject = ?
                ORDER BY activation_score DESC, updated_at DESC
                LIMIT ?
                """,
                (memory_id, scope_type, scope_id, subject, limit),
            )
        ]

    def find_same_subject_typed_peers(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        subject: str,
        peer_type: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.storage.fetch_all(
                f"""
                SELECT id, type, scope_type, scope_id, subject
                FROM memories
                WHERE id != ?
                  AND status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
                  AND scope_type = ?
                  AND scope_id = ?
                  AND subject = ?
                  AND type = ?
                ORDER BY activation_score DESC, updated_at DESC
                LIMIT ?
                """,
                (memory_id, scope_type, scope_id, subject, peer_type, limit),
            )
        ]

    def list_entity_peers(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        entities: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not entities:
            return []
        rows = self.storage.fetch_all(
            f"""
            SELECT *
            FROM memories
            WHERE id != ?
              AND status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})
              AND scope_type = ?
              AND scope_id = ?
            ORDER BY activation_score DESC, updated_at DESC
            """,
            (memory_id, scope_type, scope_id),
        )
        matches: list[dict[str, Any]] = []
        entity_set = set(entities)
        for row in rows:
            payload = dict(row)
            metadata_raw = payload.get("metadata_json")
            metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw or {}
            peer_entities = metadata.get("entities") or []
            overlap = sorted(entity_set.intersection(peer_entities))
            if not overlap:
                continue
            payload["entity_overlap"] = overlap
            matches.append(payload)
            if len(matches) >= limit:
                break
        return matches
