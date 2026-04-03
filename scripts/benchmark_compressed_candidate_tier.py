#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from aegis_py.retrieval.compressed_prefilter import CompressedCandidatePrefilter
from aegis_py.retrieval.engine import _run_compressed_candidate_stage
from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory


def resolve_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here.parent.parent):
        if (candidate / "aegis_py" / "app.py").exists():
            return candidate
    raise RuntimeError("Unable to locate repo root.")


@dataclass
class CandidateTierResult:
    name: str
    compressed_candidate_found: bool
    governed_top1_preserved: bool
    compressed_count: int
    selected_id: str | None
    expected_top1: str | None
    persistent_coverage_preserved: bool = True
    rebuild_backfill_preserved: bool = True


def sync_fts(storage) -> None:
    storage.execute("DELETE FROM memories_fts")
    storage.execute("INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories")


def run_overlap_case(app) -> CandidateTierResult:
    winner = app.put_memory(
        content="Harbor operations owns the deployment roster and maintains the release checklist.",
        type="semantic",
        scope_type="agent",
        scope_id="compressed_bench_overlap",
        source_kind="manual",
        source_ref="bench://winner",
        subject="deploy.roster",
        confidence=0.98,
        metadata={"is_winner": True},
    )
    app.put_memory(
        content="Deployment roster handoff ledger lives with harbor operations.",
        type="semantic",
        scope_type="agent",
        scope_id="compressed_bench_overlap",
        source_kind="manual",
        source_ref="bench://candidate",
        subject="deploy.roster",
        confidence=0.91,
    )
    sync_fts(app.storage)

    prefilter = CompressedCandidatePrefilter()
    compressed = _run_compressed_candidate_stage(
        app.storage,
        query="deployment roster harbor checklist steward",
        query_signature=prefilter.build_signature("deployment roster harbor checklist steward", semantic_terms=[]),
        scope_type="agent",
        scope_id="compressed_bench_overlap",
        limit=10,
        exclude_ids=set(),
        include_global=False,
        prefilter=prefilter,
    )
    query = SearchQuery(
        query="deployment roster harbor checklist steward",
        scope_type="agent",
        scope_id="compressed_bench_overlap",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "normal_recall")
    setattr(query, "scoring_mode", "v10_primary")
    results = app.search_pipeline.search(query)
    top = results[0].memory.id if results else None
    return CandidateTierResult(
        name="overlap_candidate_yield",
        compressed_candidate_found=any(item["id"] != winner.id for item in compressed),
        governed_top1_preserved=top == winner.id,
        compressed_count=len(compressed),
        selected_id=top,
        expected_top1=winner.id if winner else None,
    )


def run_cold_archive_case(app) -> CandidateTierResult:
    winner = app.put_memory(
        content="The archive steward is Bao and the checksum sheet stays in cold storage.",
        type="semantic",
        scope_type="agent",
        scope_id="compressed_bench_cold",
        source_kind="manual",
        source_ref="bench://cold-winner",
        subject="archive.steward",
        confidence=0.97,
        metadata={"is_winner": True},
    )
    archive_peer = app.put_memory(
        content="Cold storage checksum ledger belongs to Bao archive steward.",
        type="semantic",
        scope_type="agent",
        scope_id="compressed_bench_cold",
        source_kind="manual",
        source_ref="bench://cold-peer",
        subject="archive.steward",
        confidence=0.72,
    )
    app.storage.execute(
        "UPDATE memories SET activation_score = 0.22, access_count = 0 WHERE id = ?",
        (archive_peer.id,),
    )
    sync_fts(app.storage)

    prefilter = CompressedCandidatePrefilter()
    compressed = _run_compressed_candidate_stage(
        app.storage,
        query="cold checksum steward bao",
        query_signature=prefilter.build_signature("cold checksum steward bao", semantic_terms=[]),
        scope_type="agent",
        scope_id="compressed_bench_cold",
        limit=10,
        exclude_ids=set(),
        include_global=False,
        prefilter=prefilter,
    )
    query = SearchQuery(
        query="archive steward",
        scope_type="agent",
        scope_id="compressed_bench_cold",
        include_global=False,
        min_score=-10.0,
    )
    setattr(query, "intent", "correction_lookup")
    setattr(query, "scoring_mode", "v10_primary")
    results = app.search_pipeline.search(query)
    top = results[0].memory.id if results else None
    return CandidateTierResult(
        name="cold_tier_candidate_yield",
        compressed_candidate_found=any(item["id"] == archive_peer.id for item in compressed),
        governed_top1_preserved=top == winner.id,
        compressed_count=len(compressed),
        selected_id=top,
        expected_top1=winner.id if winner else None,
    )


def run_persistent_coverage_case(app) -> CandidateTierResult:
    app.put_memory(
        content="Harbor manifest remains available through the compressed warm tier.",
        type="semantic",
        scope_type="agent",
        scope_id="compressed_bench_persistent",
        source_kind="manual",
        source_ref="bench://persistent-hot",
        subject="manifest.owner",
        confidence=0.95,
        metadata={"is_winner": True},
    )
    app.storage.put_memory(
        Memory(
            id="compressed_persistent_legacy",
            type="semantic",
            scope_type="agent",
            scope_id="compressed_bench_persistent",
            content="Legacy compressed tier row missing persisted metadata.",
            source_kind="manual",
            source_ref="bench://persistent-legacy",
            subject="manifest.owner",
            confidence=0.75,
            activation_score=0.31,
            metadata={},
        )
    )
    rebuild = app.rebuild()
    footprint = app.storage_footprint(scope_type="agent", scope_id="compressed_bench_persistent")
    coverage = footprint.get("compressed_tier", {})
    return CandidateTierResult(
        name="persistent_tier_coverage",
        compressed_candidate_found=True,
        governed_top1_preserved=True,
        compressed_count=int(coverage.get("covered_memories", 0) or 0),
        selected_id=None,
        expected_top1=None,
        persistent_coverage_preserved=float(coverage.get("coverage_rate", 0.0) or 0.0) >= 1.0,
        rebuild_backfill_preserved=int(rebuild.get("compressed_tier_backfilled", 0) or 0) >= 1,
    )


def main() -> int:
    repo_root = resolve_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from aegis_py.app import AegisApp

    with tempfile.TemporaryDirectory(prefix="truthkeep_compressed_bench_") as tmp:
        tmp_root = Path(tmp)
        results: list[CandidateTierResult] = []
        for name, runner in (
            ("overlap", run_overlap_case),
            ("cold", run_cold_archive_case),
            ("persistent", run_persistent_coverage_case),
        ):
            app = AegisApp(str(tmp_root / f"compressed_candidate_bench_{name}.db"))
            try:
                results.append(runner(app))
            finally:
                app.close()

    summary = {
        "scenario_count": len(results),
        "compressed_candidate_yield_rate": round(sum(1 for item in results if item.compressed_candidate_found) / len(results), 3),
        "governed_top1_preservation_rate": round(sum(1 for item in results if item.governed_top1_preserved) / len(results), 3),
        "persistent_coverage_rate": round(sum(1 for item in results if item.persistent_coverage_preserved) / len(results), 3),
        "rebuild_backfill_rate": round(sum(1 for item in results if item.rebuild_backfill_preserved) / len(results), 3),
        "average_compressed_count": round(sum(item.compressed_count for item in results) / len(results), 3),
        "passed": all(
            item.compressed_candidate_found
            and item.governed_top1_preserved
            and item.persistent_coverage_preserved
            and item.rebuild_backfill_preserved
            for item in results
        ),
    }

    artifact_dir = repo_root / ".planning" / "benchmarks"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "compressed_candidate_tier_summary.json"
    artifact = {
        "benchmark": "compressed_candidate_tier",
        "summary": summary,
        "scenarios": [
            {
                "name": item.name,
                "compressed_candidate_found": item.compressed_candidate_found,
                "governed_top1_preserved": item.governed_top1_preserved,
                "compressed_count": item.compressed_count,
                "selected_id": item.selected_id,
                "expected_top1": item.expected_top1,
                "persistent_coverage_preserved": item.persistent_coverage_preserved,
                "rebuild_backfill_preserved": item.rebuild_backfill_preserved,
            }
            for item in results
        ],
    }
    artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

    print("## Compressed Candidate Tier Benchmark")
    print(json.dumps(artifact, indent=2, ensure_ascii=False))
    print(f"[Artifact] Wrote {artifact_path}")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
