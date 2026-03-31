import pytest
import sqlite3
import uuid

from aegis_py.replication.conflict import ConflictDetector

def test_detect_conflict_new_entity():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE memories (id TEXT, origin_node_id TEXT)")
    
    detector = ConflictDetector(conn)
    
    is_conflict, local_origin = detector.detect_conflict("memory", "123", "remote-A")
    assert is_conflict is False
    assert local_origin is None

def test_detect_conflict_same_origin():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE memories (id TEXT, origin_node_id TEXT)")
    conn.execute("INSERT INTO memories (id, origin_node_id) VALUES ('123', 'remote-A')")
    conn.commit()
    
    detector = ConflictDetector(conn)
    
    is_conflict, local_origin = detector.detect_conflict("memory", "123", "remote-A")
    assert is_conflict is False
    assert local_origin is None

def test_detect_conflict_different_origin():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE memories (id TEXT, origin_node_id TEXT)")
    conn.execute("INSERT INTO memories (id, origin_node_id) VALUES ('123', 'local-node-1')")
    conn.commit()
    
    detector = ConflictDetector(conn)
    
    is_conflict, local_origin = detector.detect_conflict("memory", "123", "remote-A")
    assert is_conflict is True
    assert local_origin == "local-node-1"
