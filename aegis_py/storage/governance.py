from __future__ import annotations

import json
import uuid
from typing import Any

from ..hygiene.transitions import now_iso


class GovernanceRepository:
    """Governance events, state transitions, and background-run storage helpers."""

    def __init__(self, storage: Any):
        self.storage = storage

    def record_memory_state_transition(
        self,
        *,
        memory_id: str,
        from_state: str | None,
        to_state: str,
        reason: str,
        actor: str = "system",
        policy_name: str | None = None,
        evidence_event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        transition_id = f"mst_{uuid.uuid4().hex[:16]}"
        self.storage.execute(
            """
            INSERT INTO memory_state_transitions (
                id, memory_id, from_state, to_state, reason, actor, policy_name,
                evidence_event_id, details_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transition_id,
                memory_id,
                from_state,
                to_state,
                reason,
                actor,
                policy_name,
                evidence_event_id,
                json.dumps(details or {}, ensure_ascii=True),
                now_iso(),
            ),
        )
        return transition_id

    def list_memory_state_transitions(self, memory_id: str) -> list[dict[str, Any]]:
        rows = self.storage.fetch_all(
            """
            SELECT id, memory_id, from_state, to_state, reason, actor, policy_name,
                   evidence_event_id, details_json, created_at
            FROM memory_state_transitions
            WHERE memory_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (memory_id,),
        )
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["details"] = self.storage._coerce_metadata(payload.pop("details_json", "{}"))
            results.append(payload)
        return results

    def record_governance_event(
        self,
        *,
        event_kind: str,
        scope_type: str,
        scope_id: str,
        memory_id: str | None = None,
        evidence_event_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> str:
        event_id = f"gov_{uuid.uuid4().hex[:16]}"
        self.storage.execute(
            """
            INSERT INTO governance_events (
                id, event_kind, scope_type, scope_id, memory_id, evidence_event_id,
                payload_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_kind,
                scope_type,
                scope_id,
                memory_id,
                evidence_event_id,
                json.dumps(payload or {}, ensure_ascii=True),
                now_iso(),
            ),
        )
        return event_id

    def list_governance_events(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if scope_type is not None:
            where.append("scope_type = ?")
            params.append(scope_type)
        if scope_id is not None:
            where.append("scope_id = ?")
            params.append(scope_id)
        if memory_id is not None:
            where.append("memory_id = ?")
            params.append(memory_id)
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        rows = self.storage.fetch_all(
            f"""
            SELECT id, event_kind, scope_type, scope_id, memory_id, evidence_event_id,
                   payload_json, created_at
            FROM governance_events
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (*params, limit),
        )
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["payload"] = self.storage._coerce_metadata(payload.pop("payload_json", "{}"))
            results.append(payload)
        return results

    def record_background_intelligence_run(
        self,
        *,
        scope_type: str,
        scope_id: str,
        worker_kind: str,
        proposal: dict[str, Any],
        mode: str = "working_copy",
        status: str = "planned",
    ) -> str:
        run_id = f"bg_{uuid.uuid4().hex[:16]}"
        self.storage.execute(
            """
            INSERT INTO background_intelligence_runs (
                id, scope_type, scope_id, worker_kind, mode, status, proposal_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                scope_type,
                scope_id,
                worker_kind,
                mode,
                status,
                json.dumps(proposal, ensure_ascii=True),
                now_iso(),
            ),
        )
        return run_id

    def get_background_intelligence_run(self, run_id: str) -> dict[str, Any] | None:
        row = self.storage.fetch_one(
            """
            SELECT id, scope_type, scope_id, worker_kind, mode, status, proposal_json, created_at
            FROM background_intelligence_runs
            WHERE id = ?
            """,
            (run_id,),
        )
        if row is None:
            return None
        payload = dict(row)
        payload["proposal"] = self.storage._coerce_metadata(payload.pop("proposal_json", "{}"))
        return payload

    def list_background_intelligence_runs(
        self,
        *,
        scope_type: str,
        scope_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        where = ["scope_type = ?", "scope_id = ?"]
        params: list[Any] = [scope_type, scope_id]
        if status is not None:
            where.append("status = ?")
            params.append(status)
        rows = self.storage.fetch_all(
            f"""
            SELECT id, scope_type, scope_id, worker_kind, mode, status, proposal_json, created_at
            FROM background_intelligence_runs
            WHERE {' AND '.join(where)}
            ORDER BY created_at DESC, id DESC
            """,
            tuple(params),
        )
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            payload["proposal"] = self.storage._coerce_metadata(payload.pop("proposal_json", "{}"))
            results.append(payload)
        return results

    def update_background_intelligence_run(
        self,
        run_id: str,
        *,
        status: str,
        proposal: dict[str, Any] | None = None,
    ) -> None:
        current = self.get_background_intelligence_run(run_id)
        if current is None:
            return
        self.storage.execute(
            "UPDATE background_intelligence_runs SET status = ?, proposal_json = ? WHERE id = ?",
            (status, json.dumps(proposal if proposal is not None else current["proposal"], ensure_ascii=True), run_id),
        )
