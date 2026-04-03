from __future__ import annotations

from aegis_py.consumer_shell_report import render_consumer_shell_html


def test_consumer_shell_report_renders_landing_shell():
    payload = {
        "shell_text": "[TruthKeep Consumer Shell]\nreadiness=ready",
        "result": {
            "query": "release owner",
            "hero": {
                "readiness": "ready",
                "health_state": "HEALTHY",
                "headline": "Strong Current Truth | Correction: the release owner is Bao.",
            },
            "primary_actions": [
                {"tool": "memory_remember", "why": "Store a fact or correction."},
                {"tool": "memory_recall", "why": "Ask what TruthKeep currently believes."},
            ],
            "default_operations": ["memory_remember", "memory_recall"],
            "advanced_highlights": ["memory_experience_brief", "memory_spotlight"],
            "guidance": ["Local memory is ready."],
            "next_actions": ["Show the current-truth story first."],
        },
    }

    html = render_consumer_shell_html(payload)

    assert "TruthKeep Consumer Shell" in html
    assert "Start Here" in html
    assert "Everyday Tools" in html
    assert "Advanced Highlights" in html
