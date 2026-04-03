from aegis_py.memory.ingest import IngestEngine
from aegis_py.memory.normalizer import SubjectNormalizer
from aegis_py.memory.scorer import WriteTimeScorer


def test_meganeura_capture_span_rewards_richer_ingest_signal():
    scorer = WriteTimeScorer()

    broad = scorer.build_profile(
        content="At 02:00 every weekday, open the backup dashboard, verify checksum 4812, compare the archive size, and write the outcome to the recovery log before 02:15.",
        memory_type="procedural",
        source_kind="manual",
    )
    narrow = scorer.build_profile(
        content="Backup maybe later.",
        memory_type="semantic",
        source_kind="message",
    )

    assert broad["meganeura_capture_span"] > narrow["meganeura_capture_span"]


def test_ammonite_subject_profile_canonicalizes_and_scores_stability():
    normalizer = SubjectNormalizer()

    profile = normalizer.profile("Café CRM / Customer-ID #42")

    assert profile.canonical_subject == "cafe.crm.customer.id.42"
    assert profile.segment_count >= 4
    assert profile.ammonite_spiral_stability > 0.72


def test_ingest_diagnostic_exposes_meganeura_and_ammonite(runtime_harness):
    engine = IngestEngine(runtime_harness.storage, search_pipeline=runtime_harness.pipeline)

    diagnostic = engine.diagnose_attempt(
        "At 02:00 every weekday, open the backup dashboard, verify checksum 4812, compare the archive size, and write the outcome to the recovery log before 02:15.",
        type="procedural",
        scope_type="agent",
        scope_id="prehistoric_tranche2",
        source_kind="manual",
        source_ref="test://prehistoric-tranche2",
        subject="Café CRM / Customer-ID #42",
    )

    assert diagnostic["score_profile"]["meganeura_capture_span"] > 0.62
    assert diagnostic["subject_profile"]["canonical_subject"] == "cafe.crm.customer.id.42"
    assert diagnostic["subject_profile"]["ammonite_spiral_stability"] > 0.72


def test_candidate_reasons_and_spotlight_trace_surface_tranche2_signals(runtime_harness):
    engine = IngestEngine(runtime_harness.storage, search_pipeline=runtime_harness.pipeline)
    memory = engine.factory.create(
        type="procedural",
        content="At 02:00 every weekday, open the backup dashboard, verify checksum 4812, compare the archive size, and write the outcome to the recovery log before 02:15.",
        scope_type="agent",
        scope_id="prehistoric_tranche2",
        source_kind="manual",
        subject="Café CRM / Customer-ID #42",
        summary="backup verification routine",
        metadata={
            "score_profile": engine.write_time_scorer.build_profile(
                content="At 02:00 every weekday, open the backup dashboard, verify checksum 4812, compare the archive size, and write the outcome to the recovery log before 02:15.",
                memory_type="procedural",
                source_kind="manual",
            ),
            "subject_profile": {
                "raw_subject": "Café CRM / Customer-ID #42",
                "canonical_subject": "cafe.crm.customer.id.42",
                "ammonite_spiral_stability": 0.81,
                "segment_count": 5,
                "alnum_retention_ratio": 1.0,
            },
            "evidence": {"event_id": "evt_prehistoric_tranche2"},
        },
        confidence=0.95,
        activation_score=1.18,
    )
    candidate = engine.build_candidate(memory)

    assert "meganeura_capture_span_broad" in candidate.reasons
    assert "ammonite_spiral_stability_strong" in candidate.reasons
