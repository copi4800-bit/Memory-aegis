import pytest
from datetime import datetime
from aegis_py.storage.manager import StorageManager
from aegis_py.preferences.extractor import SignalExtractor
from aegis_py.preferences.manager import PreferenceManager

@pytest.fixture
def pref_env(tmp_path):
    db_file = tmp_path / "test_aegis_pref.db"
    storage = StorageManager(str(db_file))
    extractor = SignalExtractor()
    manager = PreferenceManager(storage)
    return storage, extractor, manager

def test_signal_extraction(pref_env):
    storage, extractor, manager = pref_env
    
    # Terse + JSON
    signals = extractor.extract_signals("ok. ```json {} ```", "S1", "P1", "project")
    
    keys = [s.signal_key for s in signals]
    assert "verbosity" in keys
    assert "preferred_format" in keys
    
    # Verbosity should be low (0.1)
    v_sig = next(s for s in signals if s.signal_key == "verbosity")
    assert v_sig.signal_value == 0.1

def test_profile_consolidation(pref_env):
    storage, extractor, manager = pref_env
    
    # 1. Simulate multiple signals in a session
    s1 = extractor.extract_signals("How do I fix this bug?", "S1", "P1", "project")
    s2 = extractor.extract_signals("```json {'fix': true} ```", "S1", "P1", "project")
    
    for s in s1 + s2:
        storage.put_signal(s)
        
    # 2. Consolidate
    manager.consolidate_session("S1", "P1", "project")
    
    # 3. Verify Profile
    profile = storage.get_profile("P1", "project")
    assert profile is not None
    assert profile.preferences_json["preferred_format"] == "json"
    # Technical level should be 0.65 (weighted mix: 0.5*0.7 + 1.0*0.3)
    assert profile.preferences_json["technical_level"] == 0.65
    
    # 4. Verify signals were cleaned up
    with storage._get_connection() as conn:
        count = conn.execute("SELECT count(*) FROM style_signals WHERE session_id = 'S1'").fetchone()[0]
        assert count == 0

def test_profile_inheritance(pref_env):
    storage, extractor, manager = pref_env
    
    # Check that a non-existent profile returns None (manager will handle global later)
    prof = storage.get_profile("NONEXISTENT", "project")
    assert prof is None
