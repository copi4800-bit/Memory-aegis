from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Any, List, Optional, Dict

from .app import AegisApp
from .storage.models import Memory
from .surface import normalize_retrieval_mode

class Aegis:
    """
    Aegis Zero-Config Facade (Layer 2).
    Hides complexity, doesn't kill it.
    """
    
    def __init__(self, app: AegisApp):
        self._app = app

    @classmethod
    def auto(cls, db_path: Optional[str] = None) -> Aegis:
        """
        One-command initialization.
        Automatically handles DB creation, migrations, and health checks.
        """
        # Default path: ~/.openclaw/aegis_v10.db
        # Tên file chứa 'v10' để AegisApp kích hoạt logic v10
        if db_path is None:
            default_dir = Path.home() / ".openclaw"
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(default_dir / "aegis_v10.db")
            
        app = AegisApp(db_path=db_path)
        return cls(app)

    def remember(
        self, 
        content: str, 
        subject: Optional[str] = None, 
        scope_id: str = "default", 
        scope_type: str = "agent",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a new memory. 
        Uses the high-level ingest engine to ensure full v9/v10 processing.
        """
        metadata = metadata or {}
        
        # Facade default: if it's manual user input, it's a winner candidate
        if "is_winner" not in metadata:
            metadata["is_winner"] = True

        # Patch A: Slot Collision Detection
        # If we have a subject and not a correction, check for existing active memories
        if subject and not metadata.get("is_correction"):
            active_rows = self._app.storage.fetch_all(
                "SELECT content FROM memories WHERE subject = ? AND scope_id = ? AND scope_type = ? AND status = 'active'",
                (subject, scope_id, scope_type)
            )
            # If any active memory for this subject has different content, flag as conflict candidate
            if active_rows and any(row["content"] != content for row in active_rows):
                metadata["conflict_candidate"] = True
                metadata["requires_review"] = True
                # If it's a conflict candidate, maybe it shouldn't be an automatic winner 
                # to avoid retiring the old one until resolved?
                # Actually, Patch A says 'detect collision' but still let it in.
                # In zero-config facade, we might want to keep both active.
                metadata["is_winner"] = False 

        # We use app.put_memory which goes through IngestEngine
        # In the facade, we default to manual source and HIGH confidence
        # to ensure user-initiated facts aren't blocked by low-score policy gates.
        mem = self._app.put_memory(
            content=content,
            subject=subject,
            scope_id=scope_id,
            scope_type=scope_type,
            source_kind="manual",
            confidence=1.0,
            activation_score=1.0,
            metadata=metadata
        )
        
        # If ingest rejected it (likely duplicate or filtered)
        if not mem:
            # 1. Check for exact content duplicate
            rows = self._app.storage.fetch_all(
                "SELECT id FROM memories WHERE content = ? AND scope_id = ? AND scope_type = ?",
                (content, scope_id, scope_type)
            )
            if rows:
                return rows[0]["id"]
            
            # 2. Check for same subject "slot" winner if subject was provided
            if subject:
                slot_rows = self._app.storage.fetch_all(
                    "SELECT id FROM memories WHERE subject = ? AND scope_id = ? AND scope_type = ? AND status = 'active'",
                    (subject, scope_id, scope_type)
                )
                if slot_rows:
                    return slot_rows[0]["id"]

            return "rejected_by_policy"
            
        # Facade auto-indexes for immediate recall
        try:
            self._app.storage.memory.index_memory_vector(mem.id)
        except:
            pass
            
        return mem.id

    def recall(
        self, 
        query: str, 
        scope_id: str = "default", 
        scope_type: str = "agent",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories. 
        Automatically applies Governance (Superseded/Quarantine) and returns clean results.
        """
        results = self._app.search_payload(
            query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            retrieval_mode="explain" # Default to explainable for best UX
        )

        # Patch B: Recall Conflict Guard
        if self._has_slot_conflict(results):
            for r in results:
                r["facade_conflict_detected"] = True
                r["facade_conflict_message"] = "Có xung đột thông tin cần sếp xem lại."

        return results

    def _has_slot_conflict(self, results: List[Dict[str, Any]]) -> bool:
        """Detects if top results contain conflicting truths for the same subject."""
        if not results:
            return False

        # 1. Check main results for implicit slot collision
        subjects: Dict[str, str] = {}
        for r in results:
            # Handle nested memory object from serialize_search_result
            m = r.get("memory", {})
            
            # Check for explicit governance conflict status
            gov_status = r.get("governance_status") or m.get("status")
            if gov_status in {"quarantined", "pending_review", "disputed"}:
                return True
            
            subj = m.get("subject")
            if not subj:
                continue
            
            content = m.get("content")
            if subj not in subjects:
                subjects[subj] = content
            elif subjects[subj] != content:
                # Same subject, different content in top results = conflict
                return True

        # 2. Check first result's suppressed candidates for conflict indicators (v10)
        # In v10, a conflicting or high-entropy memory might be moved to suppressed
        first = results[0]
        for suppressed in first.get("suppressed_candidates", []):
            reason = suppressed.get("reason", "")
            # v10 often uses 'Chặn bởi Policy' for suppressed contenders
            if "Policy" in reason:
                return True
                
        return False

    def correct(
        self, 
        new_content: str, 
        subject: Optional[str] = None,
        old_content_hint: Optional[str] = None,
        scope_id: str = "default", 
        scope_type: str = "agent"
    ) -> str:
        """
        Update an existing memory (Truth Correction).
        Uses Governance-native path via MemoryManager and links.
        """
        # 1. Find candidates to supersede
        old_ids = []
        if subject:
            rows = self._app.storage.fetch_all(
                "SELECT id FROM memories WHERE subject = ? AND scope_id = ? AND scope_type = ? AND status = 'active'",
                (subject, scope_id, scope_type)
            )
            old_ids = [row["id"] for row in rows]
        elif old_content_hint:
            # Search-based correction
            search_res = self._app.search(old_content_hint, scope_id=scope_id, scope_type=scope_type, limit=1)
            old_ids = [r.memory.id for r in search_res if r.score > 0.6]

        # 2. Prepare correction metadata
        metadata = {
            "is_correction": True,
            "is_winner": True,
            "corrected_from": old_ids # Native path: IngestEngine will retire these
        }

        # 3. Put new winner via native ingest
        new_id = self.remember(
            content=new_content,
            subject=subject,
            scope_id=scope_id,
            scope_type=scope_type,
            metadata=metadata
        )
        
        # Facade Step 4: No manual transitions needed if IngestEngine succeeded, 
        # but if we have old_ids that IngestEngine might have missed (unlikely now), 
        # we still check UX consistency. 
        # Actually, let's trust the native path for better governance audit logs.
            
        return new_id

    def status(self) -> Dict[str, Any]:
        """
        Returns a human-readable health snapshot.
        """
        raw_status = self._app.status()
        health_info = self._app.health_surface.status()
        
        counts = health_info.get("counts", {})
        active_count = counts.get("active", 0)
        
        return {
            "state": health_info.get("health_state", "UNKNOWN"),
            "db_path": self._app.db_path,
            "memory_count": active_count,
            "counts_by_status": counts,
            "is_ready": health_info.get("health_state") == "HEALTHY"
        }

    def __repr__(self):
        s = self.status()
        return f"<Aegis Facade: {s['state']} | {s['memory_count']} memories>"
