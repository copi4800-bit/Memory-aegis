from dataclasses import dataclass
from ..storage.manager import StorageManager

@dataclass
class HealthReport:
    total_memories: int
    active_memories: int
    orphaned_links: int

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
        
        return HealthReport(
            total_memories=total,
            active_memories=active,
            orphaned_links=orphans
        )
