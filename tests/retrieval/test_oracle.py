import pytest
from aegis_py.retrieval.oracle import OracleBeast

def test_oracle_expansion_basics():
    oracle = OracleBeast()
    
    # Test phở bò expansion
    exp = oracle.expand_query("Tôi muốn ăn phở bò")
    assert "beef noodle soup" in exp or "phở bò" in exp
    assert "vietnamese food" in exp
    
    # Test sqlite expansion
    exp = oracle.expand_query("How to use sqlite fts5?")
    assert "database" in exp
    assert "relational storage" in exp
    
    # Test empty/short query
    assert oracle.expand_query("") == []
    assert oracle.expand_query("a") == []

def test_oracle_expansion_deduplication():
    oracle = OracleBeast()
    exp = oracle.expand_query("phở bò beef noodle soup")
    # Result should not contain the original query string
    assert "phở bò beef noodle soup" not in exp
    # Should contain related terms
    assert len(exp) > 0
    # Should be deduplicated
    assert len(exp) == len(set(exp))
