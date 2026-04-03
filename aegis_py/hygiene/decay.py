import json
from datetime import datetime, timezone
from ..storage.manager import StorageManager
from .transitions import transition_memory, now_iso

class DecayBeast:
    """Manages memory decay and crystallization."""
    
    HALF_LIVES = {
        "semantic": 60.0,
        "procedural": 90.0,
        "episodic": 7.0,
        "working": 2.0,
    }

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def apply_typed_decay(self):
        """Applies type-specific half-life decay to active memories."""
        self.storage.apply_decay(type_half_lives=self.HALF_LIVES)

    def crystallize_hot_memories(self):
        """Finds active memories accessed frequently and crystallizes them."""
        # memories accessed >= 5 times become crystallized
        rows = self.storage.fetch_all(
            "SELECT id, status, archived_at FROM memories WHERE status = 'active' AND access_count >= 5"
        )
        now = now_iso()
        for row in rows:
            # Transition memory to 'crystallized'
            transition_memory(
                self.storage,
                row["id"],
                status="crystallized",
                event="crystallized_by_decay_beast",
                archived_at=row["archived_at"],
                details={"reason": "high_access_count"},
                at=now
            )

    def pin_memory(self, memory_id: str):
        """Pins a memory to prevent decay (crystallizes it)."""
        now = now_iso()
        row = self.storage.fetch_one("SELECT status, archived_at FROM memories WHERE id = ?", (memory_id,))
        if row and row["status"] != "crystallized":
            transition_memory(
                self.storage,
                memory_id,
                status="crystallized",
                event="pinned_by_user",
                archived_at=row["archived_at"],
                details={"reason": "user_pinned"},
                at=now
            )

    def unpin_memory(self, memory_id: str):
        """Unpins a memory (sets back to active)."""
        now = now_iso()
        row = self.storage.fetch_one("SELECT status, archived_at FROM memories WHERE id = ?", (memory_id,))
        if row and row["status"] == "crystallized":
            transition_memory(
                self.storage,
                memory_id,
                status="active",
                event="unpinned_by_user",
                archived_at=row["archived_at"],
                details={"reason": "user_unpinned"},
                at=now
            )

    def evaluate_retirement_candidates(self) -> list[dict[str, object]]:
        rows = self.storage.fetch_all(
            """
            SELECT id, type, status, confidence, activation_score, access_count, created_at, updated_at, last_accessed_at
            FROM memories
            WHERE status = 'active'
            """
        )
        now = datetime.now(timezone.utc)
        candidates: list[dict[str, object]] = []
        for row in rows:
            anchor = row["last_accessed_at"] or row["updated_at"] or row["created_at"]
            age_days = 0.0
            if anchor:
                try:
                    anchor_dt = datetime.fromisoformat(str(anchor))
                    if anchor_dt.tzinfo is None:
                        anchor_dt = anchor_dt.replace(tzinfo=timezone.utc)
                    age_days = max(0.0, (now - anchor_dt).total_seconds() / 86400.0)
                except ValueError:
                    age_days = 0.0
            half_life = float(self.HALF_LIVES.get(row["type"], 30.0))
            confidence = float(row["confidence"] or 0.0)
            activation = float(row["activation_score"] or 0.0)
            access_count = int(row["access_count"] or 0)
            smilodon_retirement_pressure = min(
                0.99,
                (min(age_days / max(half_life, 1.0), 2.0) * 0.42)
                + ((1.0 - min(confidence, 1.0)) * 0.18)
                + ((1.0 - min(activation, 1.5) / 1.5) * 0.16)
                + (0.12 if access_count == 0 else 0.0),
            )
            candidates.append(
                {
                    "memory_id": row["id"],
                    "memory_type": row["type"],
                    "age_days": round(age_days, 3),
                    "half_life_days": half_life,
                    "smilodon_retirement_pressure": round(smilodon_retirement_pressure, 3),
                }
            )
        candidates.sort(key=lambda item: float(item["smilodon_retirement_pressure"]), reverse=True)
        return candidates

    def retire_pressure_candidates(self, threshold: float = 0.82) -> int:
        retired = 0
        timestamp = now_iso()
        for candidate in self.evaluate_retirement_candidates():
            pressure = float(candidate["smilodon_retirement_pressure"])
            if pressure < threshold:
                continue
            row = self.storage.fetch_one(
                "SELECT status, archived_at FROM memories WHERE id = ?",
                (candidate["memory_id"],),
            )
            if row is None or row["status"] != "active":
                continue
            transition_memory(
                self.storage,
                str(candidate["memory_id"]),
                status="archived",
                archived_at=timestamp,
                event="smilodon_retired_low_viability",
                details={"smilodon_retirement_pressure": pressure},
                at=timestamp,
            )
            retired += 1
        return retired
