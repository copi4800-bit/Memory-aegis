from datetime import datetime, timezone

from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory
from aegis_py.v10.models import TruthRole

def test_v10_shadow_governance(runtime_harness):
    """
    Scenario: Multiple contenders for the same slot.
    v10 must identify exactly one Winner and others as Contenders.
    """
    storage = runtime_harness.storage
    manager = runtime_harness.manager
    pipeline = runtime_harness.pipeline
    
    # 1. Setup a Fact Slot with 2 active contenders
    # Contender 1 (Lower confidence)
    m1 = Memory(
        id="c1", type="semantic", content="The company office is located in Hanoi since 2010.", subject="office_loc",
        confidence=0.7, source_kind="manual", source_ref="m1", scope_type="agent", scope_id="main"
    )
    # Contender 2 (Higher confidence - should be Winner)
    m2 = Memory(
        id="c2", type="semantic", content="The company office has moved to Saigon recently.", subject="office_loc",
        confidence=0.9, source_kind="manual", source_ref="m2", scope_type="agent", scope_id="main",
        metadata={"is_winner": True}
    )
    
    manager.store(m1)
    manager.store(m2)
    
    # Add Evidence to c2 to boost its margin above 0.2
    now = datetime.now(timezone.utc).isoformat()
    for i in range(5):
        storage.execute("INSERT INTO evidence_events (id, scope_type, scope_id, memory_id, source_kind, source_ref, raw_content, created_at) VALUES (?, 'agent', 'main', 'c2', 'manual', 'm2', 'Confirmed', ?)", (f"ev_{i}", now))
    
    # Triggers should handle FTS sync automatically, but if they don't, we force it for the test
    # In some SQLite versions, rowid might not match if AUTOINCREMENT is used or if deletions occurred.
    # But for a fresh DB, rowid 1 and 2 should match c1 and c2.
    runtime_harness.sync_fts()
    
    # 2. Perform Search
    # We use 'company' to ensure we match both records
    query_text = "company"
    fts_test = storage.fetch_all("SELECT rowid, rank FROM memories_fts(?)", (query_text,))
    print(f"DEBUG: Manual FTS check for '{query_text}': {[dict(r) for r in fts_test]}")
    
    query = SearchQuery(query=query_text, scope_type="agent", scope_id="main", min_score=-10.0)
    setattr(query, "intent", "correction_lookup") # Force winner selection in v10 TruthRegistry
    results = pipeline.search(query)
    
    print(f"\n--- Aegis v10 Shadow Governance Test ---")
    print(f"Results found: {len(results)}")
    if len(results) == 0:
        # Check if FTS even works
        fts_rows = storage.fetch_all("SELECT rowid, content FROM memories_fts")
        print(f"DEBUG: FTS content: {[dict(r) for r in fts_rows]}")
        mem_rows = storage.fetch_all("SELECT rowid, id, content FROM memories")
        print(f"DEBUG: Memory rows: {[dict(r) for r in mem_rows]}")
    
    for r in results:
        dec = r.v10_decision
        print(f"ID: {r.memory.id} | v10 Score: {r.v10_score:.2f} | v10 Role: {dec.truth_role.value} | v10 Status: {dec.governance_status.value}")
        print(f"   Reasons: {dec.decision_reason}")

    # 3. Assertions
    # Current runtime returns the admitted winner and suppresses lower-ranked contenders.
    assert len(results) == 1, "Current governed runtime should surface only the admitted winner"
    top_res = results[0]
    assert top_res.v10_decision.truth_role == TruthRole.WINNER
    assert top_res.memory.id == "c2"
    assert any(candidate["id"] == "c1" for candidate in top_res.suppressed_candidates)
    print("✅ test_v10_shadow_governance passed!")

if __name__ == "__main__":
    test_v10_shadow_governance()
