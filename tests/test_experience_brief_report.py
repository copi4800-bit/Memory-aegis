from __future__ import annotations

from aegis_py.experience_brief_report import render_experience_brief_html


def test_experience_brief_report_renders_product_shell():
    payload = {
        "brief_text": "[TruthKeep Experience Brief]\nStrong Current Truth",
        "result": {
            "hero": {
                "label": "Strong Current Truth",
                "selected_memory": "Correction: the release owner is Bao.",
                "governance_status": "active",
                "truth_role": "winner",
                "trust_score": 0.92,
                "readiness_score": 0.84,
            },
            "executive_summary": [
                "Selected truth: Correction: the release owner is Bao.",
                "Governance: active / winner",
            ],
            "human_reason": "Chosen because it is the newest governed winner.",
            "profile_snapshot": ["Profile: prefers concise updates."],
            "next_actions": ["Show the correction flow and why-not output first."],
            "why_not": [{"content": "The release owner is Linh.", "reason": "Superseded by newer truth."}],
            "compressed_snapshot": {"passed": True, "coverage_rate": 1.0},
            "runtime_snapshot": {
                "memory_count": 5,
                "health_state": "HEALTHY",
                "open_conflicts": 0,
                "historical_rows": 2,
                "smilodon_peak_retirement_pressure": 0.2,
            },
        },
    }

    html = render_experience_brief_html(payload)

    assert "TruthKeep Product Brief" in html
    assert "Strong Current Truth" in html
    assert "What TruthKeep Believes" in html
    assert "Next Actions" in html
