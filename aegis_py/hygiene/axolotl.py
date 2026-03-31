import sqlite3
from dataclasses import dataclass
from ..storage.manager import StorageManager, LEGACY_COLUMN_REPAIRS

@dataclass
class RepairReport:
    schema_repaired: int
    fts_rebuilt: bool
    orphan_links_removed: int

class AxolotlBeast:
    """Handles schema repair, index rebuilds, and orphan cleanup."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage

    def soft_repair_schema(self) -> int:
        """Check PRAGMA table_info() and add missing columns."""
        repaired_columns = 0
        conn = self.storage._get_connection()
        for table_name, expected_columns in LEGACY_COLUMN_REPAIRS.items():
            if not self.storage._table_exists(table_name):
                continue
            existing_columns = self.storage._table_columns(table_name)
            for column_name, column_sql in expected_columns.items():
                if column_name not in existing_columns:
                    conn.execute(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
                    )
                    repaired_columns += 1
        conn.commit()
        return repaired_columns

    def rebuild_fts_index(self) -> bool:
        """Rebuild memories_fts from existing data."""
        try:
            conn = self.storage._get_connection()
            conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
            conn.commit()
            return True
        except Exception:
            return False

    def repair_orphan_links(self) -> int:
        """Delete links that point to non-existent memories."""
        conn = self.storage._get_connection()
        # Find orphan links
        # A link is orphaned if its source_id or target_id does not exist in memories
        sql = """
            DELETE FROM memory_links 
            WHERE source_id NOT IN (SELECT id FROM memories)
               OR target_id NOT IN (SELECT id FROM memories)
        """
        cursor = conn.execute(sql)
        deleted = cursor.rowcount
        conn.commit()
        return deleted

    def validate_integrity(self) -> RepairReport:
        """Runs all repair operations and returns a report."""
        schema_repaired = self.soft_repair_schema()
        fts_rebuilt = self.rebuild_fts_index()
        orphan_links_removed = self.repair_orphan_links()
        
        return RepairReport(
            schema_repaired=schema_repaired,
            fts_rebuilt=fts_rebuilt,
            orphan_links_removed=orphan_links_removed
        )
