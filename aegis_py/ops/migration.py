import os
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("aegis.ops.migration")

class MigrationError(Exception):
    pass

class MigrationManager:
    """Manages SQLite schema versions and incremental migrations using PRAGMA user_version."""

    def __init__(self, db_conn: sqlite3.Connection, migrations_dir: str):
        self.conn = db_conn
        self.migrations_dir = Path(migrations_dir)
        
    def get_current_version(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA user_version")
        return cursor.fetchone()[0]
        
    def set_version(self, version: int) -> None:
        # PRAGMA commands can't use parameters bindings normally, so we format securely
        self.conn.execute(f"PRAGMA user_version = {int(version)}")

    def _get_migration_files(self) -> List[Path]:
        """Returns a sorted list of .sql files in the migrations directory."""
        if not self.migrations_dir.exists():
            return []
        files = list(self.migrations_dir.glob("*.sql"))
        # Sort by filename which should be prefixed with number (e.g. 001_baseline.sql)
        files.sort(key=lambda p: p.name)
        return files

    def run_migrations(self) -> None:
        """Runs all pending migrations sequentially."""
        current_version = self.get_current_version()
        files = self._get_migration_files()
        
        # Determine the target version based on the number of migration files available
        # Version 0 = empty db, Version 1 = 001_baseline.sql, Version 2 = 002_something.sql, etc.
        target_version = len(files)
        
        if current_version == target_version:
            logger.info(f"Database is up to date at version {current_version}.")
            return
            
        if current_version > target_version:
            raise MigrationError(f"Database version ({current_version}) is newer than available migrations ({target_version}). Downgrades are not supported automatically.")
            
        logger.info(f"Migrating database from version {current_version} to {target_version}.")
        
        for i in range(current_version, target_version):
            migration_file = files[i]
            target_file_version = i + 1
            
            logger.info(f"Applying migration: {migration_file.name} (Target version: {target_file_version})")
            
            try:
                script = migration_file.read_text(encoding="utf-8")
                
                # executescript implicitly commits the previous statement. 
                # To make PRAGMA version update part of it safely or pseudo-safely:
                self.conn.executescript(script)
                self.set_version(target_file_version)
                self.conn.commit()
                
                logger.info(f"Successfully applied {migration_file.name}")
            except Exception as e:
                logger.error(f"Migration failed on {migration_file.name}: {e}")
                raise MigrationError(f"Failed to apply migration {migration_file.name}: {e}") from e
                
        logger.info("All migrations completed successfully.")
