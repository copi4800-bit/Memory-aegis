import sqlite3
from typing import Tuple, Optional

class ConflictDetector:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        
    def detect_conflict(self, entity_type: str, entity_id: str, incoming_origin: str) -> Tuple[bool, Optional[str]]:
        """
        Detects if an incoming mutation conflicts with local state.
        Returns (is_conflict, local_origin_node_id).
        
        Rule: If an entity exists locally and its last known origin differs 
        from the incoming payload's origin, it's flagged as a conflict. 
        This prevents silent overwrites of concurrent edits across different nodes.
        """
        if entity_type == "memory":
            cursor = self.conn.cursor()
            cursor.execute("SELECT origin_node_id FROM memories WHERE id = ?", (entity_id,))
            row = cursor.fetchone()
            
            if not row:
                # Entity doesn't exist locally, no conflict
                return False, None
                
            local_origin = row[0]
            
            # If origins don't match, we have a potential concurrent edit.
            # Example: Node A created it, Node B edits it. When B syncs to A,
            # Node A sees local_origin (A) != incoming (B), so it flags as conflict.
            # If A synced it from B, local_origin is B. If B updates it again, 
            # local_origin (B) == incoming (B), so no conflict.
            if local_origin != incoming_origin:
                return True, local_origin
                
        return False, None
