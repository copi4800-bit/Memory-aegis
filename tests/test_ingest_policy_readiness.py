from __future__ import annotations

from pathlib import Path

from scripts.check_ingest_policy_readiness import evaluate_readiness, load_summary, render_result


def test_ingest_policy_readiness_passes_on_balanced_summary(tmp_path: Path):
    artifact = tmp_path / "ingest_ready.json"
    artifact.write_text(
        """
{
  "scenarios": {
    "low_confidence_repetitive": {
      "summary": {
        "attempted_writes": 30,
        "accepted_writes": 10,
        "rejected_or_noop_writes": 20,
        "diagnostic_outcomes": {
          "policy_block": 20,
          "exact_dedup": 9,
          "admit": 1
        },
        "blocked_reason_counts": {
          "blocked_low_confidence": 20
        },
        "reconciled": true,
        "canonical_admitted": true
      }
    },
    "high_confidence_distinct": {
      "summary": {
        "attempted_writes": 12,
        "accepted_writes": 12,
        "rejected_or_noop_writes": 0,
        "diagnostic_outcomes": {
          "admit": 12
        },
        "blocked_reason_counts": {},
        "reconciled": true,
        "canonical_admitted": true
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    summary = load_summary(artifact)
    passed, failures = evaluate_readiness(summary)

    assert passed is True
    assert failures == []


def test_ingest_policy_readiness_reports_when_high_confidence_path_is_too_strict(tmp_path: Path):
    artifact = tmp_path / "ingest_fail.json"
    artifact.write_text(
        """
{
  "scenarios": {
    "low_confidence_repetitive": {
      "summary": {
        "attempted_writes": 30,
        "accepted_writes": 10,
        "rejected_or_noop_writes": 20,
        "diagnostic_outcomes": {
          "policy_block": 20,
          "exact_dedup": 9,
          "admit": 1
        },
        "blocked_reason_counts": {
          "blocked_low_confidence": 20
        },
        "reconciled": true,
        "canonical_admitted": true
      }
    },
    "high_confidence_distinct": {
      "summary": {
        "attempted_writes": 12,
        "accepted_writes": 8,
        "rejected_or_noop_writes": 4,
        "diagnostic_outcomes": {
          "admit": 8,
          "policy_block": 4
        },
        "blocked_reason_counts": {
          "blocked_low_confidence": 4
        },
        "reconciled": true,
        "canonical_admitted": true
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    summary = load_summary(artifact)
    passed, failures = evaluate_readiness(summary)
    rendered = render_result(artifact, passed, failures, summary)

    assert passed is False
    assert "high_confidence_distinct did not admit every attempted write" in failures
    assert "passed: no" in rendered
