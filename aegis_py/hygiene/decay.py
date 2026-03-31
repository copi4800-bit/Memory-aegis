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
