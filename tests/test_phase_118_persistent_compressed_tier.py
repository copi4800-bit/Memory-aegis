import json

from aegis_py.app import AegisApp
from aegis_py.retrieval.compressed_prefilter import CompressedCandidatePrefilter
from aegis_py.retrieval.compressed_tier import build_compressed_tier_payload
from aegis_py.retrieval.engine import _run_compressed_candidate_stage
from aegis_py.storage.models import Memory


def test_ingest_persists_compressed_tier_metadata(tmp_path):
    app = AegisApp(str(tmp_path / "phase118_ingest.db"))
    try:
        stored = app.put_memory(
            "Harbor owner keeps the release ledger.",
            type="semantic",
            scope_type="agent",
            scope_id="phase118_scope",
            source_kind="manual",
            source_ref="test://phase118-ingest",
            subject="harbor.owner",
            confidence=0.95,
            metadata={"is_winner": True},
        )
        row = app.storage.fetch_one("SELECT metadata_json FROM memories WHERE id = ?", (stored.id,))
        metadata = json.loads(row["metadata_json"])
        compressed = metadata["compressed_tier"]
        assert compressed["tier"] == "hot"
        assert compressed["lexical_mask"]
        assert compressed["semantic_mask"] is not None
    finally:
        app.close()


def test_rebuild_backfills_missing_compressed_tier_and_surfaces_coverage(tmp_path):
    app = AegisApp(str(tmp_path / "phase118_rebuild.db"))
    try:
        app.storage.put_memory(
            Memory(
                id="phase118_legacy",
                type="semantic",
                scope_type="agent",
                scope_id="phase118_scope",
                content="Legacy memory without compressed tier.",
                source_kind="manual",
                source_ref="test://phase118-legacy",
                subject="legacy.memory",
                confidence=0.8,
                activation_score=0.7,
                metadata={},
            )
        )
        result = app.rebuild()
        row = app.storage.fetch_one("SELECT metadata_json FROM memories WHERE id = 'phase118_legacy'")
        metadata = json.loads(row["metadata_json"])
        footprint = app.storage_footprint(scope_type="agent", scope_id="phase118_scope")

        assert result["compressed_tier_backfilled"] >= 1
        assert "compressed_tier" in metadata
        assert footprint["compressed_tier"]["covered_memories"] >= 1
        assert footprint["compressed_tier"]["coverage_rate"] > 0.0
    finally:
        app.close()


def test_compressed_candidate_stage_reuses_persisted_signature(tmp_path, monkeypatch):
    app = AegisApp(str(tmp_path / "phase118_prefilter.db"))
    try:
        metadata = {
            "compressed_tier": build_compressed_tier_payload(
                content="Persistent harbor roster memory.",
                summary="Persistent harbor roster memory.",
                subject="harbor.roster",
                status="active",
                activation_score=0.9,
                metadata={},
            )
        }
        app.storage.put_memory(
            Memory(
                id="phase118_persisted",
                type="semantic",
                scope_type="agent",
                scope_id="phase118_scope",
                content="Persistent harbor roster memory.",
                summary="Persistent harbor roster memory.",
                source_kind="manual",
                source_ref="test://phase118-persisted",
                subject="harbor.roster",
                confidence=0.9,
                activation_score=0.9,
                metadata=metadata,
            )
        )

        prefilter = CompressedCandidatePrefilter()
        query_signature = prefilter.build_signature("harbor roster persistent", semantic_terms=[])

        original_build = prefilter.build_signature

        def guarded_build(text, *, semantic_terms=None):
            if "Persistent harbor roster memory." in text:
                raise AssertionError("candidate signature should have been read from persisted metadata")
            return original_build(text, semantic_terms=semantic_terms)

        monkeypatch.setattr(prefilter, "build_signature", guarded_build)

        compressed = _run_compressed_candidate_stage(
            app.storage,
            query="harbor roster persistent",
            query_signature=query_signature,
            scope_type="agent",
            scope_id="phase118_scope",
            limit=10,
            exclude_ids=set(),
            include_global=False,
            prefilter=prefilter,
        )

        surfaced = next(item for item in compressed if item["id"] == "phase118_persisted")
        assert surfaced["compressed_prefilter_score"] > 0.0
    finally:
        app.close()
