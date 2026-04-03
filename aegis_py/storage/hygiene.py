from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any


class StorageHygieneRepository:
    """Storage-growth inspection and bounded compaction helpers."""

    FOOTPRINT_TABLES = [
        "memories",
        "memory_links",
        "conflicts",
        "memory_vectors",
        "evidence_events",
        "evidence_artifacts",
        "governance_events",
        "memory_state_transitions",
        "background_intelligence_runs",
        "replication_audit_log",
        "autonomous_audit_log",
    ]

    def __init__(self, storage: Any):
        self.storage = storage

    def storage_footprint(self) -> dict[str, Any]:
        conn = self.storage._get_connection()
        page_count = int(conn.execute("PRAGMA page_count").fetchone()[0])
        page_size = int(conn.execute("PRAGMA page_size").fetchone()[0])
        freelist_count = int(conn.execute("PRAGMA freelist_count").fetchone()[0])
        rows: dict[str, int] = {}
        for table in self.FOOTPRINT_TABLES:
            if not self.storage._table_exists(table):
                continue
            row = self.storage.fetch_one(f"SELECT COUNT(*) AS count FROM {table}")
            rows[table] = int(row["count"] if row else 0)
        return {
            "db_path": self.storage.db_path,
            "page_count": page_count,
            "page_size": page_size,
            "freelist_count": freelist_count,
            "allocated_bytes": page_count * page_size,
            "free_bytes": freelist_count * page_size,
            "rows": rows,
        }

    def compact_storage(
        self,
        *,
        archived_memory_days: int,
        superseded_memory_days: int,
        evidence_days: int,
        governance_days: int,
        replication_days: int,
        background_days: int,
        vacuum: bool,
    ) -> dict[str, Any]:
        before = self.storage_footprint()
        now = datetime.now(timezone.utc)
        conn = self.storage._get_connection()

        archived_cutoff = (now - timedelta(days=archived_memory_days)).isoformat()
        superseded_cutoff = (now - timedelta(days=superseded_memory_days)).isoformat()
        evidence_cutoff = (now - timedelta(days=evidence_days)).isoformat()
        governance_cutoff = (now - timedelta(days=governance_days)).isoformat()
        replication_cutoff = (now - timedelta(days=replication_days)).isoformat()
        background_cutoff = (now - timedelta(days=background_days)).isoformat()

        deleted = {
            "archived_memories": 0,
            "superseded_memories": 0,
            "mammoth_preserved_archives": 0,
            "evidence_artifacts": 0,
            "evidence_events": 0,
            "governance_events": 0,
            "replication_audit_log": 0,
            "autonomous_audit_log": 0,
            "background_runs": 0,
        }

        archived_candidates = conn.execute(
            """
            SELECT id, confidence, access_count, metadata_json
            FROM memories
            WHERE status = 'archived'
              AND COALESCE(archived_at, updated_at, created_at) < ?
            """,
            (archived_cutoff,),
        ).fetchall()
        deletable_archived_ids: list[str] = []
        for row in archived_candidates:
            if self._should_preserve_mammoth_archive(row):
                deleted["mammoth_preserved_archives"] += 1
                continue
            deletable_archived_ids.append(row["id"])

        if deletable_archived_ids:
            placeholders = ", ".join("?" for _ in deletable_archived_ids)
            cursor = conn.execute(
                f"DELETE FROM memories WHERE id IN ({placeholders})",
                tuple(deletable_archived_ids),
            )
            deleted["archived_memories"] = cursor.rowcount if cursor.rowcount != -1 else 0
        else:
            deleted["archived_memories"] = 0

        cursor = conn.execute(
            """
            DELETE FROM memories
            WHERE status IN ('superseded', 'expired')
              AND COALESCE(archived_at, updated_at, created_at) < ?
            """,
            (superseded_cutoff,),
        )
        deleted["superseded_memories"] = cursor.rowcount if cursor.rowcount != -1 else 0

        cursor = conn.execute(
            """
            DELETE FROM evidence_artifacts
            WHERE created_at < ?
              AND (
                memory_id IS NULL
                OR memory_id NOT IN (SELECT id FROM memories WHERE status = 'active')
              )
            """,
            (evidence_cutoff,),
        )
        deleted["evidence_artifacts"] = cursor.rowcount if cursor.rowcount != -1 else 0

        cursor = conn.execute(
            """
            DELETE FROM evidence_events
            WHERE created_at < ?
              AND (
                memory_id IS NULL
                OR memory_id NOT IN (SELECT id FROM memories WHERE status = 'active')
              )
            """,
            (evidence_cutoff,),
        )
        deleted["evidence_events"] = cursor.rowcount if cursor.rowcount != -1 else 0

        cursor = conn.execute(
            """
            DELETE FROM governance_events
            WHERE created_at < ?
              AND (
                memory_id IS NULL
                OR memory_id NOT IN (SELECT id FROM memories WHERE status = 'active')
              )
            """,
            (governance_cutoff,),
        )
        deleted["governance_events"] = cursor.rowcount if cursor.rowcount != -1 else 0

        cursor = conn.execute(
            """
            DELETE FROM replication_audit_log
            WHERE applied_at < ?
            """,
            (replication_cutoff,),
        )
        deleted["replication_audit_log"] = cursor.rowcount if cursor.rowcount != -1 else 0

        cursor = conn.execute(
            """
            DELETE FROM autonomous_audit_log
            WHERE applied_at < ?
              AND status IN ('rolled_back', 'failed')
            """,
            (governance_cutoff,),
        )
        deleted["autonomous_audit_log"] = cursor.rowcount if cursor.rowcount != -1 else 0

        if self.storage._table_exists("background_intelligence_runs"):
            cursor = conn.execute(
                """
                DELETE FROM background_intelligence_runs
                WHERE created_at < ?
                  AND status = 'discarded'
                """,
                (background_cutoff,),
            )
            deleted["background_runs"] = cursor.rowcount if cursor.rowcount != -1 else 0

        conn.commit()
        total_deleted = sum(deleted.values())
        if vacuum and total_deleted > 0:
            conn.execute("VACUUM")
            conn.commit()
        after = self.storage_footprint()
        return {
            "before": before,
            "after": after,
            "deleted": deleted,
            "vacuumed": vacuum and total_deleted > 0,
        }

    def _should_preserve_mammoth_archive(self, row: Any) -> bool:
        metadata_raw = row["metadata_json"]
        if isinstance(metadata_raw, str):
            metadata = json.loads(metadata_raw or "{}")
        else:
            metadata = metadata_raw or {}

        if metadata.get("mammoth_archive_anchor") or metadata.get("retention_pinned"):
            return True

        score_profile = metadata.get("score_profile", {}) if isinstance(metadata, dict) else {}
        source_reliability = float(score_profile.get("source_reliability", 0.0) or 0.0)
        confidence = float(row["confidence"] or 0.0)
        access_count = int(row["access_count"] or 0)

        return confidence >= 0.9 and source_reliability >= 0.88 and access_count >= 1
