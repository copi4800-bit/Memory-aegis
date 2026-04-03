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


def _summarize_topology(topology: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_count": topology.get("edge_count"),
        "average_weight": topology.get("average_weight"),
        "link_types": topology.get("link_types", []),
        "megarachne_topology_strength": _to_float(topology.get("megarachne_topology_strength")),
    }


def _summarize_health(health: dict[str, Any]) -> dict[str, Any]:
    return {
        "health_level": health.get("health_level"),
        "health_label": _health_label(health.get("health_level")),
        "total_active": health.get("total_active"),
        "num_conflicts": health.get("num_conflicts"),
        "num_stale": health.get("num_stale"),
    }


def _summarize_scope(scope_geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope_type": scope_geometry.get("scope_type"),
        "scope_id": scope_geometry.get("scope_id"),
        "include_global": scope_geometry.get("include_global"),
        "explicit_scope": scope_geometry.get("explicit_scope"),
        "argentinosaurus_scope_geometry": _to_float(
            scope_geometry.get("argentinosaurus_scope_geometry")
        ),
    }


def _summarize_storage(storage_footprint: dict[str, Any]) -> dict[str, Any]:
    prehistoric = storage_footprint.get("prehistoric_storage", {})
    titanoboa = prehistoric.get("titanoboa_index_locality", {})
    return {
        "allocated_bytes": storage_footprint.get("allocated_bytes"),
        "free_bytes": storage_footprint.get("free_bytes"),
        "deinosuchus_compaction_pressure": _to_float(
            prehistoric.get("deinosuchus_compaction_pressure")
        ),
        "orphaned_links": prehistoric.get("orphaned_links"),
        "titanoboa_index_locality": {
            "subject_count": titanoboa.get("subject_count"),
            "densest_cluster": titanoboa.get("densest_cluster"),
            "average_cluster_size": titanoboa.get("average_cluster_size"),
            "titanoboa_index_locality": _to_float(titanoboa.get("titanoboa_index_locality")),
        },
    }


def _summarize_consolidation(result: Any) -> dict[str, Any]:
    metadata = getattr(result.memory, "metadata", {}) or {}
    corrected_from = metadata.get("corrected_from", []) if isinstance(metadata, dict) else []
    return {
        "glyptodon_consolidation_shell": _to_float(
            metadata.get("glyptodon_consolidation_shell") if isinstance(metadata, dict) else 0.0
        ),
        "corrected_from_count": len(corrected_from),
    }


def _summarize_taxonomy(taxonomy: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject_count": taxonomy.get("subject_count"),
        "stable_subjects": taxonomy.get("stable_subjects"),
        "drift_candidates": taxonomy.get("drift_candidates"),
        "merge_recommendations": taxonomy.get("merge_recommendations", [])[:3],
        "taxonomy_health_band": taxonomy.get("taxonomy_health_band"),
        "oviraptor_taxonomy_order": _to_float(taxonomy.get("oviraptor_taxonomy_order")),
    }


def _summarize_write_intelligence(result: Any) -> dict[str, Any]:
    metadata = getattr(result.memory, "metadata", {}) or {}
    extraction = metadata.get("extraction_profile", {}) if isinstance(metadata, dict) else {}
    lane = metadata.get("lane_profile", {}) if isinstance(metadata, dict) else {}
    subject = metadata.get("subject_profile", {}) if isinstance(metadata, dict) else {}
    return {
        "dimetrodon": {
            "keyword_count": extraction.get("keyword_count"),
            "structural_markers": extraction.get("structural_markers"),
            "dimetrodon_feature_separation": _to_float(extraction.get("dimetrodon_feature_separation")),
        },
        "chalicotherium": {
            "predicted_lane": lane.get("predicted_lane"),
            "lane_scores": lane.get("lane_scores", {}),
            "chalicotherium_ecology_fit": _to_float(lane.get("chalicotherium_ecology_fit")),
        },
        "ammonite": {
            "raw_subject": subject.get("raw_subject"),
            "canonical_subject": subject.get("canonical_subject"),
            "segment_count": subject.get("segment_count"),
            "ammonite_spiral_stability": _to_float(subject.get("ammonite_spiral_stability")),
        },
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
    scope_geometry: dict[str, Any],
    evidence: list[dict[str, Any]],
    governance: dict[str, Any],
    neighbors: dict[str, Any],
    topology: dict[str, Any],
    taxonomy: dict[str, Any],
    v10_signals: dict[str, Any],
    transition_gate: dict[str, Any],
    health: dict[str, Any],
    storage_footprint: dict[str, Any],
    locale: str = "vi",
) -> dict[str, Any]:
    spotlight = build_spotlight_payload(result, locale=locale)
    scope_summary = _summarize_scope(scope_geometry)
    evidence_summary = _summarize_evidence(evidence)
    governance_summary = _summarize_governance(governance)
    signal_summary = _summarize_signals(v10_signals, transition_gate)
    graph_summary = _summarize_graph(neighbors)
    topology_summary = _summarize_topology(topology)
    health_summary = _summarize_health(health)
    storage_summary = _summarize_storage(storage_footprint)
    consolidation_summary = _summarize_consolidation(result)
    taxonomy_summary = _summarize_taxonomy(taxonomy)
    write_intelligence = _summarize_write_intelligence(result)
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
        "scope_summary": scope_summary,
        "paraceratherium_trace": spotlight["paraceratherium_trace"],
        "retrieval_predators": spotlight["retrieval_predators"],
        "why_not": spotlight["why_not"],
        "evidence_summary": evidence_summary,
        "governance_summary": governance_summary,
        "signal_summary": signal_summary,
        "graph_summary": graph_summary,
        "topology_summary": topology_summary,
        "health_summary": health_summary,
        "storage_summary": storage_summary,
        "consolidation_summary": consolidation_summary,
        "taxonomy_summary": taxonomy_summary,
        "write_intelligence": write_intelligence,
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
            "[Argentinosaurus Scope]",
            (
                f"type={payload['scope_summary'].get('scope_type')} | "
                f"id={payload['scope_summary'].get('scope_id')} | "
                f"include_global={payload['scope_summary'].get('include_global')} | "
                f"geometry={_to_float(payload['scope_summary'].get('argentinosaurus_scope_geometry')):.3f}"
            ),
            "",
            "[Paraceratherium Trace]",
            (
                f"headline={payload['paraceratherium_trace'].get('headline')} | "
                f"subject={payload['paraceratherium_trace'].get('subject_profile')} | "
                f"policy_steps={payload['paraceratherium_trace'].get('policy_step_count')} | "
                f"story={payload['paraceratherium_trace'].get('governance_story') or 'none'}"
            ),
            "",
            "[Paraceratherium Narrative]",
            payload["paraceratherium_trace"].get("decision_narrative") or "No governed narrative for this result.",
            "",
            "[Retrieval Predators]",
            (
                f"stage={payload['retrieval_predators'].get('retrieval_stage')} | "
                f"utahraptor={payload['retrieval_predators'].get('utahraptor_lexical_pursuit') or 'none'} | "
                f"utahraptor_band={payload['retrieval_predators'].get('utahraptor_band') or 'none'} | "
                f"basilosaurus={payload['retrieval_predators'].get('basilosaurus_semantic_echo') or 'none'} | "
                f"basilosaurus_band={payload['retrieval_predators'].get('basilosaurus_band') or 'none'} | "
                f"pterodactyl={payload['retrieval_predators'].get('pterodactyl_graph_overview') or 'none'}"
            ),
            "",
            "[Pterodactyl Flight]",
            (
                f"link_type={payload['retrieval_predators'].get('pterodactyl_route', {}).get('link_type') or 'none'} | "
                f"via_memory_id={payload['retrieval_predators'].get('pterodactyl_route', {}).get('via_memory_id') or 'none'} | "
                f"hops={payload['retrieval_predators'].get('pterodactyl_route', {}).get('hops') or 0}"
            ),
            payload["retrieval_predators"].get("pterodactyl_flight_story") or "No graph flight story for this result.",
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
            "[Megarachne Topology]",
            (
                f"strength={_to_float(payload['topology_summary'].get('megarachne_topology_strength')):.3f} | "
                f"edges={payload['topology_summary'].get('edge_count')} | "
                f"avg_weight={_to_float(payload['topology_summary'].get('average_weight')):.3f} | "
                f"link_types={', '.join(payload['topology_summary'].get('link_types', [])) or 'none'}"
            ),
            "",
            "[Scope Health]",
            (
                f"level={health['health_label']} | active={health['total_active']} | "
                f"conflicts={health['num_conflicts']} | stale={health['num_stale']}"
            ),
            "",
            "[Prehistoric Storage]",
            (
                f"deinosuchus={_to_float(payload['storage_summary'].get('deinosuchus_compaction_pressure')):.3f} | "
                f"orphans={payload['storage_summary'].get('orphaned_links')} | "
                f"titanoboa={_to_float(payload['storage_summary']['titanoboa_index_locality'].get('titanoboa_index_locality')):.3f} | "
                f"cluster={payload['storage_summary']['titanoboa_index_locality'].get('densest_cluster')}"
            ),
            "",
            "[Glyptodon Consolidation]",
            (
                f"shell={_to_float(payload['consolidation_summary'].get('glyptodon_consolidation_shell')):.3f} | "
                f"corrected_from={payload['consolidation_summary'].get('corrected_from_count')}"
            ),
            "",
            "[Dimetrodon Extraction]",
            (
                f"separation={_to_float(payload['write_intelligence']['dimetrodon'].get('dimetrodon_feature_separation')):.3f} | "
                f"keywords={payload['write_intelligence']['dimetrodon'].get('keyword_count')} | "
                f"markers={payload['write_intelligence']['dimetrodon'].get('structural_markers')}"
            ),
            "",
            "[Chalicotherium Lane]",
            (
                f"lane={payload['write_intelligence']['chalicotherium'].get('predicted_lane')} | "
                f"fit={_to_float(payload['write_intelligence']['chalicotherium'].get('chalicotherium_ecology_fit')):.3f}"
            ),
            "",
            "[Ammonite Subject]",
            (
                f"raw={payload['write_intelligence']['ammonite'].get('raw_subject') or 'none'} | "
                f"canonical={payload['write_intelligence']['ammonite'].get('canonical_subject') or 'none'} | "
                f"segments={payload['write_intelligence']['ammonite'].get('segment_count') or 0} | "
                f"stability={_to_float(payload['write_intelligence']['ammonite'].get('ammonite_spiral_stability')):.3f}"
            ),
            "",
            "[Oviraptor Taxonomy]",
            (
                f"order={_to_float(payload['taxonomy_summary'].get('oviraptor_taxonomy_order')):.3f} | "
                f"subjects={payload['taxonomy_summary'].get('subject_count')} | "
                f"stable={payload['taxonomy_summary'].get('stable_subjects')} | "
                f"drift={payload['taxonomy_summary'].get('drift_candidates')} | "
                f"band={payload['taxonomy_summary'].get('taxonomy_health_band') or 'unknown'}"
            ),
            "",
            "[Oviraptor Merge Guidance]",
        ]
    )
    recommendations = payload["taxonomy_summary"].get("merge_recommendations", [])
    if recommendations:
        for item in recommendations:
            lines.append(
                f"- {item.get('subject_1')} <-> {item.get('subject_2')} | confidence={_to_float(item.get('confidence')):.3f}"
            )
    else:
        lines.append("No merge guidance for this scope.")
    lines.extend(
        [
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
