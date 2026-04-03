from aegis_py.memory.ingest import IngestEngine
from aegis_py.memory.scorer import WriteTimeScorer
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.storage.manager import StorageManager


def test_dunkleosteus_and_thylacoleo_profiles_are_exposed():
    scorer = WriteTimeScorer()

    decisive = scorer.build_profile(
        content="Set the production database backup schedule to 02:00 every day and always verify the archive checksum.",
        memory_type="procedural",
        source_kind="manual",
    )
    cautious = scorer.build_profile(
        content="Maybe the backup is not always at 02:00.",
        memory_type="semantic",
        source_kind="message",
    )

    assert decisive["dunkleosteus_decisive_pressure"] > cautious["dunkleosteus_decisive_pressure"]
    assert cautious["thylacoleo_conflict_sentinel_score"] > decisive["thylacoleo_conflict_sentinel_score"]


def test_ingest_engine_diagnose_attempt_exposes_prehistoric_signals(tmp_path):
    storage = StorageManager(str(tmp_path / "prehistoric_phase_a.db"))
    try:
        engine = IngestEngine(storage, search_pipeline=SearchPipeline(storage))
        diagnostic = engine.diagnose_attempt(
            "Maybe the backup is not always at 02:00.",
            type="semantic",
            scope_type="agent",
            scope_id="prehistoric_scope",
            source_kind="message",
            source_ref="test://prehistoric-phase-a",
            subject="backup.schedule",
        )

        profile = diagnostic["score_profile"]
        assert "dunkleosteus_decisive_pressure" in profile
        assert "thylacoleo_conflict_sentinel_score" in profile
        assert profile["thylacoleo_conflict_sentinel_score"] > 0.2
    finally:
        storage.close()


def test_ingest_engine_candidate_reasons_include_thylacoleo_signal(tmp_path):
    storage = StorageManager(str(tmp_path / "prehistoric_phase_a_candidate.db"))
    try:
        engine = IngestEngine(storage, search_pipeline=SearchPipeline(storage))
        memory = engine.factory.create(
            type="semantic",
            content="Maybe the backup is not always at 02:00.",
            scope_type="agent",
            scope_id="prehistoric_scope",
            source_kind="message",
            subject="backup.schedule",
            summary="backup schedule uncertainty",
            metadata={
                "score_profile": engine.write_time_scorer.build_profile(
                    content="Maybe the backup is not always at 02:00.",
                    memory_type="semantic",
                    source_kind="message",
                ),
                "evidence": {"event_id": "evt_prehistoric"},
            },
            confidence=0.7,
            activation_score=1.0,
        )
        candidate = engine.build_candidate(memory)

        assert "thylacoleo_conflict_sentinel_elevated" in candidate.reasons
    finally:
        storage.close()
