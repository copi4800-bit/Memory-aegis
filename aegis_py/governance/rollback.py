import json
from datetime import datetime, timezone

from aegis_py.storage.db import DatabaseManager

class RollbackException(Exception):
    pass

class RollbackManager:
    """Handles reversing autonomous actions."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def rollback(self, audit_id: str) -> None:
        """
        Reverses an autonomous action based on its audit ID.
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # Fetch the audit log
            cursor.execute("SELECT * FROM autonomous_audit_log WHERE id = ?", (audit_id,))
            audit = cursor.fetchone()
            
            if not audit:
                raise RollbackException(f"Audit log entry {audit_id} not found.")
                
            if audit['status'] != 'applied':
                raise RollbackException(f"Cannot rollback action in status: {audit['status']}")
                
            details = json.loads(audit['details_json']) if audit['details_json'] else {}
            entity_type = audit['entity_type']
            entity_id = audit['entity_id']
            action_type = audit['action_type']
            
            if entity_type == 'memory':
                if details.get('created_memory'):
                    cursor.execute("DELETE FROM memories WHERE id = ?", (entity_id,))
                    cursor.execute("DELETE FROM memory_vectors WHERE memory_id = ?", (entity_id,))
                    cursor.execute("DELETE FROM evidence_artifacts WHERE memory_id = ?", (entity_id,))
                    previous_state = None
                else:
                    previous_state = details.get('previous_state')
                    if not previous_state:
                        raise RollbackException(f"Audit log entry {audit_id} missing 'previous_state' needed for rollback.")
                if previous_state is not None:
                    # Restore the previous state of the memory
                    cursor.execute(
                        """
                        UPDATE memories SET
                            type = ?,
                            scope_type = ?,
                            scope_id = ?,
                            session_id = ?,
                            content = ?,
                            summary = ?,
                            subject = ?,
                            source_kind = ?,
                            source_ref = ?,
                            origin_node_id = ?,
                            status = ?,
                            confidence = ?,
                            activation_score = ?,
                            access_count = ?,
                            created_at = ?,
                            updated_at = ?,
                            last_accessed_at = ?,
                            expires_at = ?,
                            archived_at = ?,
                            metadata_json = ?
                        WHERE id = ?
                        """,
                        (
                            previous_state.get('type'),
                            previous_state.get('scope_type'),
                            previous_state.get('scope_id'),
                            previous_state.get('session_id'),
                            previous_state.get('content'),
                            previous_state.get('summary'),
                            previous_state.get('subject'),
                            previous_state.get('source_kind'),
                            previous_state.get('source_ref'),
                            previous_state.get('origin_node_id'),
                            previous_state.get('status'),
                            previous_state.get('confidence'),
                            previous_state.get('activation_score'),
                            previous_state.get('access_count'),
                            previous_state.get('created_at'),
                            previous_state.get('updated_at'),
                            previous_state.get('last_accessed_at'),
                            previous_state.get('expires_at'),
                            previous_state.get('archived_at'),
                            json.dumps(previous_state.get('metadata_json', {})) if isinstance(previous_state.get('metadata_json'), dict) else previous_state.get('metadata_json', '{}'),
                            entity_id
                        )
                    )
            elif entity_type == 'memory_link':
                created_link = details.get('created_link')
                if created_link:
                    cursor.execute("DELETE FROM memory_links WHERE id = ?", (entity_id,))
                else:
                    previous_state = details.get('previous_state')
                    if not previous_state:
                        raise RollbackException(f"Audit log entry {audit_id} missing rollback details for memory_link.")
                    cursor.execute(
                        """
                        INSERT INTO memory_links (
                            id, source_id, target_id, link_type, weight, metadata_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            source_id = excluded.source_id,
                            target_id = excluded.target_id,
                            link_type = excluded.link_type,
                            weight = excluded.weight,
                            metadata_json = excluded.metadata_json,
                            created_at = excluded.created_at
                        """,
                        (
                            previous_state.get('id'),
                            previous_state.get('source_id'),
                            previous_state.get('target_id'),
                            previous_state.get('link_type'),
                            previous_state.get('weight', 1.0),
                            json.dumps(previous_state.get('metadata_json', {})) if isinstance(previous_state.get('metadata_json'), dict) else previous_state.get('metadata_json', '{}'),
                            previous_state.get('created_at'),
                        )
                    )
            else:
                raise RollbackException(f"Rollback not implemented for entity type: {entity_type}")
                
            # If the action was consolidation, there might be 'merged_from' entities in previous_state
            # that were deleted or archived which we would need to restore.
            # For this Phase, we are assuming 'previous_state' represents the single entity mutated.
            # More complex rollbacks (like un-consolidation) would need arrays of previous states.
            if action_type == 'consolidate' and 'merged_from_states' in details:
                for old_mem in details['merged_from_states']:
                    # Re-insert or un-archive them
                    # Basic un-archive for this example:
                    cursor.execute(
                        "UPDATE memories SET status = ? WHERE id = ?",
                        (old_mem.get('status', 'active'), old_mem['id'])
                    )
                    
            # Mark the audit log as rolled back
            cursor.execute(
                "UPDATE autonomous_audit_log SET status = 'rolled_back', rolled_back_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), audit_id)
            )
            
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e
