import json
from pathlib import Path

from aegis_py.app import AegisApp
from aegis_py.retrieval import compressed_tier as compressed_tier_module
from scripts import (
    benchmark_compressed_candidate_tier as bench,
    check_compressed_tier_completion as completion,
    check_compressed_tier_gate as gate,
    render_compressed_tier_report as report,
)


def test_compressed_tier_status_surfaces_coverage_and_gate(tmp_path, monkeypatch):
    artifact_root = Path(tmp_path)
    monkeypatch.setattr(bench, "resolve_repo_root", lambda: artifact_root)
    assert bench.main() == 0
    monkeypatch.setattr(
        compressed_tier_module,
        "DEFAULT_COMPRESSED_TIER_ARTIFACT",
        artifact_root / ".planning" / "benchmarks" / "compressed_candidate_tier_summary.json",
    )

    app = AegisApp(str(tmp_path / "phase119_status.db"))
    try:
        app.put_memory(
            "Harbor steward keeps the compressed manifest ready.",
            type="semantic",
            scope_type="agent",
            scope_id="phase119_scope",
            source_kind="manual",
            source_ref="test://phase119",
            subject="harbor.steward",
            confidence=0.94,
            metadata={"is_winner": True},
        )
        status = app.compressed_tier_status(scope_type="agent", scope_id="phase119_scope")
        compressed = status["compressed_tier"]
        assert compressed["coverage"]["coverage_rate"] >= 1.0
        assert compressed["benchmark_available"] is True
        assert compressed["readiness"]["passed"] is True
    finally:
        app.close()


def test_compressed_tier_gate_report_and_completion(tmp_path, monkeypatch):
    artifact_root = Path(tmp_path)
    monkeypatch.setattr(bench, "resolve_repo_root", lambda: artifact_root)
    assert bench.main() == 0
    artifact = artifact_root / ".planning" / "benchmarks" / "compressed_candidate_tier_summary.json"
    output = artifact_root / ".planning" / "benchmarks" / "compressed_candidate_tier_report.md"

    report_text = report.render_report(json.loads(artifact.read_text(encoding="utf-8")), artifact)
    assert "persistent_coverage_rate" in report_text
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report_text, encoding="utf-8")

    gate_artifact = gate.load_compressed_tier_artifact(artifact)
    passed, failures, _ = compressed_tier_module.evaluate_compressed_tier_gate(gate_artifact)
    assert passed is True
    assert failures == []

    completion_artifact = completion.load_compressed_tier_artifact(artifact)
    passed, failures, summary_metrics = compressed_tier_module.evaluate_compressed_tier_gate(completion_artifact)
    assert passed is True
    assert failures == []
    assert summary_metrics["persistent_coverage_rate"] >= 1.0
