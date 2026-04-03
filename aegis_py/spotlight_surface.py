from __future__ import annotations

import json
from typing import Any, Iterable

from .surface import serialize_search_result


def _build_paraceratherium_trace(payload: dict[str, Any]) -> dict[str, Any]:
    governance = payload.get("v10_governance", {}) or {}
    memory = payload.get("memory", {}) or {}
    score_profile = memory.get("score_profile", {}) or {}
    policy_trace = governance.get("policy_trace", []) or []
    governance_story = payload.get("human_reason")
    if governance.get("truth_role") == "winner" and governance.get("governance_status") == "active":
        decision_narrative = "The governed winner stayed active and cleared the current-truth path."
    elif governance.get("governance_status") == "suppressed":
        decision_narrative = "The candidate was suppressed by governance before it could become current truth."
    else:
        decision_narrative = governance_story or "The memory cleared a bounded governed retrieval path."
    return {
        "headline": (
            f"{governance.get('truth_role') or 'unknown'} / "
            f"{governance.get('governance_status') or 'unknown'}"
        ),
        "policy_step_count": len(policy_trace),
        "policy_trace": policy_trace[:5],
        "governance_story": governance_story,
        "decision_narrative": decision_narrative,
        "decisive_signal": {
            "dunkleosteus_decisive_pressure": score_profile.get("dunkleosteus_decisive_pressure"),
            "thylacoleo_conflict_sentinel_score": score_profile.get("thylacoleo_conflict_sentinel_score"),
            "meganeura_capture_span": score_profile.get("meganeura_capture_span"),
        },
        "subject_profile": memory.get("subject"),
    }


def _build_retrieval_predators(payload: dict[str, Any]) -> dict[str, Any]:
    reasons = payload.get("reasons", []) or []
    utahraptor = next(
        (reason.split(":", 1)[1] for reason in reasons if reason.startswith("utahraptor_lexical_pursuit:")),
        None,
    )
    basilosaurus = next(
        (reason.split(":", 1)[1] for reason in reasons if reason.startswith("basilosaurus_semantic_echo:")),
        None,
    )
    pterodactyl = next(
        (reason.split(":", 1)[1] for reason in reasons if reason.startswith("pterodactyl_graph_overview:")),
        None,
    )
    memory = payload.get("memory", {}) or {}
    utahraptor_ratio = None
    utahraptor_band = None
    basilosaurus_band = None
    if utahraptor is not None:
        try:
            utahraptor_ratio = float(utahraptor)
        except (TypeError, ValueError):
            utahraptor_ratio = None
    if utahraptor_ratio is not None:
        if utahraptor_ratio >= 0.85:
            utahraptor_band = "locked"
        elif utahraptor_ratio >= 0.55:
            utahraptor_band = "tracking"
        else:
            utahraptor_band = "glancing"
    semantic_term_count = 0
    if basilosaurus:
        semantic_term_count = len([item for item in basilosaurus.split(",") if item.strip()])
        if semantic_term_count >= 3:
            basilosaurus_band = "resonant"
        elif semantic_term_count >= 1:
            basilosaurus_band = "audible"
        else:
            basilosaurus_band = "faint"
    pterodactyl_route = {
        "link_type": payload.get("relation_via_link_type"),
        "via_memory_id": payload.get("relation_via_memory_id"),
        "hops": payload.get("relation_via_hops"),
    }
    if pterodactyl:
        flight_story = (
            f"Graph flight entered through {pterodactyl_route['link_type'] or 'unknown'} links "
            f"over {pterodactyl_route['hops'] or 0} hop(s)."
        )
    else:
        flight_story = "No graph flight was needed for this retrieval."
    return {
        "retrieval_stage": memory.get("retrieval_stage") or payload.get("retrieval_stage"),
        "utahraptor_lexical_pursuit": utahraptor,
        "utahraptor_ratio": utahraptor_ratio,
        "utahraptor_band": utahraptor_band,
        "basilosaurus_semantic_echo": basilosaurus,
        "basilosaurus_band": basilosaurus_band,
        "basilosaurus_term_count": semantic_term_count,
        "pterodactyl_graph_overview": pterodactyl,
        "pterodactyl_route": pterodactyl_route,
        "pterodactyl_flight_story": flight_story,
        "hybrid_fusion": payload.get("hybrid_fusion") or {},
    }


def build_spotlight_payload(result: Any, *, locale: str = "vi") -> dict[str, Any]:
    payload = serialize_search_result(result, retrieval_mode="explain", locale=locale)
    return {
        "selected_memory": payload["memory"]["content"],
        "human_reason": payload["human_reason"],
        "truth_state": {
            "governance_status": payload["v10_governance"].get("governance_status"),
            "truth_role": payload["v10_governance"].get("truth_role"),
            "policy_trace": payload["v10_governance"].get("policy_trace", []),
        },
        "paraceratherium_trace": _build_paraceratherium_trace(payload),
        "retrieval_predators": _build_retrieval_predators(payload),
        "why_not": payload.get("suppressed_candidates", []),
    }


def render_spotlight_text(result: Any, *, locale: str = "vi") -> str:
    spotlight = build_spotlight_payload(result, locale=locale)
    lines = [
        "[Selected Result]",
        spotlight["selected_memory"],
        "",
        "[Why This]",
        spotlight["human_reason"],
        "",
        "[Truth State]",
        json.dumps(spotlight["truth_state"], indent=2, ensure_ascii=False),
        "",
        "[Paraceratherium Trace]",
        json.dumps(spotlight["paraceratherium_trace"], indent=2, ensure_ascii=False),
        "",
        "[Retrieval Predators]",
        json.dumps(spotlight["retrieval_predators"], indent=2, ensure_ascii=False),
        "",
        "[Why Not]",
    ]
    if spotlight["why_not"]:
        lines.append(json.dumps(spotlight["why_not"], indent=2, ensure_ascii=False))
    else:
        lines.append("No suppressed alternatives for this query.")
    return "\n".join(lines)


def summarize_spotlight_results(results: Iterable[Any], *, locale: str = "vi") -> list[dict[str, Any]]:
    return [build_spotlight_payload(result, locale=locale) for result in results]


def build_spotlight_response(
    query: str,
    results: Iterable[Any],
    *,
    scope_type: str,
    scope_id: str,
    locale: str = "vi",
) -> dict[str, Any]:
    materialized = list(results)
    spotlight_results = summarize_spotlight_results(materialized, locale=locale)
    top_text = render_spotlight_text(materialized[0], locale=locale) if materialized else "No spotlight result for this query."
    return {
        "backend": "python",
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "result_count": len(spotlight_results),
        "spotlight_text": top_text,
        "results": spotlight_results,
    }
