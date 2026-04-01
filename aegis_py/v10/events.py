from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .models import GovernanceStatus

@dataclass
class GovernanceEvent:
    """A discrete governance action or state change."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_id: str = ""
    actor_type: str = "system" # system | user | operator
    action: str = "" # admitted | promoted | demoted | superseded | quarantined | revoked
    
    previous_state: Optional[str] = None
    next_state: Optional[str] = None
    
    triggering_rule: Optional[str] = None
    reason_text: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class EventLogger:
    """Sinks governance events to storage for auditability."""
    def __init__(self, storage: Any):
        self.storage = storage

    def log(self, event: GovernanceEvent):
        """Persists the event to the database."""
        import json
        scope_type = event.metadata.get("scope_type", "agent")
        scope_id = event.metadata.get("scope_id", "default")
        
        self.storage.execute(
            """
            INSERT INTO governance_events (
                id, event_kind, scope_type, scope_id, memory_id,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.action,
                scope_type,
                scope_id,
                event.memory_id,
                json.dumps(event.metadata, ensure_ascii=True),
                event.timestamp.isoformat()
            )
        )
