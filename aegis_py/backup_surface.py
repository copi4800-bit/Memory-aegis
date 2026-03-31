from __future__ import annotations

from typing import Any

from .observability import ObservedOperation


class AegisBackupSurface:
    """Backup and restore facade that preserves operations-service behavior."""

    def __init__(self, app: Any):
        self.app = app

    def create_backup(
        self,
        mode: str = "snapshot",
        *,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        observation = ObservedOperation(self.app.observability, tool="backup_create")
        try:
            payload = self.app.operations.create_backup(mode=mode, workspace_dir=workspace_dir)
            observation.finish(result="success", details={"mode": mode, "path": payload.get("path")})
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__, details={"mode": mode})
            raise

    def list_backups(self, workspace_dir: str | None = None) -> dict[str, Any]:
        return self.app.operations.list_backups(workspace_dir=workspace_dir)

    def preview_restore(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        observation = ObservedOperation(
            self.app.observability,
            tool="restore_preview",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        try:
            payload = self.app.operations.preview_restore(
                snapshot_path,
                scope_type=scope_type,
                scope_id=scope_id,
            )
            observation.finish(
                result="success",
                details={"mode": payload.get("mode"), "records": payload.get("preview", {}).get("records")},
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__)
            raise

    def restore_backup(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        observation = ObservedOperation(
            self.app.observability,
            tool="restore_backup",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        try:
            payload = self.app.operations.restore_backup(
                snapshot_path,
                scope_type=scope_type,
                scope_id=scope_id,
            )
            observation.finish(
                result="success",
                details={"mode": payload.get("mode"), "restored_records": payload.get("restored_records")},
            )
            return payload
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__)
            raise

    def backup_create_summary(self, payload: dict[str, Any]) -> str:
        return "\n".join(
            [
                "## Aegis Backup",
                "",
                f"Created a {payload['mode']} backup successfully.",
                f"Backup path: {payload['path']}",
                f"File size: {payload['bytes']} bytes",
            ]
        )

    def backup_list_summary(self, payload: dict[str, Any]) -> str:
        backups = payload.get("backups", [])
        lines = ["## Aegis Backups", ""]
        if not backups:
            lines.append("No backups were found yet.")
            return "\n".join(lines)

        lines.append(f"Found {len(backups)} backup(s).")
        for entry in backups[:5]:
            lines.append(f"- {entry['mode']} backup at {entry['artifact_path']}")
        return "\n".join(lines)

    def restore_preview_summary(self, payload: dict[str, Any]) -> str:
        preview = payload["preview"]
        scope_filter = payload.get("scope_filter")
        scope_label = (
            f"{scope_filter['scope_type']}:{scope_filter['scope_id']}"
            if scope_filter is not None
            else "all local memory"
        )
        current_scope_records = sum(payload.get("current_scope_counts", {}).values())
        return "\n".join(
            [
                "## Aegis Restore Preview",
                "",
                f"This is a dry run for {scope_label}.",
                f"Backup type: {payload['mode']}",
                f"Records in backup scope: {preview['records']}",
                f"Current local records in target scope: {current_scope_records}",
                f"Records that would be considered for restore: {preview['records']}",
            ]
        )

    def restore_result_summary(self, payload: dict[str, Any]) -> str:
        scope_filter = payload.get("scope_filter")
        scope_label = (
            f"{scope_filter['scope_type']}:{scope_filter['scope_id']}"
            if scope_filter is not None
            else "the full local memory database"
        )
        restored_records = payload.get("restored_records")
        lines = [
            "## Aegis Restore",
            "",
            f"Restore completed for {scope_label}.",
            f"Backup type: {payload['mode']}",
        ]
        if restored_records is not None:
            lines.append(f"Records restored: {restored_records}")
        return "\n".join(lines)
