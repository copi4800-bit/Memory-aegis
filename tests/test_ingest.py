import pytest
from pathlib import Path

from aegis_py.app import AegisApp
from aegis_py.storage.manager import StorageManager
from aegis_py.memory.ingest import IngestEngine

@pytest.fixture
def temp_storage(tmp_path):
    db_file = tmp_path / "test_aegis_ingest.db"
    return StorageManager(str(db_file))

def test_ingest_worthy(temp_storage):
    engine = IngestEngine(temp_storage)
    
    # Meaningful fact
    mem = engine.ingest("User prefers dark mode for all UI components.")
    assert mem is not None
    assert mem.content == "User prefers dark mode for all UI components."
    
    # Nonsense
    mem_noise = engine.ingest("ok")
    assert mem_noise is None

def test_ingest_deduplication(temp_storage):
    engine = IngestEngine(temp_storage)
    
    content = "The project is due on Friday."
    mem1 = engine.ingest(content)
    assert mem1 is not None
    
    # Duplicate ingestion
    mem2 = engine.ingest(content)
    assert mem2 is None  # Should be skipped

def test_ingest_types(temp_storage):
    engine = IngestEngine(temp_storage)
    
    mem = engine.ingest("Temp working memory", type="working")
    assert mem.type == "working"
    assert mem.expires_at is not None  # Working memory should have expiry


def test_ingest_rejects_low_confidence_candidate_but_keeps_evidence(temp_storage):
    engine = IngestEngine(temp_storage)

    mem = engine.ingest(
        "Borderline memory should not auto-promote.",
        type="episodic",
        scope_type="project",
        scope_id="PROMO1",
        source_kind="manual",
        confidence=0.59,
        activation_score=1.0,
    )

    assert mem is None
    coverage = temp_storage.summarize_evidence_coverage(scope_type="project", scope_id="PROMO1")
    assert coverage["memory_records"] == 0
    assert coverage["evidence_events"] == 1


def test_ingest_marks_negation_contradictions_for_review_but_keeps_promotion(temp_storage):
    engine = IngestEngine(temp_storage)

    first = engine.ingest(
        "The deployment gate is enabled.",
        type="semantic",
        scope_type="project",
        scope_id="PROMO2",
        source_kind="manual",
        subject="deploy.gate",
    )
    second = engine.ingest(
        "The deployment gate is not enabled.",
        type="semantic",
        scope_type="project",
        scope_id="PROMO2",
        source_kind="manual",
        subject="deploy.gate",
    )
    correction = engine.ingest(
        "Actually, the deployment gate changed to disabled mode.",
        type="semantic",
        scope_type="project",
        scope_id="PROMO2",
        source_kind="manual",
        subject="deploy.gate",
    )

    assert first is not None
    assert second is not None
    assert correction is not None
    persisted = temp_storage.get_memory(second.id)
    assert persisted is not None
    assert persisted.admission_state == "hypothesized"
    assert "review_contradiction_risk" in persisted.metadata["promotion"]["reasons"]


def test_app_initializes_with_plain_filename_db_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    app = AegisApp(db_path="local-smoke.db")
    app.put_memory("Plain filename DB paths should initialize cleanly.", scope_id="plain")
    app.close()

    assert Path("local-smoke.db").exists()
