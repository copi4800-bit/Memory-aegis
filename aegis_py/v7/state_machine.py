from __future__ import annotations

from typing import Any

from ..storage.manager import StorageManager


ALLOWED_STATE_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"validated", "hypothesized", "invalidated"},
    "validated": {"consolidated", "hypothesized", "invalidated", "archived"},
    "hypothesized": {"validated", "invalidated", "archived"},
    "consolidated": {"archived"},
    "invalidated": set(),
    "archived": set(),
}


class MemoryStateMachine:
    """Applies explicit v7 state transitions with audit logging."""

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def current_state(self, memory_id: str) -> str | None:
        state = self.storage.get_memory_state(memory_id)
        if state is None:
            return None
        return state.get("memory_state")

    def can_transition(self, from_state: str | None, to_state: str) -> bool:
        if from_state is None:
            return True
        return to_state == from_state or to_state in ALLOWED_STATE_TRANSITIONS.get(from_state, set())

    def record_initial_state(
        self,
        *,
        memory_id: str,
        to_state: str,
        reason: str,
        evidence_event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.storage.record_memory_state_transition(
            memory_id=memory_id,
            from_state="draft",
            to_state=to_state,
            reason=reason,
            actor="policy_gate",
            policy_name="v7-default-policy-gate",
            evidence_event_id=evidence_event_id,
            details=details,
        )

    def transition(
        self,
        *,
        memory_id: str,
        to_state: str,
        reason: str,
        actor: str = "system",
        evidence_event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> bool:
        current = self.current_state(memory_id)
        if not self.can_transition(current, to_state):
            return False

        row = self.storage.fetch_one("SELECT metadata_json, status FROM memories WHERE id = ?", (memory_id,))
        if row is None:
            return False
        metadata = self.storage._coerce_metadata(row["metadata_json"])
        metadata["memory_state"] = to_state
        metadata["admission_state"] = to_state
        
        # Map v7 state to storage visibility status
        if to_state == "invalidated":
            new_status = "superseded"
        elif to_state == "archived":
            new_status = "archived"
        else:
            new_status = "active"
            
        self.storage.execute(
            "UPDATE memories SET metadata_json = ?, status = ?, updated_at = ? WHERE id = ?",
            (self._dump_metadata(metadata), new_status, self._now(), memory_id),
        )
        self.storage.record_memory_state_transition(
            memory_id=memory_id,
            from_state=current,
            to_state=to_state,
            reason=reason,
            actor=actor,
            evidence_event_id=evidence_event_id,
            details=details,
        )
        return True

    def _dump_metadata(self, metadata: dict[str, Any]) -> str:
        import json

        return json.dumps(metadata, ensure_ascii=True)

    def _now(self) -> str:
        from ..hygiene.transitions import now_iso

        return now_iso()
