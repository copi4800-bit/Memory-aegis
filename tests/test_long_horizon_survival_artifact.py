from __future__ import annotations

from scripts.long_horizon_memory_survival import LongHorizonResult


def test_long_horizon_result_payload_shape():
    result = LongHorizonResult(
        name="survival_90d",
        horizon_days=90,
        passed=True,
        details={
            "selected_memory": "Correction: the office address is now 200 Second Street.",
            "rows_before": 50,
            "rows_after": 12,
            "deleted": {"archived_memories": 10, "superseded_memories": 5},
        },
    )

    assert result.name == "survival_90d"
    assert result.horizon_days == 90
    assert result.passed is True
    assert result.details["rows_after"] < result.details["rows_before"]
