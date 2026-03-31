from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from ..hygiene.transitions import now_iso


class ScopeRepository:
    """Scope policy, scope revision, and style profile helpers."""

    def __init__(self, storage: Any):
        self.storage = storage

    def put_signal(self, signal: Any) -> None:
        data = signal.model_dump()
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if "signal_value" in data and isinstance(data["signal_value"], (dict, list)):
            data["signal_value"] = json.dumps(data["signal_value"])
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        conn = self.storage._get_connection()
        conn.execute(f"INSERT OR REPLACE INTO style_signals ({keys}) VALUES ({placeholders})", list(data.values()))
        conn.commit()

    def get_profile(self, scope_id: str, scope_type: str) -> Any | None:
        conn = self.storage._get_connection()
        row = conn.execute(
            "SELECT * FROM style_profiles WHERE scope_id = ? AND scope_type = ? LIMIT 1",
            (scope_id, scope_type),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        filtered = {
            "id": data.get("id") or data.get("agent_id") or f"{scope_type}:{scope_id}",
            "scope_id": data.get("scope_id", scope_id),
            "scope_type": data.get("scope_type", scope_type),
            "preferences_json": data.get("preferences_json") or "{}",
            "last_updated": data.get("last_updated") or data.get("updated_at") or now_iso(),
        }
        filtered["last_updated"] = datetime.fromisoformat(filtered["last_updated"])
        if isinstance(filtered["preferences_json"], str):
            filtered["preferences_json"] = json.loads(filtered["preferences_json"])
        from .models import StyleProfile

        return StyleProfile(**filtered)

    def upsert_profile(self, profile: Any) -> None:
        data = profile.model_dump()
        data["last_updated"] = data["last_updated"].isoformat()
        data["preferences_json"] = json.dumps(data["preferences_json"])
        existing_columns = self.storage._table_columns("style_profiles")
        if "updated_at" in existing_columns and "updated_at" not in data:
            data["updated_at"] = data["last_updated"]
        if "agent_id" in existing_columns and "agent_id" not in data:
            data["agent_id"] = data["id"]

        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        conn = self.storage._get_connection()
        conn.execute(
            f"INSERT OR REPLACE INTO style_profiles ({keys}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()

    def set_scope_policy(
        self,
        scope_type: str,
        scope_id: str,
        *,
        sync_policy: str,
        sync_state: str = "local",
        last_sync_at: str | None = None,
    ) -> None:
        now = now_iso()
        conn = self.storage._get_connection()
        conn.execute(
            """
            INSERT INTO scope_policies (
                scope_type, scope_id, sync_policy, sync_state, last_sync_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(scope_type, scope_id) DO UPDATE SET
                sync_policy=excluded.sync_policy,
                sync_state=excluded.sync_state,
                last_sync_at=excluded.last_sync_at,
                updated_at=excluded.updated_at
            """,
            (scope_type, scope_id, sync_policy, sync_state, last_sync_at, now),
        )
        conn.commit()
        self.ensure_scope_revision(scope_type, scope_id)

    def get_scope_policy(self, scope_type: str, scope_id: str) -> dict[str, Any]:
        row = self.storage.fetch_one(
            """
            SELECT scope_type, scope_id, sync_policy, sync_state, last_sync_at, updated_at
            FROM scope_policies
            WHERE scope_type = ? AND scope_id = ?
            """,
            (scope_type, scope_id),
        )
        if row is not None:
            return dict(row)
        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "sync_policy": "local_only",
            "sync_state": "local",
            "last_sync_at": None,
            "updated_at": None,
            "derived": True,
        }

    def list_scope_policies(self, sync_policy: str | None = None) -> list[dict[str, Any]]:
        params: tuple[Any, ...] = ()
        where = ""
        if sync_policy is not None:
            where = "WHERE sync_policy = ?"
            params = (sync_policy,)
        rows = self.storage.fetch_all(
            f"""
            SELECT scope_type, scope_id, sync_policy, sync_state, last_sync_at, updated_at
            FROM scope_policies
            {where}
            ORDER BY scope_type ASC, scope_id ASC
            """,
            params,
        )
        return [dict(row) for row in rows]

    def ensure_scope_revision(self, scope_type: str, scope_id: str, *, commit: bool = True) -> None:
        now = now_iso()
        conn = self.storage._get_connection()
        conn.execute(
            """
            INSERT INTO scope_revisions (scope_type, scope_id, revision, updated_at)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(scope_type, scope_id) DO NOTHING
            """,
            (scope_type, scope_id, now),
        )
        if commit:
            conn.commit()

    def get_scope_revision(self, scope_type: str, scope_id: str) -> dict[str, Any]:
        row = self.storage.fetch_one(
            """
            SELECT scope_type, scope_id, revision, updated_at
            FROM scope_revisions
            WHERE scope_type = ? AND scope_id = ?
            """,
            (scope_type, scope_id),
        )
        if row is not None:
            return dict(row)
        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "revision": 0,
            "updated_at": None,
            "derived": True,
        }

    def bump_scope_revision(self, scope_type: str, scope_id: str, *, commit: bool = True) -> dict[str, Any]:
        now = now_iso()
        conn = self.storage._get_connection()
        conn.execute(
            """
            INSERT INTO scope_revisions (scope_type, scope_id, revision, updated_at)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(scope_type, scope_id) DO UPDATE SET
                revision = scope_revisions.revision + 1,
                updated_at = excluded.updated_at
            """,
            (scope_type, scope_id, now),
        )
        if commit:
            conn.commit()
        return self.get_scope_revision(scope_type, scope_id)
