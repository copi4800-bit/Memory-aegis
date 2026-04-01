import os
import asyncio
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.core import MemoryManager
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory
from aegis_py.surface import serialize_search_result

async def test_v9_full_path_integration():
    """
    Scenario: User corrects an old fact. v9 must rank the new one #1 
    with a 'correction winner' explanation.
    """
    db_path = "/home/hali/.openclaw/extensions/memory-aegis-v7/test_v9_full_path_gsd.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = StorageManager(db_path)
    manager = MemoryManager(storage)
    pipeline = SearchPipeline(storage)
    
    # 1. Store old fact
    old_mem = Memory(
        id="old_fact",
        type="semantic",
        content="The CEO of TechCorp is Alice.",
        subject="techcorp_ceo",
        confidence=0.9,
        source_kind="manual",
        source_ref="manual",
        scope_type="agent",
        scope_id="default"
    )
    manager.store(old_mem)
    
    # 2. Store new fact (Correction)
    new_mem = Memory(
        id="new_fact",
        type="semantic",
        content="Bob is now the CEO of TechCorp.",
        subject="techcorp_ceo",
        confidence=1.0,
        source_kind="manual",
        source_ref="manual",
        scope_type="agent",
        scope_id="default"
    )
    manager.store(new_mem)
    
    # Simulate a real system where old one is marked superseded
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = 'old_fact'")
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'old_fact'), 'The CEO of TechCorp is Alice.', 'techcorp_ceo')")
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'new_fact'), 'Bob is now the CEO of TechCorp.', 'techcorp_ceo')")
    
    # 3. Search
    # We use a lower min_score just to ensure we see the candidates in the pool
    # BM25 scores can be negative on very small databases.
    query = SearchQuery(query="CEO", scope_type="agent", scope_id="default", min_score=-10.0)
    results = pipeline.search(query)
    
    print(f"\n--- v9 Full Path Integration Test ---")
    print(f"Results: {len(results)}")
    
    assert len(results) > 0, "Should find at least the new fact"
    top_result = results[0]
    
    serialized = serialize_search_result(top_result)
    print(f"Top Result ID: {top_result.memory.id}")
    print(f"Top Result Content: {top_result.memory.content}")
    print(f"Decisive Factor: {serialized['v9_audit']['decisive_factor']}")
    print(f"Human Reason: {serialized['human_reason']}")
    
    # Assertions
    assert top_result.memory.id == "new_fact", "v9 should rank the new fact first"
    assert serialized["v9_audit"]["decisive_factor"] == "hard_constraint_winner", "Should identify as truth winner"
    assert "được xác nhận là sự thật hiện tại" in serialized["human_reason"]

    # Cleanup
    storage.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ test_v9_full_path_integration passed!")

if __name__ == "__main__":
    asyncio.run(test_v9_full_path_integration())
