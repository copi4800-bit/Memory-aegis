from typing import List, Optional
from datetime import datetime, timezone
from ..storage.manager import StorageManager
from ..storage.models import StyleSignal, StyleProfile

class PreferenceManager:
    """Manages the lifecycle of user preferences: collection -> consolidation -> recall."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage

    def consolidate_session(self, session_id: str, scope_id: str, scope_type: str):
        """Merges all signals from a session into the scope's StyleProfile."""
        
        # 1. Fetch current profile (or create new)
        profile = self.storage.get_profile(scope_id, scope_type)
        if not profile:
            profile = StyleProfile(
                id=f"prof_{scope_id[:6]}_{scope_type[:3]}",
                scope_id=scope_id,
                scope_type=scope_type,
                last_updated=datetime.now(timezone.utc),
                preferences_json={}
            )
            
        # 2. Fetch all signals for this session
        with self.storage._get_connection() as conn:
            rows = conn.execute(
                "SELECT signal_key, signal_value FROM style_signals WHERE session_id = ?",
                (session_id,)
            ).fetchall()
            
        if not rows:
            return
            
        # 3. Consolidation Logic (Recency Weighted / Simple Average)
        # Groups signals by key
        numeric_signals = {}
        categorical_signals = {}
        
        for row in rows:
            key = row['signal_key']
            val = row['signal_value']
            
            # Try to convert back to float if possible
            try:
                num_val = float(val)
                if key not in numeric_signals: numeric_signals[key] = []
                numeric_signals[key].append(num_val)
            except (ValueError, TypeError):
                categorical_signals[key] = val # Recency bias: last one wins
                
        # Update numeric fields (Weighted moving average would be better, but simple average for v1)
        for key, vals in numeric_signals.items():
            avg_val = sum(vals) / len(vals)
            
            # Mix with existing profile value (70% old, 30% new session avg)
            current_val = profile.preferences_json.get(key, 0.5)
            profile.preferences_json[key] = round((current_val * 0.7) + (avg_val * 0.3), 3)
            
        # Update categorical fields
        for key, val in categorical_signals.items():
            profile.preferences_json[key] = val
            
        # 4. Save
        profile.last_updated = datetime.now(timezone.utc)
        self.storage.upsert_profile(profile)
        
        # 5. Clean up session signals (optional, but keeps DB clean)
        with self.storage._get_connection() as conn:
            conn.execute("DELETE FROM style_signals WHERE session_id = ?", (session_id,))
            conn.commit()
