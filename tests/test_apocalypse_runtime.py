from __future__ import annotations

import json
from pathlib import Path

from scripts import apocalypse_v7
from scripts.apocalypse_v7 import ApocalypseConfig, run_apocalypse


def test_apocalypse_quick_profile_rejects_corruption_and_recovers_canary(tmp_path):
    workspace_dir = tmp_path / "apocalypse"
    report = run_apocalypse(
        db_path=str(workspace_dir / "apocalypse.db"),
        workspace_dir=str(workspace_dir),
        config=ApocalypseConfig(
            profile="quick",
            seed_count=80,
            scope_count=4,
            writer_threads=2,
            reader_threads=2,
            operations_per_writer=16,
            operations_per_reader=20,
            random_seed=4419,
            write_p95_budget_ms=150.0,
            search_p95_budget_ms=100.0,
            context_p95_budget_ms=100.0,
            max_retry_budget=5,
        ),
    )

    assert report["concurrency"]["hard_errors"] == 0
    assert report["concurrency"]["recall_hit_rate"] >= 0.9
    assert report["concurrency"]["context_hit_rate"] >= 0.75
    assert report["evaluation"]["checks"]["concurrency_retry_budget"] is True
    assert report["evaluation"]["checks"]["write_p95_budget"] is True
    assert report["evaluation"]["checks"]["search_p95_budget"] is True
    assert report["evaluation"]["checks"]["context_p95_budget"] is True
    assert report["corruption_recovery"]["corrupt_snapshot_rejected"] is True
    assert report["corruption_recovery"]["corrupt_live_rejected"] is True
    assert report["corruption_recovery"]["restore"]["restored"] is True
    assert report["corruption_recovery"]["recovered_health_state"] in {"HEALTHY", "DEGRADED_SYNC"}
    assert report["corruption_recovery"]["recovered_canary_hit"] is True
    assert report["evaluation"]["passed"] is True

    clean_snapshot = Path(report["corruption_recovery"]["clean_snapshot_path"])
    assert clean_snapshot.exists()


def test_apocalypse_cli_writes_report_and_prints_json_summary(tmp_path, monkeypatch, capsys):
    workspace_dir = tmp_path / "cli-apocalypse"
    report_path = workspace_dir / "report.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "apocalypse_v7.py",
            "--profile",
            "quick",
            "--workspace-dir",
            str(workspace_dir),
            "--db-path",
            str(workspace_dir / "cli.db"),
            "--report-path",
            str(report_path),
        ],
    )

    exit_code = apocalypse_v7.main()

    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert exit_code == 0
    assert summary["report_path"] == str(report_path)
    assert summary["profile"] == "quick"
    assert "concurrency_retries" in summary
    assert "write_p95_ms" in summary
    assert "search_p95_ms" in summary
    assert "context_p95_ms" in summary
    assert summary["evaluation_passed"] is True
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["evaluation"]["passed"] is True
    assert isinstance(report["concurrency"]["error_samples"], list)
    assert report["performance_budget"]["write_p95_ms"] == 150.0
