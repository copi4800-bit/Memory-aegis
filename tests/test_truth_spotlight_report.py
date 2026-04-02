from __future__ import annotations

from pathlib import Path

from scripts.render_truth_spotlight_report import load_summary, render_report


def test_truth_spotlight_report_renders_summary_catalog_and_scenarios(tmp_path: Path):
    artifact = tmp_path / "truth_summary.json"
    artifact.write_text(
        """
{
  "summary": {
    "current_truth_top1_rate": 1.0,
    "suppressed_visibility_rate": 1.0,
    "superseded_visibility_rate": 0.75,
    "passed": true
  },
  "grouped_summary": {
    "correction": {
      "scenario_count": 1,
      "pass_rate": 1.0,
      "suppressed_visibility_rate": 1.0,
      "superseded_visibility_rate": 1.0
    }
  },
  "scenario_catalog": {
    "correction_current_truth": {
      "title": "Correction keeps current fact on top",
      "category": "correction",
      "intent": "correction_lookup",
      "description": "A corrected fact should beat the stale one."
    }
  },
  "scenarios": [
    {
      "name": "correction_current_truth",
      "category": "correction",
      "passed": true,
      "selected_id": "winner_1",
      "expected_id": "winner_1",
      "superseded_visible": true,
      "notes": ["Superseded candidate stayed visible in why-not."]
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    summary = load_summary(artifact)
    rendered = render_report(summary, artifact)

    assert "# Truth Spotlight Report" in rendered
    assert "## Grouped Summary" in rendered
    assert "## Scenario Catalog" in rendered
    assert "Correction keeps current fact on top" in rendered
    assert "### correction_current_truth" in rendered
    assert "- status: `PASS`" in rendered
    assert "Superseded candidate stayed visible in why-not." in rendered


def test_truth_spotlight_report_renders_historical_trend(tmp_path: Path):
    before_artifact = tmp_path / "before.json"
    before_artifact.write_text(
        """
{
  "summary": {
    "current_truth_top1_rate": 0.75,
    "suppressed_visibility_rate": 1.0,
    "superseded_visibility_rate": 0.5
  },
  "scenarios": [
    {
      "name": "correction_current_truth",
      "passed": false,
      "selected_id": "old_id"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    current_artifact = tmp_path / "current.json"
    current_artifact.write_text(
        """
{
  "summary": {
    "current_truth_top1_rate": 1.0,
    "suppressed_visibility_rate": 1.0,
    "superseded_visibility_rate": 0.75
  },
  "scenarios": [
    {
      "name": "correction_current_truth",
      "passed": true,
      "selected_id": "winner_1"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    before_summary = load_summary(before_artifact)
    current_summary = load_summary(current_artifact)
    rendered = render_report(current_summary, current_artifact, before_summary, before_artifact)

    assert "## Historical Trend" in rendered
    assert "improved by +0.25" in rendered
    assert "changed status to PASS" in rendered
