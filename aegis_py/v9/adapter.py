from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from ..storage.models import Memory
from .models import (
    MemoryRecordV9, 
    TrustSignals, 
    ConflictSignals, 
    CorrectionSignals, 
    LifecycleSignals, 
    MemoryState
)

def map_to_v9_record(
    memory: Memory, 
    storage: Any, # StorageManager
    query_context: Optional[Dict[str, Any]] = None
) -> MemoryRecordV9:
    """
    Adapter that bridges real Aegis storage data into the v9 Mathematical Model.
    This is the 'Body' for the v9 'Spirit'.
    """
    
    # 1. Map Trust Signals
    # We batch fetch these if possible, but for a single record we use repos
    evidence_count_row = storage.fetch_one(
        "SELECT count(*) as count FROM evidence_events WHERE memory_id = ?",
        (memory.id,)
    )
    evidence_count = evidence_count_row["count"] if evidence_count_row else 0
    
    support_row = storage.fetch_one(
        """
        SELECT COALESCE(SUM(weight), 0) as total FROM memory_links 
        WHERE (source_id = ? OR target_id = ?) 
        AND link_type IN ('supports', 'extends', 'same_subject')
        """,
        (memory.id, memory.id)
    )
    support_strength = float(support_row["total"]) if support_row else 0.0

    trust = TrustSignals(
        evidence_strength=min(1.0, evidence_count / 5.0), # Normalized: 5+ evidence = 1.0
        support_strength=min(1.0, support_strength / 3.0),
        trust_score=memory.confidence,
        stability_score=1.0 if memory.access_count > 10 else 0.5,
        source_quality=0.8 if memory.source_kind == "manual" else 0.5
    )

    # 2. Map Conflict Signals
    conflict_info = storage.batch_conflict_weight([memory.id]).get(memory.id, (0.0, False))
    conflict = ConflictSignals(
        open_conflict_count=1 if conflict_info[1] else 0,
        unresolved_contradiction=conflict_info[0],
        conflict_severity=min(1.0, conflict_info[0] * 0.5)
    )

    # 3. Map Correction Signals
    # If it's 'active' AND explicitly marked or has high metadata confidence, it's a winner
    # We avoid treating EVERY active record as a winner to prevent flashy-bias
    is_winner = (memory.status == "active") and (memory.metadata or {}).get("is_winner", False)
    is_superseded = (memory.status == "superseded")
    
    # Freshness calculation (Age in days normalized)
    now = datetime.now(timezone.utc)
    age_days = (now - memory.created_at).days
    freshness = max(0.0, 1.0 - (age_days / 30.0)) # 30 days = 0 freshness

    correction = CorrectionSignals(
        is_slot_winner=is_winner,
        is_superseded=is_superseded,
        correction_freshness=freshness,
        slot_priority=1.0 # Default
    )

    # 4. Map Lifecycle Signals
    # Map from real storage status to v9 MemoryState enum
    status_map = {
        "active": MemoryState.VALIDATED,
        "superseded": MemoryState.INVALIDATED,
        "archived": MemoryState.ARCHIVED,
        "draft": MemoryState.DRAFT
    }
    
    # Priority: Metadata override > Direct status map > Default DRAFT
    target_state = MemoryState.DRAFT
    metadata_state = (memory.metadata or {}).get("memory_state")
    if metadata_state and any(s.value == metadata_state for s in MemoryState):
        target_state = MemoryState(metadata_state)
    else:
        target_state = status_map.get(memory.status, MemoryState.DRAFT)

    lifecycle = LifecycleSignals(
        usage_count=memory.access_count,
        validated_reuse_count=memory.access_count, # Simplified
        last_meaningful_use_at=memory.last_accessed_at,
        last_updated_at=memory.updated_at,
        decay_rate=0.01, # Default
        staleness_index=min(1.0, age_days / 90.0), # 90 days = fully stale
        memory_state=target_state
    )

    # 5. Build Unified v9 Record
    metadata = memory.metadata or {}
    return MemoryRecordV9(
        id=memory.id,
        content=memory.content,
        canonical_subject=memory.subject or "general",
        fact_slot=memory.subject,
        memory_type=memory.type,
        
        # Semantic properties from metadata or inferred
        fact_kind=metadata.get("fact_kind", "multivalued"),
        singleton_fact=metadata.get("singleton_fact", False),
        
        trust=trust,
        conflict=conflict,
        correction=correction,
        lifecycle=lifecycle,
        metadata=metadata
    )
