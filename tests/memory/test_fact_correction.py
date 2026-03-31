import pytest
import time
import json
from aegis_py.app import AegisApp

@pytest.fixture
def temp_app(tmp_path):
    db_file = tmp_path / "test_aegis_correction.db"
    app = AegisApp(str(db_file))
    yield app
    app.close()

def test_explicit_fact_correction_flow(temp_app):
    # 1. Ingest initial fact
    m1 = temp_app.put_memory("My phone number is 123-456.", subject="user.phone")
    assert m1 is not None
    
    # Wait a bit to ensure time difference
    time.sleep(0.1)
    
    # 2. Ingest correction
    # "corrected to" is a trigger in CorrectionDetector
    m2 = temp_app.put_memory("My phone number changed, it is corrected to 987-654.", subject="user.phone")
    assert m2 is not None
    
    # 3. Run maintenance to trigger Meerkat + Consolidator
    temp_app.maintenance()
    
    # 4. Verify results
    # m1 should be superseded
    row1 = temp_app.storage.fetch_one("SELECT status FROM memories WHERE id = ?", (m1.id,))
    assert row1["status"] == "superseded"
    
    # m2 should be active
    row2 = temp_app.storage.fetch_one("SELECT status, metadata_json FROM memories WHERE id = ?", (m2.id,))
    assert row2["status"] == "active"
    
    # metadata should have corrected_from
    meta = json.loads(row2["metadata_json"])
    assert m1.id in meta.get("corrected_from", [])
    
    # 5. Search should only return m2
    results = temp_app.search("phone number", scope_id="default", scope_type="session")
    assert len(results) == 1
    assert results[0].memory.id == m2.id
    assert "987-654" in results[0].memory.content

def test_vietnamese_fact_correction_flow(temp_app):
    # 1. Ingest initial fact
    m1 = temp_app.put_memory("Địa chỉ nhà tôi là 123 Đường Lê Lợi.", subject="user.address")
    
    time.sleep(0.1)
    
    # 2. Ingest correction in Vietnamese
    # "đã chuyển sang" is a trigger
    m2 = temp_app.put_memory("Địa chỉ nhà tôi đã chuyển sang 456 Đường Nguyễn Huệ.", subject="user.address")
    
    # 3. Run maintenance
    temp_app.maintenance()
    
    # 4. Verify
    row1 = temp_app.storage.fetch_one("SELECT status FROM memories WHERE id = ?", (m1.id,))
    assert row1["status"] == "superseded"
    
    results = temp_app.search("địa chỉ nhà", scope_id="default", scope_type="session")
    assert len(results) == 1
    assert "Nguyễn Huệ" in results[0].memory.content
