from __future__ import annotations

from aegis_py.truth_transition_timeline_report import render_truth_transition_timeline_html


def test_truth_transition_timeline_report_renders_winner_and_superseded_sections():
    payload = {
        "timeline_text": "[Truth Transition Timeline]\n[Winner Path]\n[Superseded Memories]",
        "result": {
            "hero": {
                "selected_memory": "Correction: the release owner is Bao.",
                "memory_id": "mem_winner",
                "truth_role": "winner",
                "governance_status": "active",
            },
            "winner_path": [{"label": "validated -> invalidated", "created_at": "2026-04-03T12:00:00+00:00", "summary": "corrected_by_newer_info"}],
            "suppressed_memories": [{"content": "The release owner is Linh.", "reason": "Superseded by newer memory", "latest_state": "invalidated", "latest_reason": "corrected_by_newer_info", "latest_at": "2026-04-03T12:01:00+00:00"}],
            "scope_events": [{"label": "truth_superseded_test", "created_at": "2026-04-03T12:02:00+00:00", "summary": "winner_id=mem_winner, reason=newer_correction"}],
            "transition_story": "Current truth replaced an older candidate.",
        },
    }

    html = render_truth_transition_timeline_html(payload)

    assert "Truth Transition Timeline" in html
    assert "Winner Path" in html
    assert "Superseded Memories" in html
    assert "Scope Governance Pulse" in html
