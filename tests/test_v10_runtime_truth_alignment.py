from aegis_py.storage.models import Memory
from aegis_py.retrieval.models import SearchQuery

def test_v10_runtime_truth_alignment(runtime_harness):
    storage = runtime_harness.storage
    pipeline = runtime_harness.pipeline
    
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
    runtime_harness.put(old_mem)
    old_id = old_mem.id

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
        scope_id="default",
        metadata={"is_winner": True, "is_correction": True, "corrected_from": ["old_mem"]},
    )
    runtime_harness.put(new_mem)
    new_id = new_mem.id
    runtime_harness.sync_fts()
    
    # Explicitly mark superseded for the test scenario
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (old_id,))
    storage.execute("UPDATE memories SET status = 'active' WHERE id = ?", (new_id,))
    
    # DEBUG: Check state
    print("\n--- DEBUG: DB STATE ---")
    rows = storage.fetch_all("SELECT m.id, m.content, m.status, (SELECT rowid FROM memories_fts WHERE memories_fts.rowid = m.rowid) as fts_rowid FROM memories m")
    for r in rows:
        print(f"ID: {r['id']}, Status: {r['status']}, FTS_RowID: {r['fts_rowid']}, Content: {r['content'][:30]}")
    
    # 3. Perform real search
    query = SearchQuery(query="prefer red", scope_type="agent", scope_id="default", min_score=-10.0)
    results = pipeline.search(query)
    
    print(f"--- Aegis v10 Runtime Integration Test ---")
    print(f"Query: {query.query}")
    print(f"Top Result: {results[0].memory.content}")
    from aegis_py.surface import serialize_search_result
    serialized = serialize_search_result(results[0])
    
    print(f"Top Result Score: {results[0].v10_score:.4f}")
    print(f"Top Result Human Reason: {serialized['human_reason']}")
    
    # Assertions
    assert results[0].memory.id == new_id, "v10 Runtime should have ranked the New Memory (Truth Winner) as #1"
    assert serialized["v10_governance"]["governance_status"] == "active"
    assert "đã được cập nhật và xác nhận là sự thật mới nhất" in serialized["human_reason"], "Explanation should reflect current v10 correction wording"
    
    print("✅ test_v10_runtime_truth_alignment passed!")

if __name__ == "__main__":
    test_v10_runtime_truth_alignment()
