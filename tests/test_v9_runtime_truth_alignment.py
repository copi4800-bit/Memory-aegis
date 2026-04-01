import os
import asyncio
from datetime import datetime
from aegis_py.storage.manager import StorageManager
from aegis_py.storage.models import Memory
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery

async def test_v9_runtime_truth_alignment():
    # Setup real temporary storage
    db_path = "/home/hali/.openclaw/extensions/memory-aegis-v7/test_v9_runtime.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = StorageManager(db_path)
    pipeline = SearchPipeline(storage)
    
    # 1. Put old memory (Active initially)
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
    storage.put_memory(old_mem)
    old_id = old_mem.id
    
    # Manually populate FTS if triggers didn't fire in test env
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)", (old_id, old_mem.content, old_mem.subject))
    
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
    storage.put_memory(new_mem)
    new_id = new_mem.id
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)", (new_id, new_mem.content, new_mem.subject))
    
    # Explicitly mark superseded for the test scenario
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_id,))
    storage.execute("UPDATE memories SET status = 'active' WHERE id = ?", (new_id,))
    
    # DEBUG: Check state
    print("\n--- DEBUG: DB STATE ---")
    rows = storage.fetch_all("SELECT m.id, m.content, m.status, (SELECT rowid FROM memories_fts WHERE memories_fts.rowid = m.rowid) as fts_rowid FROM memories m")
    for r in rows:
        print(f"ID: {r['id']}, Status: {r['status']}, FTS_RowID: {r['fts_rowid']}, Content: {r['content'][:30]}")
    
    # 3. Perform real search
    query = SearchQuery(query="prefer red", scope_type="agent", scope_id="default")
    results = pipeline.search(query)
    
    print(f"--- Aegis v9 Runtime Integration Test ---")
    print(f"Query: {query.query}")
    print(f"Top Result: {results[0].memory.content}")
    from aegis_py.surface import serialize_search_result
    serialized = serialize_search_result(results[0])
    
    print(f"Top Result Score: {results[0].v9_score:.4f}")
    print(f"Top Result Human Reason: {serialized['human_reason']}")
    
    # Assertions
    assert results[0].memory.id == new_id, "v9 Runtime should have ranked the New Memory (Truth Winner) as #1"
    assert "được xác nhận là sự thật hiện tại" in serialized["human_reason"], "Explanation should reflect v9 truth alignment"
    
    # Cleanup
    storage.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ test_v9_runtime_truth_alignment passed!")

if __name__ == "__main__":
    asyncio.run(test_v9_runtime_truth_alignment())
