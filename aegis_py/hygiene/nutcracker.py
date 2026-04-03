from dataclasses import dataclass
from ..storage.manager import StorageManager

@dataclass
class HealthReport:
    total_memories: int
    active_memories: int
    orphaned_links: int
    deinosuchus_compaction_pressure: float

class NutcrackerBeast:
    """Storage hygiene: vacuuming and health checks."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage

    def vacuum_db(self):
        """Executes SQLite VACUUM to reclaim space."""
        conn = self.storage._get_connection()
        conn.execute("VACUUM")
        conn.commit()

    def count_orphans(self) -> int:
        """Đếm records mồ côi (links trỏ tới memory không tồn tại)."""
        row = self.storage.fetch_one("""
            SELECT COUNT(*) as count FROM memory_links 
            WHERE source_id NOT IN (SELECT id FROM memories)
               OR target_id NOT IN (SELECT id FROM memories)
        """)
        return row["count"] if row else 0

    def check_db_health(self) -> HealthReport:
        """Kiểm tra sức khỏe DB."""
        total = self.storage.fetch_one("SELECT COUNT(*) as count FROM memories")["count"]
        active = self.storage.fetch_one("SELECT COUNT(*) as count FROM memories WHERE status = 'active'")["count"]
        orphans = self.count_orphans()
        archived = self.storage.fetch_one("SELECT COUNT(*) as count FROM memories WHERE status = 'archived'")["count"]
        superseded = self.storage.fetch_one("SELECT COUNT(*) as count FROM memories WHERE status = 'superseded'")["count"]
        deinosuchus_compaction_pressure = min(
            0.99,
            0.28
            + (min(orphans, 4) * 0.16)
            + (min(archived + superseded, max(total, 1)) / max(total, 1)) * 0.4,
        )
        
        return HealthReport(
            total_memories=total,
            active_memories=active,
            orphaned_links=orphans,
            deinosuchus_compaction_pressure=round(deinosuchus_compaction_pressure, 3),
        )

    def check_scope_health(self, scope_type: str, scope_id: str) -> dict[str, float | int | str]:
        total = self.storage.fetch_one(
            "SELECT COUNT(*) as count FROM memories WHERE scope_type = ? AND scope_id = ?",
            (scope_type, scope_id),
        )["count"]
        active = self.storage.fetch_one(
            "SELECT COUNT(*) as count FROM memories WHERE scope_type = ? AND scope_id = ? AND status = 'active'",
            (scope_type, scope_id),
        )["count"]
        archived = self.storage.fetch_one(
            "SELECT COUNT(*) as count FROM memories WHERE scope_type = ? AND scope_id = ? AND status = 'archived'",
            (scope_type, scope_id),
        )["count"]
        superseded = self.storage.fetch_one(
            "SELECT COUNT(*) as count FROM memories WHERE scope_type = ? AND scope_id = ? AND status = 'superseded'",
            (scope_type, scope_id),
        )["count"]
        orphans = self.storage.fetch_one(
            """
            SELECT COUNT(*) as count FROM memory_links l
            JOIN memories m ON l.source_id = m.id
            WHERE m.scope_type = ? AND m.scope_id = ?
              AND (
                l.source_id NOT IN (SELECT id FROM memories)
                OR l.target_id NOT IN (SELECT id FROM memories)
              )
            """,
            (scope_type, scope_id),
        )["count"]
        pressure = min(
            0.99,
            0.24
            + (min(orphans, 4) * 0.14)
            + ((archived + superseded) / max(total, 1)) * 0.42,
        )
        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "total_memories": total,
            "active_memories": active,
            "orphaned_links": orphans,
            "deinosuchus_compaction_pressure": round(pressure, 3),
        }
