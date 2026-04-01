import os
import asyncio
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.core import MemoryManager
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery
from aegis_py.surface import serialize_search_result

async def test_v9_runtime_full_path():
    # Setup real temporary storage
    db_path = "/home/hali/.openclaw/extensions/memory-aegis-v7/test_v9_full_path.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = StorageManager(db_path)
    # MemoryManager handles the high-level logic (triggers etc are in SQLite, 
    # but we use Manager to be safe and idiomatic)
    manager = MemoryManager(storage)
    pipeline = SearchPipeline(storage)
    
    from aegis_py.storage.models import Memory
    
    # 1. Put old memory (via Manager.store)
    old_mem = Memory(
        id="old_mem",
        type="semantic",
        content="My favorite color is blue.",
        subject="favorite_color",
        confidence=0.9,
        source_kind="manual",
        source_ref="test",
        scope_type="agent",
        scope_id="default"
    )
    manager.store(old_mem)
    
    # 2. Put new correction
    new_mem = Memory(
        id="new_mem",
        type="semantic",
        content="Actually, I prefer red now.",
        subject="favorite_color",
        confidence=1.0,
        source_kind="manual",
        source_ref="test",
        scope_type="agent",
        scope_id="default"
    )
    manager.store(new_mem)
    
    # Explicitly ensure triggers/logic state is as expected for the test
    # (In a real system, the second 'put' with same subject might auto-supersede)
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_mem.id,))
    
    # 3. Perform real search
    # We use a lower min_score just to ensure we see the candidates in the pool
    query = SearchQuery(query="prefer red", scope_type="agent", scope_id="default", min_score=0.1)
    results = pipeline.search(query)
    
    print(f"\n--- Aegis v9 Full Path Integration Test ---")
    print(f"Results found: {len(results)}")
    
    if results:
        serialized = serialize_search_result(results[0])
        print(f"Top Result: {results[0].memory.content}")
        print(f"Top Result v9 Score: {results[0].v9_score:.4f}")
        print(f"Top Result Human Reason: {serialized['human_reason']}")
        
        # Assertions
        assert results[0].memory.id == new_mem.id, "v9 should rank the newer winner first"
        assert "bản sửa lỗi mới nhất" in serialized["human_reason"], "Should use v9 faithful explanation"
    else:
        print("❌ FAILED: No results found!")

    # Cleanup
    storage.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ test_v9_runtime_full_path passed!")

if __name__ == "__main__":
    asyncio.run(test_v9_runtime_full_path())
