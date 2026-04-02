from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory
from aegis_py.surface import serialize_search_result

def test_v10_full_path_integration(runtime_harness):
    """
    Scenario: User corrects an old fact. v10 must rank the new one #1 
    with a 'correction winner' explanation.
    """
    storage = runtime_harness.storage
    manager = runtime_harness.manager
    pipeline = runtime_harness.pipeline
    
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
        scope_id="default",
        metadata={"is_winner": True, "is_correction": True, "corrected_from": ["old_fact"]},
    )
    manager.store(new_mem)
    
    # Simulate a real system where old one is marked superseded
    storage.execute("UPDATE memories SET status = 'superseded' WHERE id = 'old_fact'")
    runtime_harness.sync_fts()
    
    # 3. Search
    # We use a lower min_score just to ensure we see the candidates in the pool
    # BM25 scores can be negative on very small databases.
    query = SearchQuery(query="CEO", scope_type="agent", scope_id="default", min_score=-10.0)
    results = pipeline.search(query)
    
    print(f"\n--- v10 Full Path Integration Test ---")
    print(f"Results: {len(results)}")
    
    assert len(results) > 0, "Should find at least the new fact"
    top_result = results[0]
    
    serialized = serialize_search_result(top_result)
    print(f"Top Result ID: {top_result.memory.id}")
    print(f"Top Result Content: {top_result.memory.content}")
    print(f"Human Reason: {serialized['human_reason']}")
    
    # Assertions
    assert top_result.memory.id == "new_fact", "v10 should rank the new fact first"
    assert serialized["v10_governance"]["governance_status"] == "active"
    assert "đã được cập nhật và xác nhận là sự thật mới nhất" in serialized["human_reason"]
    assert any(candidate["id"] == "old_fact" for candidate in top_result.suppressed_candidates)
    print("✅ test_v10_full_path_integration passed!")

if __name__ == "__main__":
    test_v10_full_path_integration()
