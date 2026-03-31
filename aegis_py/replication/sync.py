from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Dict

from aegis_py.storage.db import DatabaseManager
from aegis_py.replication.identity import IdentityManager
from aegis_py.replication.conflict import ConflictDetector
from aegis_py.observability.metrics import SyncMetricsTracker


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Mutation:
    action: str  # 'upsert', 'delete'
    entity_type: str  # 'memory', 'memory_link'
    entity_id: str
    data: dict[str, Any]
    timestamp: datetime


@dataclass
class ReplicationPayload:
    payload_id: str
    origin_node_id: str
    scope_type: str
    scope_id: str
    mutations: List[Mutation]
    generated_at: datetime = field(default_factory=_now_utc)


class SyncManager:
    def __init__(self, db: DatabaseManager, identity_manager: IdentityManager):
        self.db = db
        self.identity_manager = identity_manager

    def apply_payload(self, payload: ReplicationPayload) -> Dict[str, Any]:
        """
        Idempotently applies a replication payload.
        Returns statistics about the application.
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        detector = ConflictDetector(conn)
        
        # Calculate lag
        lag_seconds = (datetime.now(timezone.utc) - payload.generated_at).total_seconds()
        SyncMetricsTracker.log_sync_lag(payload.origin_node_id, max(0, lag_seconds))
        
        stats = {
            "applied": 0,
            "skipped": 0,
            "conflicts": 0,
            "errors": 0
        }
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # Ensure the origin node is registered
            # We don't have the node's name, so we use its ID as placeholder if new
            self.identity_manager.register_remote_identity(payload.origin_node_id, f"node-{payload.origin_node_id[:8]}")
            
            for mutation in payload.mutations:
                # 1. Check idempotency: Have we applied this mutation from this payload already?
                cursor.execute(
                    "SELECT id FROM replication_audit_log WHERE payload_id = ? AND entity_id = ? AND status = 'applied'",
                    (payload.payload_id, mutation.entity_id)
                )
                if cursor.fetchone():
                    stats["skipped"] += 1
                    continue
                    
                audit_id = str(uuid.uuid4())
                audit_status = 'applied'
                
                try:
                    if mutation.entity_type == "memory":
                        if mutation.action == "upsert":
                            is_conflict, local_origin = detector.detect_conflict(
                                mutation.entity_type, 
                                mutation.entity_id, 
                                payload.origin_node_id
                            )
                            
                            data = mutation.data
                            status = "reconcile_required" if is_conflict else data.get('status', 'active')
                            if is_conflict:
                                audit_status = 'conflict'
                                stats["conflicts"] += 1
                            
                            # SQLite UPSERT logic
                            cursor.execute(
                                """
                                INSERT INTO memories (
                                    id, type, scope_type, scope_id, session_id, content, summary, 
                                    subject, source_kind, source_ref, origin_node_id, status, 
                                    confidence, activation_score, access_count, created_at, 
                                    updated_at, last_accessed_at, expires_at, archived_at, metadata_json
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(id) DO UPDATE SET
                                    type = excluded.type,
                                    scope_type = excluded.scope_type,
                                    scope_id = excluded.scope_id,
                                    session_id = excluded.session_id,
                                    content = excluded.content,
                                    summary = excluded.summary,
                                    subject = excluded.subject,
                                    source_kind = excluded.source_kind,
                                    source_ref = excluded.source_ref,
                                    origin_node_id = excluded.origin_node_id,
                                    status = excluded.status,
                                    confidence = excluded.confidence,
                                    activation_score = excluded.activation_score,
                                    access_count = excluded.access_count,
                                    updated_at = excluded.updated_at,
                                    last_accessed_at = excluded.last_accessed_at,
                                    expires_at = excluded.expires_at,
                                    archived_at = excluded.archived_at,
                                    metadata_json = excluded.metadata_json
                                """,
                                (
                                    data.get('id', mutation.entity_id),
                                    data.get('type', 'semantic'),
                                    data.get('scope_type', payload.scope_type),
                                    data.get('scope_id', payload.scope_id),
                                    data.get('session_id'),
                                    data.get('content', ''),
                                    data.get('summary'),
                                    data.get('subject'),
                                    data.get('source_kind', 'sync'),
                                    data.get('source_ref'),
                                    payload.origin_node_id,
                                    status,
                                    data.get('confidence', 1.0),
                                    data.get('activation_score', 1.0),
                                    data.get('access_count', 0),
                                    data.get('created_at', _now_utc().isoformat()),
                                    data.get('updated_at', _now_utc().isoformat()),
                                    data.get('last_accessed_at'),
                                    data.get('expires_at'),
                                    data.get('archived_at'),
                                    json.dumps(data.get('metadata_json', {})) if isinstance(data.get('metadata_json'), dict) else data.get('metadata_json', '{}')
                                )
                            )
                        elif mutation.action == "delete":
                            cursor.execute("DELETE FROM memories WHERE id = ?", (mutation.entity_id,))
                            
                    cursor.execute(
                        """
                        INSERT INTO replication_audit_log (
                            id, payload_id, origin_node_id, entity_type, entity_id, action, applied_at, status, details_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            audit_id,
                            payload.payload_id,
                            payload.origin_node_id,
                            mutation.entity_type,
                            mutation.entity_id,
                            mutation.action,
                            _now_utc().isoformat(),
                            audit_status,
                            json.dumps(mutation.data)
                        )
                    )
                    
                    if audit_status == 'applied':
                        stats["applied"] += 1
                except Exception as e:
                    cursor.execute(
                        """
                        INSERT INTO replication_audit_log (
                            id, payload_id, origin_node_id, entity_type, entity_id, action, applied_at, status, details_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            audit_id,
                            payload.payload_id,
                            payload.origin_node_id,
                            mutation.entity_type,
                            mutation.entity_id,
                            mutation.action,
                            _now_utc().isoformat(),
                            'failed',
                            json.dumps({"error": str(e), "data": mutation.data})
                        )
                    )
                    stats["errors"] += 1
                    SyncMetricsTracker.record_sync_failure(payload.origin_node_id, payload.payload_id, len(payload.mutations), str(e))
            
            cursor.execute("COMMIT")
            SyncMetricsTracker.record_sync_success(payload.origin_node_id, payload.payload_id, stats["applied"], stats["skipped"], stats["conflicts"])
        except Exception as e:
            cursor.execute("ROLLBACK")
            SyncMetricsTracker.record_sync_failure(payload.origin_node_id, payload.payload_id, len(payload.mutations), f"Transaction failed: {str(e)}")
            raise
            
        return stats
