from __future__ import annotations
import time
import uuid
import json
from typing import Any, Optional
from pathlib import Path

class AegisTelemetry:
    """
    Implements the Aegis Event & Telemetry Spec v1.0 from 6.md.
    Focuses on Outcome, Engagement, and Fidelity.
    """
    def __init__(self, log_path: str = "/tmp/aegis_telemetry.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_name: str,
        surface_name: str,
        payload: dict[str, Any],
        surface_mode: str = "compact",
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ):
        envelope = {
            "event_name": event_name,
            "event_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "iso_time": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "surface_name": surface_name,
            "surface_mode": surface_mode,
            "user_id_hash": hash(user_id), # Simple hash for demo
            "session_id": session_id,
            "payload": payload,
            "context": context or {},
            "engine_version": "8.0.0"
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(envelope, ensure_ascii=False) + "\n")

    # Shortcut for Surface Exposure (Requirement in 6.md)
    def track_exposure(self, surface: str, mode: str, details: dict[str, Any]):
        self.log_event(f"surface_exposure.{surface}.shown", surface, details, surface_mode=mode)

    # Shortcut for Outcome (The most important metric in 6.md)
    def track_outcome(self, event_type: str, details: dict[str, Any]):
        self.log_event(f"outcome.{event_type}", "system", details)
