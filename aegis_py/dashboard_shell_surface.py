from __future__ import annotations

from typing import Any


def build_dashboard_shell_payload(*, query: str, scope_type: str, scope_id: str, consumer_shell: dict[str, Any], experience_brief: dict[str, Any], core_showcase: dict[str, Any], truth_transition_timeline: dict[str, Any]) -> dict[str, Any]:
    consumer_result = consumer_shell.get("result") or {}
    brief_result = experience_brief.get("result") or {}
    showcase_result = core_showcase.get("result") or {}
    hero = {
        "headline": consumer_result.get("hero", {}).get("headline") or "No current brief available.",
        "readiness": consumer_result.get("hero", {}).get("readiness"),
        "health_state": consumer_result.get("hero", {}).get("health_state"),
        "truth_role": brief_result.get("hero", {}).get("truth_role"),
        "governance_status": brief_result.get("hero", {}).get("governance_status"),
    }
    ordinary_lane = consumer_result.get("ordinary_lane", {})
    operator_lane = consumer_result.get("operator_lane", {})
    timeline_result = truth_transition_timeline.get("result") or {}
    sections = [
        {"title": "Ordinary Mode", "summary": ordinary_lane.get("description", "The narrow daily path for normal use."), "items": consumer_result.get("primary_actions", [])},
        {"title": "Current Truth", "summary": brief_result.get("human_reason") or "No governed explanation available.", "items": brief_result.get("executive_summary", [])},
        {"title": "Truth Transition Timeline", "summary": timeline_result.get("transition_story") or "No transition story available.", "items": timeline_result.get("timeline_preview", [])},
        {"title": "Operator Mode", "summary": operator_lane.get("description", "Inspection and maintenance tools for advanced use."), "items": operator_lane.get("operations", [])},
        {"title": "Deep Inspection", "summary": showcase_result.get("human_reason") or "No showcase payload available.", "items": [f"trust={showcase_result.get('verdict', {}).get('trust_score')}", f"readiness={showcase_result.get('verdict', {}).get('readiness_score')}", f"evidence={showcase_result.get('evidence_summary', {}).get('count')}"]},
    ]
    payload = {"query": query, "scope": {"scope_type": scope_type, "scope_id": scope_id}, "hero": hero, "sections": sections, "consumer_shell": consumer_shell, "experience_brief": experience_brief, "core_showcase": core_showcase, "dashboard_text": ""}
    payload["dashboard_text"] = render_dashboard_shell_text(payload)
    return {"query": query, "scope": {"scope_type": scope_type, "scope_id": scope_id}, "ready": bool(consumer_shell.get("ready")), "dashboard_text": payload["dashboard_text"], "result": payload}


def render_dashboard_shell_text(payload: dict[str, Any]) -> str:
    hero = payload["hero"]
    lines = [
        "[TruthKeep Dashboard Shell]",
        f"readiness={hero.get('readiness')} | health={hero.get('health_state')} | truth_role={hero.get('truth_role')} | governance={hero.get('governance_status')}",
        "",
        "[Headline]",
        hero.get("headline") or "No headline available.",
    ]
    for section in payload["sections"]:
        lines.extend(["", f"[{section['title']}]", section["summary"]])
        for item in section["items"]:
            if isinstance(item, dict):
                label = item.get("tool") or item.get("title") or "item"
                desc = item.get("why") or item.get("summary") or ""
                lines.append(f"- {label}: {desc}")
            else:
                lines.append(f"- {item}")
    return "\n".join(lines)
