import os
import asyncio
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.core import MemoryManager
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory
from aegis_py.v10.models import TruthRole, GovernanceStatus, RetrievableMode

async def test_v10_full_governance_gauntlet():
    """
    Scenario: Safety violations and high-severity conflicts.
    v10 must exclude or quarantine records based on the Constitution.
    """
    db_path = "/home/hali/.openclaw/extensions/memory-aegis-v7/test_v10_gauntlet.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    storage = StorageManager(db_path)
    manager = MemoryManager(storage)
    pipeline = SearchPipeline(storage)
    
    # 1. Setup Dangerous Memory (C0 Violation)
    m_danger = Memory(
        id="danger", type="semantic", content="This contains ILLEGAL_CONTENT.", subject="risk",
        confidence=1.0, source_kind="manual", scope_type="agent", scope_id="main"
    )
    # 2. Setup High Conflict Memory (C3 Quarantine)
    m_conflict = Memory(
        id="conflict_record", type="semantic", content="Conflict info", subject="dispute",
        confidence=0.9, source_kind="manual", scope_type="agent", scope_id="main"
    )
    m_other = Memory(
        id="other", type="semantic", content="Other info", subject="dispute",
        confidence=0.9, source_kind="manual", scope_type="agent", scope_id="main"
    )
    
    manager.store(m_danger)
    manager.store(m_conflict)
    manager.store(m_other)
    
    # Manually trigger conflict high severity
    storage.execute("INSERT INTO conflicts (id, subject_key, memory_a_id, memory_b_id, score, status, created_at) VALUES ('c1', 'dispute', 'conflict_record', 'other', 0.9, 'open', '2026-04-01')")
    
    # Fast FTS sync
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'danger'), ?, ?)", (m_danger.content, m_danger.subject))
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'conflict_record'), ?, ?)", (m_conflict.content, m_conflict.subject))
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'other'), ?, ?)", (m_other.content, m_other.subject))
    
    # 3. Perform Search
    query = SearchQuery(query="ILLEGAL Conflict", scope_type="agent", scope_id="main", min_score=-10.0)
    results = pipeline.search(query)
    
    print(f"\n--- Aegis v10 Full Governance Gauntlet ---")
    print(f"Results admitted for normal serving: {len(results)}")
    
    # Check suppression reasons
    # We expect results to be empty because both records should be blocked
    assert len(results) == 0, "Governance should have blocked all records"
    
    # Verify DB directly or check suppressed results (if available in the first result object)
    # In this gauntlet, they are suppressed entirely.
    
    # 4. User Override Test (C1 Supremacy)
    m_override = Memory(
        id="user_pref", type="semantic", content="Use my nickname: Hali.", subject="nickname",
        confidence=0.5, source_kind="manual", scope_type="agent", scope_id="main",
        metadata={"is_winner": True} # v10 C1 Policy requires this
    )
    manager.store(m_override)
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) VALUES ((SELECT rowid FROM memories WHERE id = 'user_pref'), ?, ?)", (m_override.content, m_override.subject))
    
    query_override = SearchQuery(query="nickname", scope_type="agent", scope_id="main", min_score=-10.0)
    setattr(query_override, "intent", "user_override_active") # Trigger C1
    
    results_override = pipeline.search(query_override)
    print(f"Results after User Override: {len(results_override)}")
    
    assert len(results_override) > 0
    assert results_override[0].v10_decision.governance_status == GovernanceStatus.ACTIVE
    assert "C1_USER_OVERRIDE_APPLIED" in results_override[0].v10_decision.policy_trace

    # Cleanup
    storage.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ test_v10_full_governance_gauntlet passed!")

if __name__ == "__main__":
    asyncio.run(test_v10_full_governance_gauntlet())
