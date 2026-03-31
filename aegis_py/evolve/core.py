from __future__ import annotations

import json
from ..hygiene.transitions import transition_memory, coerce_metadata, now_iso


class EvolveEngine:
    """Handles bounded reinforcement, decay, and archival hygiene."""

    REINFORCE_DELTA = 0.1
    DECAY_RATE = 0.05
    THRESHOLD_ARCHIVE = 0.3
    THRESHOLD_EXPIRE = 0.1

    def __init__(self, db_manager):
        self.db = db_manager

    def reinforce(self, memory_id: str) -> bool:
        self.db.execute(
            """
            UPDATE memories
            SET activation_score = MIN(2.0, activation_score + ?),
                access_count = access_count + 1,
                last_accessed_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (self.REINFORCE_DELTA, now_iso(), now_iso(), memory_id),
        )
        return True

    def apply_decay(self, days_passed: float) -> bool:
        decay_amount = days_passed * self.DECAY_RATE
        self.db.execute(
            """
            UPDATE memories
            SET activation_score = MAX(0.0, activation_score - ?),
                updated_at = ?
            WHERE status = 'active'
            """,
            (decay_amount, now_iso()),
        )
        return True

    def run_hygiene(self) -> bool:
        now = now_iso()
        archive_rows = self.db.fetch_all(
            """
            SELECT id, archived_at, metadata_json
            FROM memories
            WHERE activation_score < ? AND status = 'active'
            """,
            (self.THRESHOLD_ARCHIVE,),
        )
        for row in archive_rows:
            transition_memory(
                self.db,
                row["id"],
                status="archived",
                event="archived_by_hygiene",
                archived_at=row["archived_at"] or now,
                details={"threshold": self.THRESHOLD_ARCHIVE},
                at=now,
            )

        expire_rows = self.db.fetch_all(
            """
            SELECT id, expires_at, metadata_json
            FROM memories
            WHERE activation_score < ? AND status = 'archived'
            """,
            (self.THRESHOLD_EXPIRE,),
        )
        for row in expire_rows:
            transition_memory(
                self.db,
                row["id"],
                status="expired",
                event="expired_by_hygiene",
                expires_at=row["expires_at"] or now,
                details={"threshold": self.THRESHOLD_EXPIRE},
                at=now,
            )
        return True
