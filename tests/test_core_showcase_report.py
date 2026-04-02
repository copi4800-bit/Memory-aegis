from __future__ import annotations

from aegis_py.core_showcase_report import render_core_showcase_html


def test_core_showcase_report_renders_final_form_html():
    payload = {
        "verdict": {
            "label": "Strong Current Truth",
            "trust_score": 0.91,
            "readiness_score": 0.82,
            "evidence_count": 2,
            "governance_events": 3,
            "health_level": "Good",
            "admission_state": "validated",
        },
        "executive_summary": [
            "Selected truth: Correction: the release date moved to April 24.",
            "Governance: active / winner",
        ],
        "selected_memory": "Correction: the release date moved to April 24.",
        "human_reason": "Chosen because it is the newest governed winner.",
        "truth_state": {
            "governance_status": "active",
            "truth_role": "winner",
            "policy_trace": ["C2_SLOT_WINNER_PROTECTION"],
        },
        "why_not": [
            {
                "content": "The release date is April 10.",
                "reason": "Superseded by newer truth.",
            }
        ],
        "evidence_summary": {
            "count": 2,
            "latest_source_kind": "manual",
            "latest_source_ref": "demo://release",
            "items": [
                {
                    "source_kind": "manual",
                    "source_ref": "demo://release",
                    "raw_content": "Release date corrected to April 24.",
                }
            ],
        },
        "governance_summary": {
            "event_count": 3,
            "transition_count": 1,
            "latest_event_kind": "active",
            "latest_transition": "validated",
            "events": [
                {
                    "event_kind": "active",
                    "created_at": "2026-04-02T00:00:00+00:00",
                    "payload": {"truth_role": "winner"},
                }
            ],
        },
        "signal_summary": {
            "labels": {"trust": "High", "readiness": "Warming"},
            "signals": {
                "belief_score": 0.88,
                "trust_score": 0.91,
                "readiness_score": 0.82,
                "conflict_signal": 0.0,
                "admission_state": "validated",
            },
        },
        "health_summary": {
            "health_label": "Good",
            "total_active": 4,
            "num_conflicts": 0,
            "num_stale": 1,
        },
    }

    html = render_core_showcase_html(payload)

    assert "Aegis Final-Form Memory Brief" in html
    assert "Strong Current Truth" in html
    assert "Why Aegis chose this memory" in html
    assert "Suppressed alternatives" in html
    assert "Chosen because it is the newest governed winner." in html
