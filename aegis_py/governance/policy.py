from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from aegis_py.storage.db import DatabaseManager

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PolicyMatrix:
    id: str
    scope_type: str
    scope_id: str
    auto_resolve: bool = False
    auto_archive: bool = False
    auto_consolidate: bool = False
    auto_escalate: bool = False
    updated_at: datetime = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = _now_utc()


class PolicyManager:
    """Manages the governance rules for autonomous actions."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_policy(self, scope_type: str, scope_id: str) -> PolicyMatrix:
        """Retrieves the policy for a given scope, or returns a default restrictive policy."""
        row = self.db.fetch_one(
            "SELECT * FROM policy_matrix WHERE scope_type = ? AND scope_id = ?",
            (scope_type, scope_id)
        )
        
        if row:
            return PolicyMatrix(
                id=row['id'],
                scope_type=row['scope_type'],
                scope_id=row['scope_id'],
                auto_resolve=bool(row['auto_resolve']),
                auto_archive=bool(row['auto_archive']),
                auto_consolidate=bool(row['auto_consolidate']),
                auto_escalate=bool(row['auto_escalate']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
            
        # Return default restrictive policy (all False)
        return PolicyMatrix(
            id=str(uuid.uuid4()),
            scope_type=scope_type,
            scope_id=scope_id
        )

    def save_policy(self, policy: PolicyMatrix) -> None:
        """Saves or updates a policy matrix."""
        self.db.execute(
            """
            INSERT INTO policy_matrix (
                id, scope_type, scope_id, auto_resolve, auto_archive, 
                auto_consolidate, auto_escalate, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(scope_type, scope_id) DO UPDATE SET
                auto_resolve = excluded.auto_resolve,
                auto_archive = excluded.auto_archive,
                auto_consolidate = excluded.auto_consolidate,
                auto_escalate = excluded.auto_escalate,
                updated_at = excluded.updated_at
            """,
            (
                policy.id,
                policy.scope_type,
                policy.scope_id,
                int(policy.auto_resolve),
                int(policy.auto_archive),
                int(policy.auto_consolidate),
                int(policy.auto_escalate),
                _now_utc().isoformat()
            )
        )

    def can_auto_resolve(self, scope_type: str, scope_id: str) -> bool:
        return self.get_policy(scope_type, scope_id).auto_resolve
        
    def can_auto_archive(self, scope_type: str, scope_id: str) -> bool:
        return self.get_policy(scope_type, scope_id).auto_archive

    def can_auto_consolidate(self, scope_type: str, scope_id: str) -> bool:
        return self.get_policy(scope_type, scope_id).auto_consolidate
