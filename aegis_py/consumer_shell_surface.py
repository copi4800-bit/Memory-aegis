from __future__ import annotations

from typing import Any


def _safe_query_preview(query: str | None) -> str:
    text = (query or "").strip()
    return text if text else "What should TruthKeep remember or correct right now?"


def _brief_headline(experience_brief: dict[str, Any]) -> str:
    result = experience_brief.get("result")
    if not isinstance(result, dict):
        return "No current-truth brief yet for this scope."
    hero = result.get("hero", {})
    return f"{hero.get('label', 'Unknown')} | {hero.get('selected_memory', 'No selected memory')}"


def build_consumer_shell_payload(
    *,
    query: str,
    scope_type: str,
    scope_id: str,
    public_surface: dict[str, Any],
    onboarding: dict[str, Any],
    status_summary: str,
    experience_brief: dict[str, Any],
) -> dict[str, Any]:
    consumer_contract = public_surface.get("consumer_contract", {})
    default_ops = consumer_contract.get("default_operations", [])
    advanced_ops = consumer_contract.get("advanced_operations", [])
    readiness = onboarding.get("readiness", "unknown")
    health_state = onboarding.get("health_state", "unknown")
    guidance = onboarding.get("guidance", [])
    result = experience_brief.get("result") or {}
    next_actions = result.get("next_actions", []) if isinstance(result, dict) else []
    payload = {
        "query": _safe_query_preview(query),
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "hero": {
            "readiness": readiness,
            "health_state": health_state,
            "headline": _brief_headline(experience_brief),
        },
        "primary_actions": [
            {"tool": "memory_remember", "why": "Store a fact or correction."},
            {"tool": "memory_recall", "why": "Ask what TruthKeep currently believes."},
            {"tool": "memory_experience_brief", "why": "Show the product-facing current-truth story."},
        ],
        "default_operations": default_ops[:6],
        "advanced_highlights": [
            tool for tool in advanced_ops
            if tool in {"memory_spotlight", "memory_core_showcase", "memory_experience_brief", "memory_compressed_tier_status", "memory_doctor"}
        ],
        "guidance": guidance[:5],
        "status_summary": status_summary,
        "experience_brief": experience_brief,
        "next_actions": next_actions[:4],
    }
    payload["shell_text"] = render_consumer_shell_text(payload)
    return {
        "query": payload["query"],
        "scope": payload["scope"],
        "ready": str(readiness).strip().upper() == "READY",
        "shell_text": payload["shell_text"],
        "result": payload,
    }


def render_consumer_shell_text(payload: dict[str, Any]) -> str:
    hero = payload["hero"]
    lines = [
        "[TruthKeep Consumer Shell]",
        f"readiness={hero['readiness']} | health={hero['health_state']}",
        "",
        "[Current Brief]",
        hero["headline"],
        "",
        "[Start Here]",
    ]
    for item in payload["primary_actions"]:
        lines.append(f"- {item['tool']}: {item['why']}")
    lines.extend(["", "[Everyday Tools]"])
    lines.extend(f"- {tool}" for tool in payload["default_operations"] or ["No default operations listed."])
    lines.extend(["", "[Advanced Highlights]"])
    lines.extend(f"- {tool}" for tool in payload["advanced_highlights"] or ["No advanced highlights listed."])
    lines.extend(["", "[Setup Guidance]"])
    lines.extend(f"- {item}" for item in payload["guidance"] or ["No setup guidance required."])
    if payload["next_actions"]:
        lines.extend(["", "[Next Actions]"])
        lines.extend(f"- {item}" for item in payload["next_actions"])
    lines.extend(["", "[Status Summary]", payload["status_summary"]])
    return "\n".join(lines)
