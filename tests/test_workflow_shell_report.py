from __future__ import annotations

from aegis_py.workflow_shell_report import render_workflow_shell_html


def test_workflow_shell_report_renders_canonical_loop():
    payload = {
        "workflow_text": "[TruthKeep Workflow Shell]\n[Ordinary Path]\n[Truth Transition Timeline]\n[Operator Escape Hatches]",
        "result": {
            "hero": {
                "headline": "Strong Current Truth | Correction: the release owner is Bao.",
                "readiness": "READY",
                "health_state": "HEALTHY",
                "truth_role": "winner",
                "governance_status": "active",
            },
            "workflow_steps": [{"title": "Remember or correct a fact", "summary": "Store one concrete fact.", "tool": "memory_remember", "proof": "Correction: the release owner is Bao."}],
            "ordinary_lane": {"description": "The narrow daily path for normal use.", "operations": ["memory_remember", "memory_recall", "memory_correct"]},
            "current_truth": "Correction: the release owner is Bao.",
            "verification": {"human_reason": "Governed current truth.", "suppressed_count": 1, "suppressed_preview": ["The release owner is Linh."]},
            "truth_transition_timeline": {"story": "Current truth replaced an older candidate.", "preview": ["2026-04-03T12:00:00+00:00 | validated -> invalidated | corrected_by_newer_info"]},
            "next_actions": ["Use memory_correct when facts change."],
            "operator_escape_hatches": ["memory_core_showcase"],
        },
    }

    html = render_workflow_shell_html(payload)

    assert "TruthKeep Workflow Shell" in html
    assert "Ordinary Path" in html
    assert "Truth Transition Timeline" in html
    assert "Operator Escape Hatches" in html
