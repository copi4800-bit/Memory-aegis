from __future__ import annotations

from typing import Any


def _to_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _build_workflow_steps(*, consumer_shell: dict[str, Any], experience_brief: dict[str, Any], core_showcase: dict[str, Any]) -> list[dict[str, Any]]:
    brief_result = experience_brief.get("result") or {}
    showcase_result = core_showcase.get("result") or {}
    selected = brief_result.get("hero", {}).get("selected_memory") or "No current truth selected yet."
    why_not = _to_list(brief_result.get("why_not"))
    executive = _to_list(brief_result.get("executive_summary"))
    human_reason = brief_result.get("human_reason") or "No governed explanation available."
    return [
        {
            "id": "capture",
            "title": "Remember or correct a fact",
            "summary": "Store one concrete fact or a correction through the default memory path.",
            "tool": "memory_remember",
            "proof": executive[0] if executive else selected,
        },
        {
            "id": "inspect",
            "title": "Inspect current truth",
            "summary": "Read what TruthKeep currently believes before changing anything else.",
            "tool": "memory_recall",
            "proof": selected,
        },
        {
            "id": "correct",
            "title": "Correct stale truth safely",
            "summary": "Apply a correction and let governance keep the old fact visible but suppressed.",
            "tool": "memory_correct",
            "proof": why_not[0].get("content") if why_not else human_reason,
        },
        {
            "id": "verify",
            "title": "Verify why the winner won",
            "summary": "Use explanation surfaces only after the current truth is stable.",
            "tool": "memory_experience_brief",
            "proof": showcase_result.get("human_reason") or human_reason,
        },
    ]


def build_workflow_shell_payload(*, query: str, scope_type: str, scope_id: str, consumer_shell: dict[str, Any], experience_brief: dict[str, Any], core_showcase: dict[str, Any], truth_transition_timeline: dict[str, Any]) -> dict[str, Any]:
    consumer_result = consumer_shell.get("result") or {}
    brief_result = experience_brief.get("result") or {}
    steps = _build_workflow_steps(consumer_shell=consumer_shell, experience_brief=experience_brief, core_showcase=core_showcase)
    hero = {
        "headline": consumer_result.get("hero", {}).get("headline") or "No workflow headline available.",
        "readiness": consumer_result.get("hero", {}).get("readiness"),
        "health_state": consumer_result.get("hero", {}).get("health_state"),
        "truth_role": brief_result.get("hero", {}).get("truth_role"),
        "governance_status": brief_result.get("hero", {}).get("governance_status"),
    }
    ordinary_lane = consumer_result.get("ordinary_lane", {})
    operator_lane = consumer_result.get("operator_lane", {})
    suppressed = _to_list(brief_result.get("why_not"))
    timeline_result = truth_transition_timeline.get("result") or {}
    payload = {
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "hero": hero,
        "workflow_steps": steps,
        "current_truth": brief_result.get("hero", {}).get("selected_memory") or "No current truth selected.",
        "verification": {
            "human_reason": brief_result.get("human_reason") or "No governed reason available.",
            "suppressed_count": len(suppressed),
            "suppressed_preview": [item.get("content") for item in suppressed[:2]],
        },
        "ordinary_lane": ordinary_lane,
        "truth_transition_timeline": {
            "story": timeline_result.get("transition_story") or "No transition story available.",
            "preview": _to_list(timeline_result.get("timeline_preview"))[:4],
        },
        "next_actions": _to_list(consumer_result.get("next_actions"))[:4],
        "operator_escape_hatches": operator_lane.get("operations", [])[:6] or ["memory_spotlight", "memory_core_showcase", "memory_governance", "memory_v10_field_snapshot"],
        "workflow_text": "",
    }
    payload["workflow_text"] = render_workflow_shell_text(payload)
    return {"query": query, "scope": {"scope_type": scope_type, "scope_id": scope_id}, "ready": bool(consumer_shell.get("ready")), "workflow_text": payload["workflow_text"], "result": payload}


def render_workflow_shell_text(payload: dict[str, Any]) -> str:
    hero = payload["hero"]
    verification = payload["verification"]
    ordinary = payload.get("ordinary_lane", {})
    lines = [
        "[TruthKeep Workflow Shell]",
        f"readiness={hero.get('readiness')} | health={hero.get('health_state')} | truth_role={hero.get('truth_role')} | governance={hero.get('governance_status')}",
        "",
        "[Headline]",
        hero.get("headline") or "No headline available.",
        "",
        "[Current Truth]",
        payload.get("current_truth") or "No current truth selected.",
        "",
        "[Ordinary Path]",
        ordinary.get("description", "The narrow daily path for normal use."),
    ]
    for step in payload["workflow_steps"]:
        lines.append(f"- {step['title']} | tool={step['tool']}")
        lines.append(f"  {step['summary']}")
        lines.append(f"  proof={step['proof']}")
    lines.extend(["", "[Verification]", verification["human_reason"], f"suppressed_count={verification['suppressed_count']}"])
    for item in verification["suppressed_preview"]:
        lines.append(f"- suppressed={item}")
    lines.extend(["", "[Truth Transition Timeline]", payload["truth_transition_timeline"]["story"]])
    for item in payload["truth_transition_timeline"]["preview"]:
        lines.append(f"- {item}")
    lines.extend(["", "[Next Actions]"])
    for item in payload["next_actions"] or ["No immediate next action."]:
        lines.append(f"- {item}")
    lines.extend(["", "[Operator Escape Hatches]"])
    for item in payload["operator_escape_hatches"]:
        lines.append(f"- {item}")
    return "\n".join(lines)
