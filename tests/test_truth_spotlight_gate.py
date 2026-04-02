from __future__ import annotations

from pathlib import Path

from scripts.check_truth_spotlight_gate import evaluate_thresholds, load_summary, render_result


def test_truth_spotlight_gate_passes_on_expected_summary(tmp_path: Path):
    artifact = tmp_path / "truth_summary.json"
    artifact.write_text(
        """
{
  "summary": {
    "current_truth_top1_rate": 1.0,
    "suppressed_visibility_rate": 1.0,
    "superseded_visibility_rate": 0.75
  },
  "grouped_summary": {
    "correction": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    },
    "conflict": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    },
    "lexical_resilience": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    },
    "override": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    summary = load_summary(artifact)
    passed, failures = evaluate_thresholds(summary)

    assert passed is True
    assert failures == []


def test_truth_spotlight_gate_reports_threshold_failures(tmp_path: Path):
    artifact = tmp_path / "truth_summary_fail.json"
    artifact.write_text(
        """
{
  "summary": {
    "current_truth_top1_rate": 0.75,
    "suppressed_visibility_rate": 0.5,
    "superseded_visibility_rate": 0.5
  },
  "grouped_summary": {
    "correction": {
      "pass_rate": 0.0,
      "suppressed_visibility_rate": 0.0,
      "superseded_visibility_rate": 0.0
    },
    "conflict": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    },
    "lexical_resilience": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    },
    "override": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    summary = load_summary(artifact)
    passed, failures = evaluate_thresholds(summary)
    rendered = render_result(artifact, passed, failures, summary)

    assert passed is False
    assert len(failures) >= 6
    assert "current_truth_top1_rate=0.750 fell below required 1.000" in rendered
    assert "correction.pass_rate=0.000 fell below required 1.000" in rendered
    assert "passed: no" in rendered


def test_truth_spotlight_gate_fails_when_group_is_missing(tmp_path: Path):
    artifact = tmp_path / "truth_summary_missing_group.json"
    artifact.write_text(
        """
{
  "summary": {
    "current_truth_top1_rate": 1.0,
    "suppressed_visibility_rate": 1.0,
    "superseded_visibility_rate": 0.75
  },
  "grouped_summary": {
    "correction": {
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    summary = load_summary(artifact)
    passed, failures = evaluate_thresholds(summary)

    assert passed is False
    assert "grouped_summary missing required category 'conflict'" in failures
