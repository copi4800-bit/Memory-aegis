from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any


class AegisOperationalService:
    """Behavior-preserving operational workflows delegated from AegisApp."""

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
        self.app.storage.set_scope_policy(
            scope_type,
            scope_id,
            sync_policy=sync_policy,
            sync_state=sync_state,
            last_sync_at=last_sync_at,
        )
        return self.get_scope_policy(scope_type=scope_type, scope_id=scope_id)

    def get_scope_policy(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        sync_policy: str | None = None,
    ) -> dict[str, Any]:
        if (scope_type is None) != (scope_id is None):
            raise ValueError("scope_type and scope_id must both be provided when inspecting a single scope.")

        if scope_type is not None and scope_id is not None:
            policy = self.app.storage.get_scope_policy(scope_type, scope_id)
            policy["backend"] = "python"
            return policy

        return {
            "backend": "python",
            "policies": self.app.storage.list_scope_policies(sync_policy=sync_policy),
            "default_policy": "local_only",
            "sync_required": False,
        }

    def create_backup(
        self,
        mode: str = "snapshot",
        *,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        backups_dir = Path(workspace_dir or Path(self.app.db_path).parent) / ".aegis_py" / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = self.app._timestamp_slug()

        if mode == "export":
            target = backups_dir / f"aegis-export-{timestamp}.json"
            target.write_text(self.app.export_memories("json"), encoding="utf-8")
            manifest = self.app._write_backup_manifest(target, "export")
            return {
                "mode": "export",
                "path": str(target),
                "bytes": target.stat().st_size,
                "manifest_path": str(manifest),
                "backend": "python",
            }

        if mode != "snapshot":
            raise ValueError(f"Unsupported backup mode: {mode}")

        target = backups_dir / f"aegis-snapshot-{timestamp}.db"
        source = self.app.storage._get_connection()
        target_conn = sqlite3.connect(target)
        try:
            source.backup(target_conn)
        finally:
            target_conn.close()
        manifest = self.app._write_backup_manifest(target, "snapshot")
        return {
            "mode": "snapshot",
            "path": str(target),
            "bytes": target.stat().st_size,
            "manifest_path": str(manifest),
            "backend": "python",
        }

    def list_backups(self, workspace_dir: str | None = None) -> dict[str, Any]:
        backups_dir = self.app._backups_dir(workspace_dir)
        entries: list[dict[str, Any]] = []
        if backups_dir.exists():
            for manifest_path in sorted(backups_dir.glob("*.manifest.json"), reverse=True):
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    artifact_path = Path(manifest["artifact_path"])
                    if not artifact_path.exists():
                        continue
                    entries.append(manifest)
                except (OSError, json.JSONDecodeError, KeyError):
                    continue
        return {"backend": "python", "backups": entries}

    def preview_restore(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        source = Path(snapshot_path).expanduser()
        if not source.exists():
            raise FileNotFoundError(f"Backup file not found: {snapshot_path}")

        scope_filter = self.app._normalize_scope_filter(scope_type=scope_type, scope_id=scope_id)
        manifest = self.app._load_manifest_for_backup(source)
        mode = manifest["mode"] if manifest else ("export" if source.suffix.lower() == ".json" else "snapshot")
        current_counts = self.app._memory_counts()
        current_scope_counts = self.app._memory_counts(scope_filter=scope_filter)

        if mode == "export":
            payload = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("Export backup payload must be a JSON array.")
            source_rows = self.app._filter_export_rows(payload, scope_filter=scope_filter)
            preview = self.app._build_preview_counts(
                source_rows=source_rows,
                source_scope_count=len({(row.get("scope_type"), row.get("scope_id")) for row in payload}),
                current_scope_counts=current_scope_counts,
                scope_filter=scope_filter,
            )
        else:
            with sqlite3.connect(source) as conn:
                conn.row_factory = sqlite3.Row
                source_rows = self.app._read_snapshot_memories(conn, scope_filter=scope_filter)
                scope_count_row = conn.execute(
                    "SELECT COUNT(DISTINCT scope_type || ':' || scope_id) FROM memories"
                ).fetchone()
                preview = self.app._build_preview_counts(
                    source_rows=source_rows,
                    source_scope_count=scope_count_row[0] if scope_count_row else 0,
                    current_scope_counts=current_scope_counts,
                    scope_filter=scope_filter,
                )

        return {
            "backend": "python",
            "dry_run": True,
            "mode": mode,
            "path": str(source),
            "manifest": manifest,
            "target_db_path": self.app.db_path,
            "scope_filter": scope_filter,
            "current_counts": current_counts,
            "current_scope_counts": current_scope_counts,
            "preview": preview,
        }

    def restore_backup(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        source = Path(snapshot_path).expanduser()
        if not source.exists():
            raise FileNotFoundError(f"Backup file not found: {snapshot_path}")
        scope_filter = self.app._normalize_scope_filter(scope_type=scope_type, scope_id=scope_id)
        manifest = self.app._load_manifest_for_backup(source)

        if scope_filter is not None:
            restored_rows = self.app._restore_scope_from_backup(source, scope_filter=scope_filter)
            return {
                "restored": True,
                "mode": "export" if source.suffix.lower() == ".json" else "snapshot",
                "path": str(source),
                "manifest": manifest,
                "scope_filter": scope_filter,
                "restored_records": restored_rows,
                "backend": "python",
            }

        self.app.close()
        target = Path(self.app.db_path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)

        if source.suffix.lower() == ".json":
            if target.exists():
                target.unlink()
            self.app._bind_runtime()
            rows = json.loads(source.read_text(encoding="utf-8"))
            for row in rows:
                self.app.put_memory(
                    row["content"],
                    type=row["type"],
                    scope_type=row["scope_type"],
                    scope_id=row["scope_id"],
                    session_id=row.get("session_id"),
                    source_kind=row.get("source_kind", "manual"),
                    source_ref=row.get("source_ref"),
                    subject=row.get("subject"),
                    summary=row.get("summary"),
                )
            return {
                "restored": True,
                "mode": "export",
                "path": str(source),
                "manifest": manifest,
                "backend": "python",
            }

        shutil.copy2(source, target)
        self.app._bind_runtime()
        return {
            "restored": True,
            "mode": "snapshot",
            "path": str(source),
            "manifest": manifest,
            "backend": "python",
        }

    def export_sync_envelope(
        self,
        *,
        scope_type: str,
        scope_id: str,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        policy = self.app.storage.get_scope_policy(scope_type, scope_id)
        if policy["sync_policy"] != "sync_eligible":
            raise ValueError("Only sync_eligible scopes can be exported as sync envelopes.")
        rows = self.app.storage.fetch_all(
            """
            SELECT *
            FROM memories
            WHERE scope_type = ? AND scope_id = ?
            ORDER BY created_at ASC
            """,
            (scope_type, scope_id),
        )
        records: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            if isinstance(payload.get("metadata_json"), str):
                payload["metadata_json"] = json.loads(payload["metadata_json"])
            records.append(payload)

        sync_dir = Path(workspace_dir or Path(self.app.db_path).parent) / ".aegis_py" / "sync"
        sync_dir.mkdir(parents=True, exist_ok=True)
        envelope_path = sync_dir / f"aegis-sync-{scope_type}-{scope_id}-{self.app._timestamp_slug()}.json"
        revision = self.app.storage.get_scope_revision(scope_type, scope_id)
        envelope = {
            "envelope_version": 1,
            "backend": "python",
            "scope": {"scope_type": scope_type, "scope_id": scope_id},
            "policy": policy,
            "scope_revision": revision,
            "exported_at": self.app._timestamp_slug(),
            "records": records,
        }
        envelope_path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "backend": "python",
            "path": str(envelope_path),
            "scope_type": scope_type,
            "scope_id": scope_id,
            "scope_revision": revision["revision"],
            "records": len(records),
        }

    def preview_sync_envelope(self, envelope_path: str) -> dict[str, Any]:
        source = Path(envelope_path).expanduser()
        if not source.exists():
            raise FileNotFoundError(f"Sync envelope not found: {envelope_path}")
        envelope = json.loads(source.read_text(encoding="utf-8"))
        scope = envelope["scope"]
        incoming_revision = envelope.get("scope_revision") or {"revision": 0, "updated_at": None}
        records = envelope.get("records", [])
        local_rows = self.app.storage.fetch_all(
            """
            SELECT id, updated_at
            FROM memories
            WHERE scope_type = ? AND scope_id = ?
            """,
            (scope["scope_type"], scope["scope_id"]),
        )
        local_index = {row["id"]: row["updated_at"] for row in local_rows}
        diff = self._build_sync_reconcile_diff(local_index=local_index, records=records)
        local_revision = self.app.storage.get_scope_revision(scope["scope_type"], scope["scope_id"])
        if int(local_revision["revision"]) != int(incoming_revision.get("revision", 0)):
            diff["revision_mismatch"] = 1
        return {
            "backend": "python",
            "dry_run": True,
            "path": str(source),
            "scope": scope,
            "local_scope_revision": local_revision,
            "incoming_scope_revision": incoming_revision,
            "incoming_records": len(records),
            "new_records": diff["incoming_new"],
            "existing_records": diff["incoming_existing"],
            "reconcile": diff,
        }

    def import_sync_envelope(self, envelope_path: str) -> dict[str, Any]:
        source = Path(envelope_path).expanduser()
        if not source.exists():
            raise FileNotFoundError(f"Sync envelope not found: {envelope_path}")
        envelope = json.loads(source.read_text(encoding="utf-8"))
        scope = envelope["scope"]
        incoming_revision = envelope.get("scope_revision") or {"revision": 0, "updated_at": None}
        policy = self.app.storage.get_scope_policy(scope["scope_type"], scope["scope_id"])
        if policy["sync_policy"] != "sync_eligible":
            raise ValueError("Only sync_eligible scopes can import sync envelopes.")
        records = envelope.get("records", [])
        local_rows = self.app.storage.fetch_all(
            """
            SELECT id, updated_at
            FROM memories
            WHERE scope_type = ? AND scope_id = ?
            """,
            (scope["scope_type"], scope["scope_id"]),
        )
        local_index = {row["id"]: row["updated_at"] for row in local_rows}
        diff = self._build_sync_reconcile_diff(local_index=local_index, records=records)
        local_revision = self.app.storage.get_scope_revision(scope["scope_type"], scope["scope_id"])
        if int(local_revision["revision"]) != int(incoming_revision.get("revision", 0)):
            diff["revision_mismatch"] = 1
        inserted = 0
        replaced = 0
        unchanged = 0
        for row in records:
            payload = dict(row)
            payload["metadata_json"] = json.dumps(payload.get("metadata_json") or {}, ensure_ascii=False)
            existing = local_index.get(payload["id"])
            if existing is None:
                inserted += 1
            elif existing == payload.get("updated_at"):
                unchanged += 1
            else:
                replaced += 1
            keys = [
                "id", "type", "scope_type", "scope_id", "session_id", "content", "summary", "subject",
                "source_kind", "source_ref", "status", "confidence", "activation_score", "access_count",
                "created_at", "updated_at", "last_accessed_at", "expires_at", "archived_at", "metadata_json",
            ]
            self.app.storage.execute(
                f"""
                INSERT OR REPLACE INTO memories ({", ".join(keys)})
                VALUES ({", ".join(["?"] * len(keys))})
                """,
                tuple(payload.get(key) for key in keys),
            )
        post_revision = self.app.storage.bump_scope_revision(scope["scope_type"], scope["scope_id"])
        return {
            "backend": "python",
            "imported": True,
            "scope": scope,
            "records": len(records),
            "reconcile": diff,
            "local_scope_revision_before": local_revision,
            "incoming_scope_revision": incoming_revision,
            "local_scope_revision_after": post_revision,
            "inserted_records": inserted,
            "replaced_records": replaced,
            "unchanged_records": unchanged,
            "path": str(source),
        }

    def _build_sync_reconcile_diff(
        self,
        *,
        local_index: dict[str, str | None],
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        incoming_index = {row["id"]: row.get("updated_at") for row in records}
        incoming_new = 0
        incoming_existing = 0
        revision_mismatch = 0
        for memory_id, updated_at in incoming_index.items():
            local_updated = local_index.get(memory_id)
            if local_updated is None:
                incoming_new += 1
                continue
            incoming_existing += 1
            if local_updated != updated_at:
                revision_mismatch += 1

        local_only = 0
        for memory_id in local_index:
            if memory_id not in incoming_index:
                local_only += 1

        return {
            "incoming_new": incoming_new,
            "incoming_existing": incoming_existing,
            "local_only": local_only,
            "revision_mismatch": revision_mismatch,
        }
