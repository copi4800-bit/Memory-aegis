from aegis_py.hygiene.bowerbird import BowerbirdBeast
from aegis_py.memory.classifier import LaneClassifier
from aegis_py.memory.extractor import ContentExtractor
from aegis_py.memory.ingest import IngestEngine
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.storage.manager import StorageManager


def test_dimetrodon_profile_separates_rich_structure():
    extractor = ContentExtractor()

    rich = extractor.derive_profile(
        "Backup policy: open dashboard, compare checksum 4812, verify archive size, and record the result before 02:15."
    )
    sparse = extractor.derive_profile("backup later")

    assert rich["dimetrodon_feature_separation"] > sparse["dimetrodon_feature_separation"]
    assert rich["keyword_count"] > sparse["keyword_count"]


def test_chalicotherium_profile_surfaces_lane_fit():
    classifier = LaneClassifier()
    profile = classifier.profile(
        content="How to rotate backup keys safely before release.",
        source_kind="manual",
    )

    assert profile["predicted_lane"] == "procedural"
    assert profile["chalicotherium_ecology_fit"] > 0.6


def test_ingest_diagnostic_surfaces_tranche4_profiles(tmp_path):
    storage = StorageManager(str(tmp_path / "prehistoric_tranche4.db"))
    try:
        engine = IngestEngine(storage, search_pipeline=SearchPipeline(storage))
        diagnostic = engine.diagnose_attempt(
            "How to rotate backup keys safely before release: open the key vault, export the current key, create a new key, and verify clients before cutover.",
            scope_type="agent",
            scope_id="prehistoric_tranche4",
            source_kind="manual",
            source_ref="test://prehistoric-tranche4",
        )

        assert diagnostic["lane_profile"]["predicted_lane"] == "procedural"
        assert diagnostic["lane_profile"]["chalicotherium_ecology_fit"] > 0.6
        assert diagnostic["extraction_profile"]["dimetrodon_feature_separation"] > 0.62
    finally:
        storage.close()


def test_candidate_reasons_include_dimetrodon_and_chalicotherium(tmp_path):
    storage = StorageManager(str(tmp_path / "prehistoric_tranche4_candidate.db"))
    try:
        engine = IngestEngine(storage, search_pipeline=SearchPipeline(storage))
        memory = engine.factory.create(
            type="procedural",
            content="How to rotate backup keys safely before release: open the key vault, export the current key, create a new key, and verify clients before cutover.",
            scope_type="agent",
            scope_id="prehistoric_tranche4",
            source_kind="manual",
            subject="backup.keys.rotation",
            summary="backup key rotation",
            metadata={
                "score_profile": engine.write_time_scorer.build_profile(
                    content="How to rotate backup keys safely before release: open the key vault, export the current key, create a new key, and verify clients before cutover.",
                    memory_type="procedural",
                    source_kind="manual",
                ),
                "lane_profile": engine.lane_classifier.profile(
                    content="How to rotate backup keys safely before release: open the key vault, export the current key, create a new key, and verify clients before cutover.",
                    source_kind="manual",
                ),
                "extraction_profile": engine.content_extractor.derive_profile(
                    "How to rotate backup keys safely before release: open the key vault, export the current key, create a new key, and verify clients before cutover."
                ),
                "subject_profile": {
                    "raw_subject": "backup.keys.rotation",
                    "canonical_subject": "backup.keys.rotation",
                    "ammonite_spiral_stability": 0.83,
                    "segment_count": 3,
                    "alnum_retention_ratio": 1.0,
                },
                "evidence": {"event_id": "evt_prehistoric_tranche4"},
            },
            confidence=0.97,
            activation_score=1.2,
        )
        candidate = engine.build_candidate(memory)

        assert "chalicotherium_lane_fit_high" in candidate.reasons
        assert "dimetrodon_feature_separation_strong" in candidate.reasons
    finally:
        storage.close()


def test_oviraptor_taxonomy_cleanup_uses_canonical_subjects(runtime_harness):
    runtime_harness.storage.execute(
        """
        INSERT INTO memories (
            id, type, scope_type, scope_id, content, subject, source_kind, status,
            confidence, activation_score, access_count, metadata_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 0.9, 1.0, 0, '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        ("ov_subject_raw", "semantic", "agent", "prehistoric_tranche4", "Customer record", "Café CRM / Customer-ID #42", "manual"),
    )
    bowerbird = BowerbirdBeast(runtime_harness.storage)

    report = bowerbird.normalize_subjects()
    normalized = runtime_harness.storage.fetch_one(
        "SELECT subject FROM memories WHERE id = ?",
        ("ov_subject_raw",),
    )

    assert normalized["subject"] == "cafe.crm.customer.id.42"
    assert report["normalized_count"] >= 1
    assert report["oviraptor_taxonomy_order"] > 0.4

