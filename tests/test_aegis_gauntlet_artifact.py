from __future__ import annotations

from scripts.aegis_gauntlet import GauntletResult, build_grouped_summary


def test_aegis_gauntlet_grouped_summary_shapes_categories():
    results = [
        GauntletResult("truth_case", "core_truth", True, {"selected_id": "a"}),
        GauntletResult("scale_case", "scale", False, {"selected_id": "b"}),
        GauntletResult("adv_case", "adversarial", True, {"selected_id": "c"}),
        GauntletResult("product_case", "product_readiness", True, {"selected_id": "d"}),
        GauntletResult("recovery_case", "product_readiness", True, {"selected_id": "e"}),
        GauntletResult("ingest_case", "product_readiness", False, {"selected_id": "f"}),
    ]

    summary = build_grouped_summary(results)

    assert summary["core_truth"]["scenario_count"] == 1
    assert summary["core_truth"]["pass_rate"] == 1.0
    assert summary["scale"]["pass_rate"] == 0.0
    assert summary["adversarial"]["pass_rate"] == 1.0
    assert summary["product_readiness"]["scenario_count"] == 3
    assert summary["product_readiness"]["pass_rate"] == 0.667
