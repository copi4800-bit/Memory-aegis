import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from aegis_py.ops.migration import MigrationManager, MigrationError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

def test_migration_manager_initial_version(db_conn, temp_dir):
    manager = MigrationManager(db_conn, temp_dir)
    assert manager.get_current_version() == 0

def test_run_migrations_from_scratch(db_conn, temp_dir):
    # Create two migration files
    mig_dir = Path(temp_dir)
    
    (mig_dir / "001_baseline.sql").write_text("CREATE TABLE test1 (id INTEGER PRIMARY KEY);")
    (mig_dir / "002_add_column.sql").write_text("ALTER TABLE test1 ADD COLUMN name TEXT;")
    
    manager = MigrationManager(db_conn, temp_dir)
    manager.run_migrations()
    
    assert manager.get_current_version() == 2
    
    # Verify schema changes
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA table_info(test1)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "id" in columns
    assert "name" in columns

def test_incremental_migration(db_conn, temp_dir):
    mig_dir = Path(temp_dir)
    (mig_dir / "001_baseline.sql").write_text("CREATE TABLE test1 (id INTEGER PRIMARY KEY);")
    
    # Run first migration
    manager1 = MigrationManager(db_conn, temp_dir)
    manager1.run_migrations()
    assert manager1.get_current_version() == 1
    
    # Add second migration later
    (mig_dir / "002_add_column.sql").write_text("ALTER TABLE test1 ADD COLUMN name TEXT;")
    
    manager2 = MigrationManager(db_conn, temp_dir)
    manager2.run_migrations()
    assert manager2.get_current_version() == 2

def test_migration_failure_rolls_back(db_conn, temp_dir):
    mig_dir = Path(temp_dir)
    (mig_dir / "001_baseline.sql").write_text("CREATE TABLE test1 (id INTEGER PRIMARY KEY);")
    # Intentional syntax error in 002
    (mig_dir / "002_bad.sql").write_text("ALTER TABLE test1 ADD COLUMN name TEXT; INVALID SQL SYNTAX;")
    
    manager = MigrationManager(db_conn, temp_dir)
    
    with pytest.raises(MigrationError):
        manager.run_migrations()
        
    # Version should still be 1 because 001 succeeded, but 002 failed before bumping version.
    assert manager.get_current_version() == 1