import pytest
from aegis_py.app import AegisApp

@pytest.fixture
def temp_app(tmp_path):
    db_file = tmp_path / "test_aegis_dedupe.db"
    app = AegisApp(str(db_file))
    yield app
    app.close()

def test_semantic_deduplication_on_ingest(temp_app):
    # 1. Ingest first memory
    temp_app.put_memory("Tôi rất thích ăn phở bò.", subject="food.vietnamese")
    
    # 2. Ingest semantically similar memory
    # "Beef noodle soup is my favorite" is similar to "Tôi rất thích ăn phở bò" via Oracle expansion
    # IngestEngine should detect this and reinforce instead of creating new
    result = temp_app.put_memory("Beef noodle soup is my favorite.", subject="food.vietnamese")
    
    # 3. Verify only one memory exists for this subject
    memories = temp_app.storage.fetch_all(
        "SELECT id, content, access_count FROM memories WHERE subject = 'food.vietnamese' AND status = 'active'"
    )
    
    # Should be 1 because the second one was deduped
    assert len(memories) == 1
    # Access count should be at least 2 (initial + dedupe reinforcement)
    assert memories[0]["access_count"] >= 2

def test_librarian_maintenance_consolidation(temp_app):
    # 1. Manually insert two similar memories without dedupe check
    # (by disabling search_pipeline temporarily in ingest_engine)
    temp_app.ingest_engine.search_pipeline = None
    
    m1 = temp_app.put_memory("I love coding in Python.", subject="tech.python")
    m2 = temp_app.put_memory("Python programming is fun.", subject="tech.python")
    
    # Verify two active memories exist
    active_before = temp_app.storage.fetch_all(
        "SELECT id FROM memories WHERE subject = 'tech.python' AND status = 'active'"
    )
    assert len(active_before) == 2
    
    # 2. Re-enable search_pipeline and run maintenance
    temp_app.ingest_engine.search_pipeline = temp_app.search_pipeline
    temp_app.maintenance()
    
    # 3. Verify they were consolidated
    active_after = temp_app.storage.fetch_all(
        "SELECT id, metadata_json FROM memories WHERE subject = 'tech.python' AND status = 'active'"
    )
    assert len(active_after) == 1
    
    # Check superseded status
    superseded = temp_app.storage.fetch_all(
        "SELECT id FROM memories WHERE subject = 'tech.python' AND status = 'superseded'"
    )
    assert len(superseded) == 1
    
    # Verify merge trace in metadata
    import json
    metadata = json.loads(active_after[0]["metadata_json"])
    merged_ids = metadata.get("merged_from", [])
    
    # Master can be m1 or m2, but the other one must be in merged_from
    assert (m1.id in merged_ids) or (m2.id in merged_ids)
