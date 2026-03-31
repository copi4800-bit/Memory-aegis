from __future__ import annotations

from typing import Any

from .retrieval.v8_dynamics import bundle_energy_snapshot
from .storage.manager import DEFAULT_COMPACTION_POLICY


class AegisOperatorSurface:
    """Operator-oriented storage, governance, and evidence facade."""

    def __init__(self, app: Any):
        self.app = app

    def inspect_governance(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        events = self.app.storage.list_governance_events(
            scope_type=scope_type,
            scope_id=scope_id,
            memory_id=memory_id,
            limit=limit,
        )
        transitions = self.app.storage.list_memory_state_transitions(memory_id) if memory_id else []
        return {
            "backend": "python",
            "events": events,
            "transitions": transitions,
        }

    def evidence_artifacts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return {
            "backend": "python",
            "artifacts": self.app.storage.list_evidence_artifacts(
                scope_type=scope_type,
                scope_id=scope_id,
                memory_id=memory_id,
                limit=limit,
            ),
        }

    def storage_footprint(self) -> dict[str, Any]:
        return self.app.storage.storage_footprint()

    def storage_compaction_policy(self) -> dict[str, int]:
        return dict(DEFAULT_COMPACTION_POLICY)

    def compact_storage(
        self,
        *,
        archived_memory_days: int = 30,
        superseded_memory_days: int = 14,
        evidence_days: int = 30,
        governance_days: int = 30,
        replication_days: int = 14,
        background_days: int = 14,
        vacuum: bool = True,
    ) -> dict[str, Any]:
        return self.app.storage.compact_storage(
            archived_memory_days=archived_memory_days,
            superseded_memory_days=superseded_memory_days,
            evidence_days=evidence_days,
            governance_days=governance_days,
            replication_days=replication_days,
            background_days=background_days,
            vacuum=vacuum,
        )

    def get_memory_evidence(self, memory_id: str) -> list[dict[str, Any]]:
        events = self.app.storage.get_linked_evidence_for_memory(memory_id)
        return [
            {
                "id": event.id,
                "scope_type": event.scope_type,
                "scope_id": event.scope_id,
                "session_id": event.session_id,
                "memory_id": event.memory_id,
                "source_kind": event.source_kind,
                "source_ref": event.source_ref,
                "raw_content": event.raw_content,
                "metadata": event.metadata,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]

    def memory_neighbors(self, memory_id: str, *, limit: int = 10) -> dict[str, Any]:
        memory = self.app.storage.get_memory(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found: {memory_id}")
        return {
            "backend": "python",
            "memory_id": memory_id,
            "scope_type": memory.scope_type,
            "scope_id": memory.scope_id,
            "neighbors": self.app.storage.list_memory_neighbors(memory_id=memory_id, limit=limit),
        }

    def v8_field_snapshot(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        memory_ids = self.app._list_field_snapshot_memory_ids(scope_type=scope_type, scope_id=scope_id)
        signals_list = [self.app.compute_v8_core_signals(memory_id) for memory_id in memory_ids]
        counts = {
            "draft": 0,
            "validated": 0,
            "consolidated": 0,
            "hypothesized": 0,
            "invalidated": 0,
            "archived": 0,
        }
        for signals in signals_list:
            state = str(signals.get("admission_state") or "validated")
            counts[state] = counts.get(state, 0) + 1

        def _avg(key: str) -> float:
            if not signals_list:
                return 0.0
            return round(
                sum(float(item.get(key, 0.0) or 0.0) for item in signals_list) / len(signals_list),
                6,
            )

        return {
            "backend": "python",
            "scope": {
                "scope_type": scope_type,
                "scope_id": scope_id,
            },
            "memory_ids": memory_ids,
            "counts": counts,
            "averages": {
                "belief_score": _avg("belief_score"),
                "trust_score": _avg("trust_score"),
                "readiness_score": _avg("readiness_score"),
                "conflict_signal": _avg("conflict_signal"),
                "decay_signal": _avg("decay_signal"),
            },
            "energy": bundle_energy_snapshot(signals_list),
        }

    def v8_core_signals(self, memory_id: str) -> dict[str, Any]:
        signals = self.app.compute_v8_core_signals(memory_id)
        return {
            "backend": "python",
            "memory_id": memory_id,
            "observables": self._v8_observables(signals),
            "signals": signals,
        }

    def v8_transition_gate(self, memory_id: str) -> dict[str, Any]:
        operator = self.app.evaluate_v8_transition_operator(memory_id)
        return {
            "backend": "python",
            "memory_id": memory_id,
            "observables": self._v8_observables(operator["signals"]),
            "transition_operator": operator,
            "inputs": operator["inputs"],
            "decision": operator["decision"],
            "thresholds": operator["thresholds"],
            "transition_gate": operator["transition_gate"],
            "signals": operator["signals"],
        }

    def _v8_observables(self, signals: dict[str, Any]) -> dict[str, Any]:
        trust_score = float(signals.get("trust_score", 0.0) or 0.0)
        readiness_score = float(signals.get("readiness_score", 0.0) or 0.0)
        if trust_score >= 0.8:
            trust_level = "high"
        elif trust_score >= 0.6:
            trust_level = "medium"
        else:
            trust_level = "low"
        if readiness_score >= 0.8:
            readiness_level = "ready"
        elif readiness_score >= 0.5:
            readiness_level = "warming"
        else:
            readiness_level = "cold"
        return {
            "trust": {
                "score": round(trust_score, 6),
                "level": trust_level,
            },
            "readiness": {
                "score": round(readiness_score, 6),
                "level": readiness_level,
            },
            "state": signals.get("admission_state"),
        }

    def apply_v8_outcome_feedback(
        self,
        memory_id: str,
        *,
        success_score: float,
        relevance_score: float | None = None,
        override_score: float = 0.0,
        actor: str = "v8_feedback",
    ) -> dict[str, Any]:
        return self.app.apply_v8_outcome_feedback(
            memory_id,
            success_score=success_score,
            relevance_score=relevance_score,
            override_score=override_score,
            actor=actor,
        )

    def apply_v8_retrieval_feedback(
        self,
        *,
        query: str,
        scope_id: str,
        scope_type: str = "session",
        success_score: float,
        selected_memory_ids: list[str] | None = None,
        override_memory_ids: list[str] | None = None,
        limit: int = 5,
        include_global: bool = True,
        actor: str = "v8_bundle_feedback",
    ) -> dict[str, Any]:
        return self.app.apply_v8_retrieval_feedback(
            query=query,
            scope_id=scope_id,
            scope_type=scope_type,
            success_score=success_score,
            selected_memory_ids=selected_memory_ids,
            override_memory_ids=override_memory_ids,
            limit=limit,
            include_global=include_global,
            actor=actor,
        )

    def v8_bundle_snapshot(
        self,
        *,
        query: str,
        scope_id: str,
        scope_type: str = "session",
        limit: int = 5,
        include_global: bool = True,
    ) -> dict[str, Any]:
        return self.app.v8_bundle_snapshot(
            query=query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
        )

    def apply_v8_transition_gate(self, memory_id: str, *, actor: str = "v8_core") -> dict[str, Any]:
        return self.app.apply_v8_transition_gate(memory_id, actor=actor)
