from __future__ import annotations

from aegis_py.dashboard_shell_report import render_dashboard_shell_html


def test_dashboard_shell_report_renders_unified_dashboard():
    payload = {
        "dashboard_text": "[TruthKeep Dashboard Shell]\nreadiness=READY",
        "result": {
            "hero": {
                "headline": "Strong Current Truth | Correction: the release owner is Bao.",
                "readiness": "READY",
                "health_state": "HEALTHY",
                "truth_role": "winner",
                "governance_status": "active",
            },
            "sections": [
                {"title": "Start Here", "summary": "Everyday actions.", "items": [{"tool": "memory_remember", "why": "Store a fact."}]},
                {"title": "Current Truth", "summary": "Governed current truth.", "items": ["Selected truth"]},
            ],
        },
    }

    html = render_dashboard_shell_html(payload)

    assert "TruthKeep Unified Dashboard" in html
    assert "Start Here" in html
    assert "Current Truth" in html
