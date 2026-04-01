from __future__ import annotations
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from .models import DecisionObject, TruthRole, GovernanceStatus

@dataclass
class ReviewItem:
    """An entry in the governance review queue."""
    memory_id: str
    reason: str
    priority: float = 0.0
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewQueueV10:
    """Manages high-entropy or high-risk memories that require intervention."""
    
    def __init__(self, storage: Any):
        self.storage = storage
        self.queue: List[ReviewItem] = []

    def enqueue(self, d: DecisionObject, m: Any, reason: str):
        """Adds a memory to the review queue with calculated priority."""
        # Q_priority = risk + impact + ambiguity
        risk = 1.0 if d.governance_status == GovernanceStatus.QUARANTINED else 0.5
        impact = 1.0 if d.truth_role == TruthRole.WINNER else 0.3
        
        # Calculate ambiguity from score trace if available
        ambiguity = 0.0
        if d.score_trace:
            # Placeholder for entropy calculation
            ambiguity = 0.5
            
        priority = risk * 0.4 + impact * 0.4 + ambiguity * 0.2
        
        item = ReviewItem(
            memory_id=d.memory_id,
            reason=reason,
            priority=priority,
            context_snapshot={"status": d.governance_status.value, "role": d.truth_role.value}
        )
        self.queue.append(item)
        # In real system, this persists to a 'review_queue' table
        self._persist_to_db(item)

    def _persist_to_db(self, item: ReviewItem):
        import json
        self.storage.execute(
            """
            INSERT INTO review_queue (id, memory_id, reason, priority, status, context_json, created_at) 
            VALUES (?, ?, ?, ?, 'open', ?, ?)
            """,
            (
                f"rev_{uuid.uuid4().hex[:12]}",
                item.memory_id, 
                item.reason, 
                item.priority, 
                json.dumps(item.context_snapshot), 
                item.created_at.isoformat()
            )
        )

    def list_pending(self) -> List[ReviewItem]:
        """Returns sorted pending reviews."""
        self.queue.sort(key=lambda x: x.priority, reverse=True)
        return self.queue
