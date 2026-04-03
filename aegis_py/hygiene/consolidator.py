from __future__ import annotations

import json
import logging
from typing import Any, Dict
from ..storage.manager import StorageManager
from ..hygiene.transitions import transition_memory, now_iso

logger = logging.getLogger(__name__)


class ConsolidatorBeast:
    """
    The Consolidator Beast resolves contradictions and manages fact corrections.
    It implements a temporal preference policy (newer info wins).
    """

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def resolve_corrections(self) -> int:
        """
        Scans for open conflicts and resolves those identified as correction candidates.
        """
        # Fetch open conflicts that are marked as correction candidates
        conflicts = self.storage.fetch_all(
            """
            SELECT c.id, c.reason, 
                   m_a.id AS id_a, m_a.created_at AS created_a, m_a.metadata_json AS meta_a,
                   m_b.id AS id_b, m_b.created_at AS created_b, m_b.metadata_json AS meta_b
            FROM conflicts c
            JOIN memories m_a ON c.memory_a_id = m_a.id
            JOIN memories m_b ON c.memory_b_id = m_b.id
            WHERE c.status = 'open' 
              AND (c.reason = 'Correction candidate' OR c.reason = 'Potential logical contradiction')
            """
        )

        resolved_count = 0
        for row in conflicts:
            # We determine the winner based on recency (Temporal Preference)
            # SQLite stores dates as ISO strings; string comparison works for chronologically.
            if row["created_a"] >= row["created_b"]:
                winner_id, loser_id = row["id_a"], row["id_b"]
                winner_meta_raw = row["meta_a"]
            else:
                winner_id, loser_id = row["id_b"], row["id_a"]
                winner_meta_raw = row["meta_b"]

            # In slice 037, same-subject contradictions and explicit corrections both
            # use a bounded recency preference policy.
            if row["reason"] in {"Correction candidate", "Potential logical contradiction"}:
                self._apply_correction(row["id"], winner_id, loser_id, winner_meta_raw)
                resolved_count += 1
            
        return resolved_count

    def _apply_correction(self, conflict_id: str, winner_id: str, loser_id: str, winner_meta_raw: Any) -> None:
        """
        Performs the state transition for a correction resolution.
        """
        logger.info(f"Consolidator applying correction: {winner_id} supersedes {loser_id}")

        # 1. Supersede the loser
        transition_memory(
            self.storage,
            loser_id,
            status="superseded",
            event="corrected_by_newer_info",
            details={"winner_id": winner_id, "conflict_id": conflict_id}
        )
        
        # 2. Update winner metadata with correction link
        winner_meta = json.loads(winner_meta_raw) if isinstance(winner_meta_raw, str) else (winner_meta_raw or {})
        corrected_from = winner_meta.get("corrected_from", [])
        if loser_id not in corrected_from:
            corrected_from.append(loser_id)
        winner_meta["corrected_from"] = corrected_from
        glyptodon_consolidation_shell = min(
            0.99,
            0.4 + (min(len(corrected_from), 4) * 0.12),
        )
        winner_meta["glyptodon_consolidation_shell"] = round(glyptodon_consolidation_shell, 3)
        
        self.storage.execute(
            "UPDATE memories SET metadata_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(winner_meta, ensure_ascii=False), now_iso(), winner_id)
        )

        # 3. Resolve the conflict record
        self.storage.execute(
            """
            UPDATE conflicts 
            SET status = 'resolved', 
                resolution = 'auto_correction_by_recency', 
                resolved_at = ? 
            WHERE id = ?
            """,
            (now_iso(), conflict_id)
        )
