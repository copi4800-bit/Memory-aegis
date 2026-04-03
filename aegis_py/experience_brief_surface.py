from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _slice_nonempty_lines(text: str, *, limit: int) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:limit]


def _build_runtime_snapshot(doctor: dict[str, Any]) -> dict[str, Any]:
    storage = doctor.get("storage", {})
    counts = doctor.get("counts", {})
    return {
        "health_state": doctor.get("health_state"),
        "memory_count": counts.get("memories", 0),
        "open_conflicts": counts.get("open_conflicts", 0),
        "historical_rows": storage.get("historical_rows", 0),
        "smilodon_peak_retirement_pressure": _to_float(storage.get("smilodon_peak_retirement_pressure")),
        "issues": doctor.get("issues", []),
    }


def _build_compressed_snapshot(compressed_status: dict[str, Any]) -> dict[str, Any]:
    compressed = compressed_status.get("compressed_tier", {})
    coverage = compressed.get("coverage", {})
    readiness = compressed.get("readiness", {})
    return {
        "coverage_rate": _to_float(coverage.get("coverage_rate")),
        "covered_memories": coverage.get("covered_memories", 0),
        "memory_count": coverage.get("memory_count", 0),
        "tier_counts": coverage.get("tier_counts", {}),
        "passed": bool(readiness.get("passed")),
        "failures": readiness.get("failures", []),
        "summary_metrics": readiness.get("summary_metrics", {}),
    }


def _build_next_actions(
    *,
    showcase_payload: dict[str, Any],
    runtime_snapshot: dict[str, Any],
    compressed_snapshot: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    health_level = showcase_payload.get("health_summary", {}).get("health_label")
    why_not = showcase_payload.get("why_not", [])
    if compressed_snapshot["passed"]:
        actions.append("Compressed retrieval tier is ready; scale candidate generation without touching truth logic.")
    else:
        actions.append("Rerun compressed-tier benchmark and gate before leaning on the retrieval substrate.")
    if runtime_snapshot["open_conflicts"] > 0:
        actions.append("Resolve active conflicts so the current-truth path stays easy to trust.")
    elif why_not:
        actions.append("Use the suppressed alternatives section to explain to users why older facts lost.")
    if runtime_snapshot["smilodon_peak_retirement_pressure"] >= 0.7:
        actions.append("Run compaction or review archival policy before long-horizon storage gets noisy.")
    elif health_level == "Good":
        actions.append("Current health is stable; this is a good moment to show the product flow, not just the engine.")
    if showcase_payload.get("truth_state", {}).get("truth_role") != "winner":
        actions.append("Promote the strongest governed candidate before presenting this scope as settled truth.")
    return actions[:4]


def build_experience_brief_payload(
    *,
    query: str,
    scope_type: str,
    scope_id: str,
    showcase_response: dict[str, Any],
    profile_text: str,
    doctor: dict[str, Any],
    doctor_summary: str,
    compressed_status: dict[str, Any],
) -> dict[str, Any]:
    showcase_payload = showcase_response.get("result")
    if showcase_payload is None:
        return {
            "query": query,
            "scope": {"scope_type": scope_type, "scope_id": scope_id},
            "available": False,
            "brief_text": "No experience brief is available because the scope has no governed showcase result yet.",
            "result": None,
        }

    runtime_snapshot = _build_runtime_snapshot(doctor)
    compressed_snapshot = _build_compressed_snapshot(compressed_status)
    next_actions = _build_next_actions(
        showcase_payload=showcase_payload,
        runtime_snapshot=runtime_snapshot,
        compressed_snapshot=compressed_snapshot,
    )
    payload = {
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "hero": {
            "label": showcase_payload["verdict"]["label"],
            "selected_memory": showcase_payload["selected_memory"],
            "governance_status": showcase_payload["truth_state"].get("governance_status"),
            "truth_role": showcase_payload["truth_state"].get("truth_role"),
            "trust_score": showcase_payload["verdict"].get("trust_score"),
            "readiness_score": showcase_payload["verdict"].get("readiness_score"),
        },
        "executive_summary": showcase_payload.get("executive_summary", []),
        "human_reason": showcase_payload.get("human_reason"),
        "why_not": showcase_payload.get("why_not", []),
        "profile_snapshot": _slice_nonempty_lines(profile_text, limit=8),
        "doctor_snapshot": _slice_nonempty_lines(doctor_summary, limit=8),
        "runtime_snapshot": runtime_snapshot,
        "compressed_snapshot": compressed_snapshot,
        "showcase": showcase_payload,
        "next_actions": next_actions,
    }
    payload["brief_text"] = render_experience_brief_text(payload)
    return {
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "available": True,
        "brief_text": payload["brief_text"],
        "result": payload,
    }


def render_experience_brief_text(payload: dict[str, Any]) -> str:
    hero = payload["hero"]
    runtime = payload["runtime_snapshot"]
    compressed = payload["compressed_snapshot"]
    lines = [
        "[TruthKeep Experience Brief]",
        (
            f"{hero['label']} | role={hero['truth_role']} | status={hero['governance_status']} | "
            f"trust={_to_float(hero['trust_score']):.3f} | readiness={_to_float(hero['readiness_score']):.3f}"
        ),
        "",
        "[What TruthKeep Believes]",
        hero["selected_memory"],
        "",
        "[Why It Believes This]",
        payload["human_reason"] or "No governed reason available.",
        "",
        "[Executive Summary]",
    ]
    lines.extend(f"- {item}" for item in payload["executive_summary"])
    lines.extend(
        [
            "",
            "[Profile Snapshot]",
        ]
    )
    lines.extend(f"- {item}" for item in payload["profile_snapshot"] or ["No profile snapshot available."])
    lines.extend(
        [
            "",
            "[Runtime Snapshot]",
            (
                f"health_state={runtime['health_state']} | memories={runtime['memory_count']} | "
                f"open_conflicts={runtime['open_conflicts']} | historical_rows={runtime['historical_rows']} | "
                f"smilodon={runtime['smilodon_peak_retirement_pressure']:.3f}"
            ),
            "",
            "[Compressed Tier]",
            (
                f"passed={compressed['passed']} | coverage={compressed['coverage_rate']:.3f} | "
                f"covered={compressed['covered_memories']}/{compressed['memory_count']} | "
                f"tiers={compressed['tier_counts']}"
            ),
            "",
            "[Next Actions]",
        ]
    )
    lines.extend(f"- {item}" for item in payload["next_actions"] or ["No immediate action required."])
    lines.extend(["", "[Suppressed Alternatives]"])
    if payload["why_not"]:
        for item in payload["why_not"]:
            lines.append(f"- {item.get('content')} | reason={item.get('reason')}")
    else:
        lines.append("No suppressed alternatives for this query.")
    return "\n".join(lines)
