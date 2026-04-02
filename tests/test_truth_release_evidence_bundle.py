from __future__ import annotations

import json
from pathlib import Path

from scripts.bundle_truth_release_evidence import build_bundle, load_json


def test_truth_release_evidence_bundle_includes_core_artifacts(tmp_path: Path):
    summary_path = tmp_path / "truth_summary.json"
    report_path = tmp_path / "truth_report.md"
    summary_path.write_text(
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
  },
  "scenario_catalog": {
    "correction_current_truth": {
      "title": "Correction keeps current fact on top"
    }
  },
  "scenarios": [
    {
      "name": "correction_current_truth",
      "passed": true
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    report_path.write_text("# Truth Spotlight Report\n", encoding="utf-8")

    summary = load_json(summary_path)
    bundle = build_bundle(summary_path, report_path, summary)

    assert bundle["bundle"] == "truth_release_evidence"
    assert bundle["passed"] is True
    assert bundle["summary_path"] == str(summary_path)
    assert bundle["report_path"] == str(report_path)
    assert bundle["scenario_count"] == 1
    assert "correction_current_truth" in bundle["scenario_catalog"]
