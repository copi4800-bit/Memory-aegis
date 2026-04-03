import json
from pathlib import Path

from scripts import benchmark_compressed_candidate_tier as bench


def test_compressed_candidate_benchmark_writes_passing_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(bench, "resolve_repo_root", lambda: Path(tmp_path))
    # use repo-local root resolution by running from actual workspace import path
    result = bench.main()
    assert result == 0

    artifact = json.loads(
        (tmp_path / ".planning" / "benchmarks" / "compressed_candidate_tier_summary.json").read_text(encoding="utf-8")
    )
    assert artifact["summary"]["compressed_candidate_yield_rate"] >= 1.0
    assert artifact["summary"]["governed_top1_preservation_rate"] >= 1.0
    assert artifact["summary"]["persistent_coverage_rate"] >= 1.0
    assert artifact["summary"]["rebuild_backfill_rate"] >= 1.0
    assert artifact["summary"]["passed"] is True
