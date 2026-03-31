from __future__ import annotations

from typing import Any

from .observability import ObservedOperation


class AegisGovernedBackgroundSurface:
    """Governed background planning and mutation facade."""

    def __init__(self, app: Any):
        self.app = app

    def plan_background_intelligence(
        self,
        *,
        scope_type: str,
        scope_id: str,
    ) -> dict[str, Any]:
        observation = ObservedOperation(
            self.app.observability,
            tool="background_plan",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        try:
            proposals = self.app.background_intelligence.plan_scope(scope_type=scope_type, scope_id=scope_id)
            payload = {
                "backend": "python",
                "scope_type": scope_type,
                "scope_id": scope_id,
                "proposal_count": len(proposals),
                "proposals": proposals,
            }
            observation.finish(result="success" if proposals else "empty", details={"proposal_count": len(proposals)})
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__)
            raise

    def apply_background_intelligence_run(self, run_id: str, *, max_mutations: int = 5) -> dict[str, Any]:
        observation = ObservedOperation(self.app.observability, tool="background_apply")
        try:
            payload = self.app.background_intelligence.apply_run(run_id, max_mutations=max_mutations)
            observation.finish(
                result="success" if payload.get("applied") else "no_op",
                details={"run_id": run_id, "audit_count": len(payload.get("audit_ids", []))},
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__, details={"run_id": run_id})
            raise

    def shadow_background_intelligence_run(self, run_id: str) -> dict[str, Any]:
        return self.app.background_intelligence.shadow_run(run_id)

    def rollback_background_intelligence_run(self, run_id: str) -> dict[str, Any]:
        observation = ObservedOperation(self.app.observability, tool="background_rollback")
        try:
            payload = self.app.background_intelligence.rollback_run(run_id)
            observation.finish(
                result="success" if payload.get("rolled_back") else "no_op",
                details={"run_id": run_id, "audit_count": len(payload.get("audit_ids", []))},
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__, details={"run_id": run_id})
            raise
