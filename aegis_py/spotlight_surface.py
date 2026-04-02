from __future__ import annotations

import json
from typing import Any, Iterable

from .surface import serialize_search_result


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
