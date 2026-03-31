from __future__ import annotations

import socket
import uuid
import platform
from datetime import datetime, timezone
from dataclasses import dataclass
from aegis_py.storage.db import DatabaseManager


@dataclass
class NodeIdentity:
    node_id: str
    is_local: bool
    name: str
    created_at: datetime


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class IdentityManager:
    """Manages node identities for replication provenance."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_local_identity(self) -> NodeIdentity:
        """Retrieves the local node identity, generating one if it doesn't exist."""
        row = self.db.fetch_one("SELECT * FROM node_identities WHERE is_local = 1")
        if row:
            return NodeIdentity(
                node_id=row['node_id'],
                is_local=bool(row['is_local']),
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        
        # Generate new identity
        node_id = str(uuid.uuid4())
        name = f"{socket.gethostname()}-{platform.system()}"
        created_at = _now_utc().isoformat()

        self.db.execute(
            "INSERT INTO node_identities (node_id, is_local, name, created_at) VALUES (?, 1, ?, ?)",
            (node_id, name, created_at)
        )
        return NodeIdentity(
            node_id=node_id,
            is_local=True,
            name=name,
            created_at=datetime.fromisoformat(created_at)
        )

    def register_remote_identity(self, node_id: str, name: str) -> NodeIdentity:
        """Registers or retrieves a remote node identity."""
        row = self.db.fetch_one("SELECT * FROM node_identities WHERE node_id = ?", (node_id,))
        if row:
            return NodeIdentity(
                node_id=row['node_id'],
                is_local=bool(row['is_local']),
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        
        created_at = _now_utc().isoformat()
        self.db.execute(
            "INSERT INTO node_identities (node_id, is_local, name, created_at) VALUES (?, 0, ?, ?)",
            (node_id, name, created_at)
        )
        return NodeIdentity(
            node_id=node_id,
            is_local=False,
            name=name,
            created_at=datetime.fromisoformat(created_at)
        )
