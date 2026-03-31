from __future__ import annotations
from typing import Any, Dict, List
from ..storage.manager import StorageManager
from .i18n import get_text

class MemoryHealthSnapshot:
    """Diagnoses memory health and provides actionable insights (6.md compliant)."""

    def __init__(self, storage: StorageManager, locale: str = "vi"):
        self.storage = storage
        self.locale = locale

    def diagnose(self, scope_type: str = "agent", scope_id: str = "default") -> Dict[str, Any]:
        """Runs full system diagnosis for a specific scope."""
        
        # 1. Gather raw counts
        total_active = self.storage.fetch_one(
            "SELECT count(*) as count FROM memories WHERE status = 'active' AND scope_type = ? AND scope_id = ?",
            (scope_type, scope_id)
        )["count"]
        
        stale_count = self.storage.fetch_one(
            """
            SELECT count(*) as count FROM memories 
            WHERE status = 'active' AND scope_type = ? AND scope_id = ?
            AND (access_count = 0 AND (last_accessed_at IS NULL OR last_accessed_at < datetime('now', '-30 days')))
            """,
            (scope_type, scope_id)
        )["count"]

        # 2. Check for conflict clusters
        conflicts = self.storage.fetch_all(
            """
            SELECT subject, count(*) as count FROM memories 
            WHERE status = 'active' AND scope_type = ? AND scope_id = ? AND subject IS NOT NULL
            GROUP BY subject HAVING count > 1
            """,
            (scope_type, scope_id)
        )
        
        num_conflicts = len(conflicts)
        
        # 3. Determine overall health level
        if num_conflicts > 5 or total_active > 1000:
            health_level = "critical"
        elif num_conflicts > 0 or stale_count > 10:
            health_level = "warning"
        elif total_active > 0:
            health_level = "good"
        else:
            health_level = "perfect"

        # 4. Build narrative & insights
        # This will be formatted by app.py later with honorifics
        return {
            "health_level": health_level,
            "total_active": total_active,
            "num_conflicts": num_conflicts,
            "num_stale": stale_count,
            "locale": self.locale
        }

    def _generate_summary(self, total: int, conflicts: int, stale: int) -> str:
        if self.locale == "vi":
            msg = f"Hệ thống đang quản lý {total} ký ức."
            if conflicts > 0:
                msg += f" Có {conflicts} xung đột cần xử lý."
            if stale > 0:
                msg += f" Có {stale} thông tin đã cũ."
            return msg
        else:
            msg = f"System is managing {total} memories."
            if conflicts > 0:
                msg += f" {conflicts} conflicts detected."
            if stale > 0:
                msg += f" {stale} stale items found."
            return msg
