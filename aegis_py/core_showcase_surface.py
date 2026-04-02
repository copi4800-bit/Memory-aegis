from __future__ import annotations

from typing import Any

from .spotlight_surface import build_spotlight_payload


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _trust_label(score: float) -> str:
    if score >= 0.85:
        return "High"
    if score >= 0.65:
        return "Medium"
    return "Low"


def _readiness_label(score: float) -> str:
    if score >= 0.85:
        return "Ready"
    if score >= 0.55:
        return "Warming"
    return "Cold"


def _health_label(level: str | None) -> str:
    return (level or "unknown").replace("_", " ").title()


def _summarize_evidence(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    first = evidence[0] if evidence else None
    return {
        "count": len(evidence),
        "latest_source_kind": first.get("source_kind") if first else None,
        "latest_source_ref": first.get("source_ref") if first else None,
        "items": evidence[:5],
    }


def _summarize_governance(governance: dict[str, Any]) -> dict[str, Any]:
    events = governance.get("events", [])[:5]
    transitions = governance.get("transitions", [])[:5]
    latest_event = events[0] if events else None
    latest_transition = transitions[0] if transitions else None
    return {
        "event_count": len(governance.get("events", [])),
        "transition_count": len(governance.get("transitions", [])),
        "latest_event_kind": latest_event.get("event_kind") if latest_event else None,
        "latest_transition": latest_transition.get("to_state") if latest_transition else None,
        "events": events,
        "transitions": transitions,
    }


def _summarize_signals(v10_signals: dict[str, Any], transition_gate: dict[str, Any]) -> dict[str, Any]:
    signals = v10_signals.get("signals", {})
    trust_score = _to_float(signals.get("trust_score"))
    readiness_score = _to_float(signals.get("readiness_score"))
    return {
        "observables": v10_signals.get("observables", {}),
        "signals": {
            "belief_score": signals.get("belief_score"),
            "trust_score": signals.get("trust_score"),
            "readiness_score": signals.get("readiness_score"),
            "conflict_signal": signals.get("conflict_signal"),
            "admission_state": signals.get("admission_state"),
        },
        "labels": {
            "trust": _trust_label(trust_score),
            "readiness": _readiness_label(readiness_score),
        },
        "transition_gate": transition_gate.get("decision", {}),
    }


def _summarize_graph(neighbors: dict[str, Any]) -> dict[str, Any]:
    items = neighbors.get("neighbors", [])[:5]
    preview = []
    for item in items:
        preview.append(
            {
                "target_id": item.get("target_id"),
                "link_type": item.get("link_type"),
                "weight": item.get("weight"),
            }
        )
    return {
        "neighbor_count": len(neighbors.get("neighbors", [])),
        "neighbors": items,
        "preview": preview,
    }


def _summarize_health(health: dict[str, Any]) -> dict[str, Any]:
    return {
        "health_level": health.get("health_level"),
        "health_label": _health_label(health.get("health_level")),
        "total_active": health.get("total_active"),
        "num_conflicts": health.get("num_conflicts"),
        "num_stale": health.get("num_stale"),
    }


def _build_verdict(
    *,
    truth_state: dict[str, Any],
    signal_summary: dict[str, Any],
    evidence_summary: dict[str, Any],
    governance_summary: dict[str, Any],
    health_summary: dict[str, Any],
) -> dict[str, Any]:
    trust_score = _to_float(signal_summary["signals"].get("trust_score"))
    readiness_score = _to_float(signal_summary["signals"].get("readiness_score"))
    truth_role = truth_state.get("truth_role")
    governance_status = truth_state.get("governance_status")
    state = signal_summary["signals"].get("admission_state")
    if truth_role == "winner" and governance_status == "active" and trust_score >= 0.8:
        label = "Strong Current Truth"
    elif trust_score >= 0.6:
        label = "Governed Candidate"
    else:
        label = "Weak Memory Candidate"
    return {
        "label": label,
        "trust_score": trust_score,
        "readiness_score": readiness_score,
        "evidence_count": evidence_summary["count"],
        "governance_events": governance_summary["event_count"],
        "health_level": health_summary["health_label"],
        "admission_state": state,
    }


def _build_executive_summary(
    *,
    selected_memory: str,
    truth_state: dict[str, Any],
    signal_summary: dict[str, Any],
    evidence_summary: dict[str, Any],
    why_not: list[dict[str, Any]],
) -> list[str]:
    return [
        f"Selected truth: {selected_memory}",
        (
            "Governance: "
            f"{truth_state.get('governance_status')} / {truth_state.get('truth_role')}"
        ),
        (
            "Core confidence: "
            f"trust={_to_float(signal_summary['signals'].get('trust_score')):.3f} "
            f"({signal_summary['labels']['trust']}), "
            f"readiness={_to_float(signal_summary['signals'].get('readiness_score')):.3f} "
            f"({signal_summary['labels']['readiness']})"
        ),
        f"Evidence trail: {evidence_summary['count']} linked event(s)",
        f"Suppressed alternatives: {len(why_not)}",
    ]


def build_core_showcase_payload(
    result: Any,
    *,
    evidence: list[dict[str, Any]],
    governance: dict[str, Any],
    neighbors: dict[str, Any],
    v10_signals: dict[str, Any],
    transition_gate: dict[str, Any],
    health: dict[str, Any],
    locale: str = "vi",
) -> dict[str, Any]:
    spotlight = build_spotlight_payload(result, locale=locale)
    evidence_summary = _summarize_evidence(evidence)
    governance_summary = _summarize_governance(governance)
    signal_summary = _summarize_signals(v10_signals, transition_gate)
    graph_summary = _summarize_graph(neighbors)
    health_summary = _summarize_health(health)
    verdict = _build_verdict(
        truth_state=spotlight["truth_state"],
        signal_summary=signal_summary,
        evidence_summary=evidence_summary,
        governance_summary=governance_summary,
        health_summary=health_summary,
    )
    executive_summary = _build_executive_summary(
        selected_memory=spotlight["selected_memory"],
        truth_state=spotlight["truth_state"],
        signal_summary=signal_summary,
        evidence_summary=evidence_summary,
        why_not=spotlight["why_not"],
    )
    return {
        "memory_id": result.memory.id,
        "verdict": verdict,
        "executive_summary": executive_summary,
        "selected_memory": spotlight["selected_memory"],
        "human_reason": spotlight["human_reason"],
        "truth_state": spotlight["truth_state"],
        "why_not": spotlight["why_not"],
        "evidence_summary": evidence_summary,
        "governance_summary": governance_summary,
        "signal_summary": signal_summary,
        "graph_summary": graph_summary,
        "health_summary": health_summary,
    }


def render_core_showcase_text(payload: dict[str, Any]) -> str:
    verdict = payload["verdict"]
    signal_summary = payload["signal_summary"]
    governance = payload["governance_summary"]
    evidence = payload["evidence_summary"]
    graph = payload["graph_summary"]
    health = payload["health_summary"]
    why_not = payload["why_not"]

    lines = [
        "[Aegis Core Verdict]",
        (
            f"{verdict['label']} | trust={verdict['trust_score']:.3f} "
            f"| readiness={verdict['readiness_score']:.3f} "
            f"| evidence={verdict['evidence_count']} "
            f"| health={verdict['health_level']}"
        ),
        "",
        "[Executive Summary]",
    ]
    lines.extend(f"- {item}" for item in payload["executive_summary"])
    lines.extend(
        [
            "",
            "[Selected Result]",
            payload["selected_memory"],
            "",
            "[Why This]",
            payload["human_reason"],
            "",
            "[Truth State]",
            (
                f"role={payload['truth_state'].get('truth_role')} | "
                f"status={payload['truth_state'].get('governance_status')} | "
                f"policy_trace={', '.join(payload['truth_state'].get('policy_trace', [])) or 'none'}"
            ),
            "",
            "[Evidence Trail]",
            (
                f"{evidence['count']} event(s) | latest_source_kind={evidence.get('latest_source_kind') or 'unknown'} "
                f"| latest_source_ref={evidence.get('latest_source_ref') or 'unknown'}"
            ),
            "",
            "[Governance Timeline]",
            (
                f"events={governance['event_count']} | transitions={governance['transition_count']} | "
                f"latest_event={governance.get('latest_event_kind') or 'none'} | "
                f"latest_transition={governance.get('latest_transition') or 'none'}"
            ),
            "",
            "[Core Signals]",
            (
                f"belief={_to_float(signal_summary['signals'].get('belief_score')):.3f} | "
                f"trust={_to_float(signal_summary['signals'].get('trust_score')):.3f} ({signal_summary['labels']['trust']}) | "
                f"readiness={_to_float(signal_summary['signals'].get('readiness_score')):.3f} ({signal_summary['labels']['readiness']}) | "
                f"conflict={_to_float(signal_summary['signals'].get('conflict_signal')):.3f} | "
                f"state={signal_summary['signals'].get('admission_state')}"
            ),
            "",
            "[Transition Gate]",
            (
                f"recommended_state={signal_summary['transition_gate'].get('recommended_state')} | "
                f"recommended_action={signal_summary['transition_gate'].get('recommended_action')} | "
                f"promote_ready={signal_summary['transition_gate'].get('promote_ready')} | "
                f"demote_ready={signal_summary['transition_gate'].get('demote_ready')}"
            ),
            "",
            "[Graph Context]",
            f"neighbors={graph['neighbor_count']}",
            "",
            "[Scope Health]",
            (
                f"level={health['health_label']} | active={health['total_active']} | "
                f"conflicts={health['num_conflicts']} | stale={health['num_stale']}"
            ),
            "",
            "[Why Not]",
        ]
    )
    if why_not:
        for item in why_not:
            lines.append(
                f"- {item.get('content')} | id={item.get('id')} | reason={item.get('reason')}"
            )
    else:
        lines.append("No suppressed alternatives for this query.")
    return "\n".join(lines)


def build_core_showcase_response(
    query: str,
    *,
    scope_type: str,
    scope_id: str,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if payload is None:
        return {
            "backend": "python",
            "query": query,
            "scope": {"scope_type": scope_type, "scope_id": scope_id},
            "result_count": 0,
            "showcase_text": "No core showcase result for this query.",
            "result": None,
        }
    return {
        "backend": "python",
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "result_count": 1,
        "showcase_text": render_core_showcase_text(payload),
        "result": payload,
    }
