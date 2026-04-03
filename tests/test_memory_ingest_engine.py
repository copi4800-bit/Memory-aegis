from aegis_py.memory.ingest import IngestEngine
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.storage.manager import StorageManager


def test_ingest_engine_diagnose_attempt_reports_policy_block(tmp_path):
    storage = StorageManager(str(tmp_path / "memory_engine_diag_block.db"))
    try:
        engine = IngestEngine(storage, search_pipeline=SearchPipeline(storage))
        diagnostic = engine.diagnose_attempt(
            "Repeated ingest payload 0 for memory engine pressure.",
            type="semantic",
            scope_type="agent",
            scope_id="diag_scope",
            source_kind="manual",
            source_ref="test://engine-diag-block",
            subject="ingest.engine",
            confidence=0.4,
            activation_score=1.0,
        )

        assert diagnostic["outcome"] == "policy_block"
        assert diagnostic["target_state"] == "draft"
        assert "blocked_low_confidence" in diagnostic["reasons"]
    finally:
        storage.close()


def test_ingest_engine_diagnose_attempt_reports_exact_dedup(tmp_path):
    storage = StorageManager(str(tmp_path / "memory_engine_diag_dedup.db"))
    try:
        engine = IngestEngine(storage, search_pipeline=SearchPipeline(storage))
        stored = engine.ingest(
            "The build color is blue.",
            type="semantic",
            scope_type="agent",
            scope_id="diag_scope",
            source_kind="manual",
            source_ref="test://engine-diag-dedup/original",
            subject="build.color",
            confidence=0.95,
            activation_score=1.0,
        )

        diagnostic = engine.diagnose_attempt(
            "The build color is blue.",
            type="semantic",
            scope_type="agent",
            scope_id="diag_scope",
            source_kind="manual",
            source_ref="test://engine-diag-dedup/repeat",
            subject="build.color",
            confidence=0.95,
            activation_score=1.0,
        )

        assert stored is not None
        assert diagnostic["outcome"] == "exact_dedup"
        assert diagnostic["reason_code"] == "exact_content_scope_match"
        assert diagnostic["exact_duplicate_id"] == stored.id
    finally:
        storage.close()
