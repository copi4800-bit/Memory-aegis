import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from ..storage.models import Memory

class MemoryFactory:
    """Factory to create Memory instances with type-specific defaults."""
    
    @staticmethod
    def create(
        type: str,
        content: str,
        scope_type: str,
        scope_id: str,
        source_kind: str,
        source_ref: Optional[str] = None,
        subject: Optional[str] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        confidence: float = 1.0,
        activation_score: float = 1.0,
    ) -> Memory:
        now = datetime.now(timezone.utc)
        expires_at = None
        
        # Type-specific logic
        if type == "working":
            # Working memory expires after 24 hours by default
            expires_at = now + timedelta(hours=24)
        
        return Memory(
            id=f"mem_{uuid.uuid4().hex[:12]}",
            type=type,
            scope_type=scope_type,
            scope_id=scope_id,
            content=content,
            summary=summary,
            subject=subject,
            source_kind=source_kind,
            source_ref=source_ref,
            metadata=metadata or {},
            confidence=confidence,
            activation_score=activation_score,
            expires_at=expires_at,
            session_id=session_id
        )
