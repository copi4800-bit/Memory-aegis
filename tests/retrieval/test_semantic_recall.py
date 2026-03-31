import pytest
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.ingest import IngestEngine
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.retrieval.models import SearchQuery

@pytest.fixture
def temp_engine(tmp_path):
    db_file = tmp_path / "test_aegis_semantic.db"
    storage = StorageManager(str(db_file))
    engine = IngestEngine(storage)
    return storage, engine

def test_semantic_recall_foundational(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    
    # Ingest a memory with specific wording
    engine.ingest("Tôi rất thích ăn phở bò.", scope_id="food", scope_type="session")
    
    # Query with semantic expansion enabled, using a synonym with NO lexical overlap
    # "Vietnamese beef noodle soup" has no words in common with "Tôi rất thích ăn phở bò."
    query = SearchQuery(
        query="I enjoy Vietnamese beef noodle soup",
        scope_id="food",
        scope_type="session",
        semantic=True
    )
    
    results = pipeline.search_with_expansion(query)
    
    assert len(results) > 0
    assert "phở bò" in results[0].memory.content
    assert results[0].retrieval_stage == "semantic_recall"
    assert any("semantic_oracle_expansion" in reason for reason in results[0].reasons)

def test_semantic_recall_optional_toggle(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    
    engine.ingest("Tôi rất thích ăn phở bò.", scope_id="food", scope_type="session")
    
    # Query with semantic=False
    query_off = SearchQuery(
        query="beef noodle soup",
        scope_id="food",
        scope_type="session",
        semantic=False
    )
    results_off = pipeline.search_with_expansion(query_off)
    # Should be empty because no lexical overlap and semantic is off
    assert len(results_off) == 0
    
    # Query with semantic=True
    query_on = SearchQuery(
        query="beef noodle soup",
        scope_id="food",
        scope_type="session",
        semantic=True
    )
    results_on = pipeline.search_with_expansion(query_on)
    assert len(results_on) > 0
    assert results_on[0].retrieval_stage == "semantic_recall"

def test_semantic_recall_blending(temp_engine):
    storage, engine = temp_engine
    pipeline = SearchPipeline(storage)
    
    # Exact match
    engine.ingest("The user loves beef noodle soup", scope_id="test")
    # Semantic match
    engine.ingest("Tôi thích phở bò", scope_id="test")
    
    query = SearchQuery(
        query="beef noodle soup",
        scope_id="test",
        semantic=True
    )
    results = pipeline.search_with_expansion(query)
    
    assert len(results) >= 2
    # Lexical match should usually be first due to higher score/certainty
    assert results[0].retrieval_stage == "lexical"
    assert results[1].retrieval_stage == "semantic_recall"
