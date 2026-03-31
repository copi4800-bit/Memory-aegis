from __future__ import annotations

from typing import Any

from .observability import ObservedOperation


class AegisSyncSurface:
    """Sync-policy and sync-envelope facade."""

    def __init__(self, app: Any):
        self.app = app

    def set_scope_policy(
        self,
        scope_type: str,
        scope_id: str,
        *,
        sync_policy: str,
        sync_state: str = "local",
        last_sync_at: str | None = None,
    ) -> dict[str, Any]:
        return self.app.operations.set_scope_policy(
            scope_type,
            scope_id,
            sync_policy=sync_policy,
            sync_state=sync_state,
            last_sync_at=last_sync_at,
        )

    def get_scope_policy(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        sync_policy: str | None = None,
    ) -> dict[str, Any]:
        return self.app.operations.get_scope_policy(
            scope_type=scope_type,
            scope_id=scope_id,
            sync_policy=sync_policy,
        )

    def export_sync_envelope(
        self,
        *,
        scope_type: str,
        scope_id: str,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        observation = ObservedOperation(
            self.app.observability,
            tool="sync_export",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        try:
            payload = self.app.operations.export_sync_envelope(
                scope_type=scope_type,
                scope_id=scope_id,
                workspace_dir=workspace_dir,
            )
            observation.finish(
                result="success",
                details={"records": payload.get("records", 0), "path": payload.get("path")},
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__)
            raise

    def preview_sync_envelope(self, envelope_path: str) -> dict[str, Any]:
        observation = ObservedOperation(self.app.observability, tool="sync_preview")
        try:
            payload = self.app.operations.preview_sync_envelope(envelope_path)
            observation.finish(
                result="success",
                scope_type=payload["scope"]["scope_type"],
                scope_id=payload["scope"]["scope_id"],
                details={"incoming_records": payload.get("incoming_records", 0)},
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__, details={"path": envelope_path})
            raise

    def import_sync_envelope(self, envelope_path: str) -> dict[str, Any]:
        observation = ObservedOperation(self.app.observability, tool="sync_import")
        try:
            payload = self.app.operations.import_sync_envelope(envelope_path)
            observation.finish(
                result="success",
                scope_type=payload["scope"]["scope_type"],
                scope_id=payload["scope"]["scope_id"],
                details={
                    "incoming_records": payload.get("records", 0),
                    "inserted": payload.get("inserted_records", 0),
                    "replaced": payload.get("replaced_records", 0),
                },
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__, details={"path": envelope_path})
            raise
