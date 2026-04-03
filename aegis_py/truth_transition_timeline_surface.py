from __future__ import annotations

from typing import Any


def _to_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _preview_payload(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict) or not payload:
        return "no payload"
    priority_keys = ["reason", "winner_id", "recommended_state", "governance_status", "truth_role"]
    parts: list[str] = []
    for key in priority_keys:
        value = payload.get(key)
        if value not in (None, "", [], {}):
            parts.append(f"{key}={value}")
    if parts:
        return ", ".join(parts[:2])
    key = sorted(payload.keys())[0]
    return f"{key}={payload.get(key)}"


def _transition_entry(item: dict[str, Any]) -> dict[str, Any]:
    from_state = item.get("from_state") or "unknown"
    to_state = item.get("to_state") or "unknown"
    reason = item.get("reason") or "unspecified"
    return {
        "kind": "transition",
        "created_at": item.get("created_at"),
        "label": f"{from_state} -> {to_state}",
        "summary": reason,
        "memory_id": item.get("memory_id"),
    }


def _event_entry(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "event",
        "created_at": item.get("created_at"),
        "label": item.get("event_kind") or "governance_event",
        "summary": _preview_payload(item.get("payload") or {}),
        "memory_id": item.get("memory_id"),
    }


def _suppressed_entry(item: dict[str, Any], governance: dict[str, Any]) -> dict[str, Any]:
    transitions = _to_list(governance.get("transitions"))
    events = _to_list(governance.get("events"))
    latest_transition = transitions[-1] if transitions else None
    latest_event = events[0] if events else None
    latest_state = latest_transition.get("to_state") if latest_transition else None
    latest_at = (latest_transition or latest_event or {}).get("created_at")
    latest_reason = latest_transition.get("reason") if latest_transition is not None else (latest_event.get("event_kind") if latest_event is not None else None)
    return {
        "id": item.get("id"),
        "content": item.get("content") or "Unknown suppressed memory.",
        "reason": item.get("reason") or "suppressed",
        "latest_state": latest_state or "suppressed",
        "latest_reason": latest_reason or "suppressed_by_governance",
        "latest_at": latest_at,
    }


def _build_story(*, hero: dict[str, Any], winner_entries: list[dict[str, Any]], suppressed: list[dict[str, Any]]) -> str:
    selected = hero.get("selected_memory") or "No current truth selected."
    if suppressed and winner_entries:
        latest = winner_entries[-1]
        return (
            f"Current truth remains '{selected}' after {len(winner_entries)} tracked winner transition/event step(s), "
            f"while {len(suppressed)} older or competing memory candidate(s) stayed suppressed. "
            f"Latest winner movement: {latest['label']} because {latest['summary']}."
        )
    if suppressed:
        return (
            f"Current truth remains '{selected}' and {len(suppressed)} suppressed candidate(s) stay behind it, "
            "but no explicit winner transition history was needed to keep the state stable."
        )
    if winner_entries:
        latest = winner_entries[-1]
        return f"Current truth '{selected}' has a visible winner path. Latest movement: {latest['label']} because {latest['summary']}."
    return f"Current truth '{selected}' is stable, but no explicit transition history was recorded for this scope yet."


def build_truth_transition_timeline_payload(*, query: str, scope_type: str, scope_id: str, experience_brief: dict[str, Any], scope_governance: dict[str, Any], winner_governance: dict[str, Any], suppressed_governance: dict[str, dict[str, Any]]) -> dict[str, Any]:
    brief_result = experience_brief.get("result") or {}
    showcase = brief_result.get("showcase") or {}
    hero = {
        "selected_memory": brief_result.get("hero", {}).get("selected_memory") or "No current truth selected.",
        "memory_id": showcase.get("memory_id"),
        "truth_role": brief_result.get("hero", {}).get("truth_role"),
        "governance_status": brief_result.get("hero", {}).get("governance_status"),
    }
    winner_transitions = [_transition_entry(item) for item in _to_list(winner_governance.get("transitions"))[:6]]
    winner_events = [_event_entry(item) for item in list(reversed(_to_list(winner_governance.get("events"))[:6]))]
    winner_path = sorted(winner_transitions + winner_events, key=lambda item: (item.get("created_at") or "", item["kind"]))
    scope_events = [_event_entry(item) for item in list(reversed(_to_list(scope_governance.get("events"))[:6]))]
    suppressed = [_suppressed_entry(item, suppressed_governance.get(item.get("id") or "", {})) for item in _to_list(brief_result.get("why_not"))[:3]]
    preview = [f"{item['created_at'] or 'unknown'} | {item['label']} | {item['summary']}" for item in winner_path[-4:]]
    payload = {
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "hero": hero,
        "winner_path": winner_path,
        "suppressed_memories": suppressed,
        "scope_events": scope_events,
        "timeline_preview": preview,
        "transition_story": _build_story(hero=hero, winner_entries=winner_path, suppressed=suppressed),
        "timeline_text": "",
    }
    payload["timeline_text"] = render_truth_transition_timeline_text(payload)
    return {"query": query, "scope": {"scope_type": scope_type, "scope_id": scope_id}, "ready": True, "timeline_text": payload["timeline_text"], "result": payload}


def render_truth_transition_timeline_text(payload: dict[str, Any]) -> str:
    hero = payload["hero"]
    lines = [
        "[Truth Transition Timeline]",
        f"truth_role={hero.get('truth_role')} | governance={hero.get('governance_status')} | winner_memory_id={hero.get('memory_id') or 'unknown'}",
        "",
        "[Current Truth]",
        hero.get("selected_memory") or "No current truth selected.",
        "",
        "[Transition Story]",
        payload.get("transition_story") or "No transition story available.",
        "",
        "[Winner Path]",
    ]
    if payload["winner_path"]:
        for item in payload["winner_path"]:
            lines.append(f"- {item['created_at'] or 'unknown'} | {item['label']} | {item['summary']}")
    else:
        lines.append("No winner path entries recorded.")
    lines.extend(["", "[Superseded Memories]"])
    if payload["suppressed_memories"]:
        for item in payload["suppressed_memories"]:
            lines.append(f"- {item['content']} | suppressed_reason={item['reason']} | latest_state={item['latest_state']} | latest_reason={item['latest_reason']} | at={item['latest_at'] or 'unknown'}")
    else:
        lines.append("No suppressed memories for this query.")
    lines.extend(["", "[Scope Governance Pulse]"])
    if payload["scope_events"]:
        for item in payload["scope_events"]:
            lines.append(f"- {item['created_at'] or 'unknown'} | {item['label']} | {item['summary']}")
    else:
        lines.append("No scope governance events recorded.")
    return "\n".join(lines)
