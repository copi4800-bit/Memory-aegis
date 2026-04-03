from __future__ import annotations

import logging
import json
from typing import Any, Dict, List
from ..storage.manager import StorageManager
from ..hygiene.transitions import transition_memory, now_iso

logger = logging.getLogger(__name__)


class LibrarianBeast:
    """
    The Librarian Beast is responsible for semantic consolidation and 
    knowledge-base cleanup. It manages the 'merge' lifecycle for 
    equivalent memories.
    """

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def consolidate_equivalents(self, scope_type: str, scope_id: str, subject: str) -> int:
        """
        Scans for equivalent memories within a subject and merges them.
        Uses subject-based clustering as a fast heuristic.
        """
        if not subject or subject == "general.untagged":
            return 0

        # Fetch active memories for this subject
        memories = self.storage.fetch_all(
            """
            SELECT * FROM memories 
            WHERE status = 'active' 
              AND scope_type = ? 
              AND scope_id = ? 
              AND subject = ?
            ORDER BY activation_score DESC, updated_at DESC
            """,
            (scope_type, scope_id, subject)
        )
        
        if len(memories) < 2:
            return 0

        # Simple semantic clustering (initially just subject-based, 
        # but can be extended with weaver links)
        # Skip if any memory is an explicit correction (let Consolidator handle it)
        active_memories = []
        for m in memories:
            m_dict = dict(m)
            meta = json.loads(m_dict["metadata_json"]) if isinstance(m_dict["metadata_json"], str) else (m_dict["metadata_json"] or {})
            if meta.get("is_correction"):
                return 0
            active_memories.append(m_dict)

        master = active_memories[0]
        duplicates = active_memories[1:]
        
        merged_count = 0
        for dup in duplicates:
            self._merge_memories(master, dup)
            merged_count += 1
            
        return merged_count

    def _merge_memories(self, master: Dict[str, Any], duplicate: Dict[str, Any]) -> None:
        """
        Merges a duplicate memory into a master memory.
        """
        logger.info(f"Librarian merging duplicate {duplicate['id']} into master {master['id']}")
        
        # 1. Transition duplicate to superseded
        transition_memory(
            self.storage,
            duplicate["id"],
            status="superseded",
            event="merged_by_librarian",
            details={"master_id": master["id"]}
        )
        
        # 2. Update master metadata and scores
        master_metadata = json.loads(master["metadata_json"]) if isinstance(master["metadata_json"], str) else (master["metadata_json"] or {})
        dup_metadata = json.loads(duplicate["metadata_json"]) if isinstance(duplicate["metadata_json"], str) else (duplicate["metadata_json"] or {})
        
        # Track history
        merged_from = master_metadata.get("merged_from", [])
        if duplicate["id"] not in merged_from:
            merged_from.append(duplicate["id"])
        master_metadata["merged_from"] = merged_from
        
        # Combine provenance if possible
        if duplicate.get("source_ref") and duplicate["source_ref"] != master.get("source_ref"):
            refs = master_metadata.get("other_sources", [])
            if duplicate["source_ref"] not in refs:
                refs.append(duplicate["source_ref"])
            master_metadata["other_sources"] = refs

        # 3. Apply updates to database
        new_activation = min(10.0, float(master["activation_score"]) + (float(duplicate["activation_score"]) * 0.2))
        new_access_count = int(master["access_count"]) + int(duplicate["access_count"])
        
        self.storage.execute(
            """
            UPDATE memories 
            SET activation_score = ?, 
                access_count = ?, 
                metadata_json = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                new_activation, 
                new_access_count, 
                json.dumps(master_metadata, ensure_ascii=False),
                now_iso(),
                master["id"]
            )
        )
        
        # Update local master dict to reflect changes for the next loop iteration
        master["activation_score"] = new_activation
        master["access_count"] = new_access_count
        master["metadata_json"] = master_metadata

    def build_index_locality_report(self, scope_type: str, scope_id: str) -> Dict[str, Any]:
        rows = self.storage.fetch_all(
            """
            SELECT subject, COUNT(*) AS count
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND subject IS NOT NULL
            GROUP BY subject
            ORDER BY count DESC, subject ASC
            """,
            (scope_type, scope_id),
        )
        subject_count = len(rows)
        densest_cluster = int(rows[0]["count"]) if rows else 0
        avg_cluster = 0.0 if not rows else sum(int(row["count"]) for row in rows) / len(rows)
        titanoboa_index_locality = min(
            0.99,
            0.3 + (min(densest_cluster, 6) * 0.08) + (min(avg_cluster, 4.0) * 0.06),
        )
        return {
            "subject_count": subject_count,
            "densest_cluster": densest_cluster,
            "average_cluster_size": round(avg_cluster, 3),
            "titanoboa_index_locality": round(titanoboa_index_locality, 3),
        }

    def build_subject_locality_report(self, scope_type: str, scope_id: str, subject: str | None) -> Dict[str, Any]:
        if not subject:
            return {
                "subject": subject,
                "cluster_size": 0,
                "titanoboa_subject_locality": 0.0,
            }
        row = self.storage.fetch_one(
            """
            SELECT COUNT(*) AS count
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND subject = ?
            """,
            (scope_type, scope_id, subject),
        )
        cluster_size = int(row["count"]) if row else 0
        locality = min(0.99, 0.22 + (min(cluster_size, 6) * 0.11))
        return {
            "subject": subject,
            "cluster_size": cluster_size,
            "titanoboa_subject_locality": round(locality, 3),
        }
