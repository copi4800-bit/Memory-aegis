from __future__ import annotations

import json
from typing import Any, Iterable

from .retrieval.models import SearchResult
from .tool_registry import TOOL_REGISTRY, operations_for_audience, public_operations
from .ux.schema import unify_v10_signals
from .ux.translator import generate_human_reason
from .v10_scoring.translator import FaithfulRenderer

RETRIEVAL_MODES = {"fast", "explain"}

DEFAULT_OPERATIONS = operations_for_audience("default")
ADVANCED_OPERATIONS = operations_for_audience("advanced")
PUBLIC_OPERATIONS = public_operations()

ORDINARY_OPERATIONS = [
    "memory_remember",
    "memory_recall",
    "memory_correct",
    "memory_profile",
    "memory_stats",
]

OPERATOR_OPERATIONS = [
    "memory_workflow_shell",
    "memory_truth_transition_timeline",
    "memory_spotlight",
    "memory_core_showcase",
    "memory_governance",
    "memory_v10_field_snapshot",
    "memory_doctor",
    "memory_rebuild",
    "memory_scan",
    "memory_storage_footprint",
    "memory_storage_compact",
    "memory_backup_upload",
    "memory_backup_preview",
    "memory_backup_download",
]

# Global v10 Renderer
V10_RENDERER = FaithfulRenderer()


def normalize_retrieval_mode(retrieval_mode: str | None) -> str:
    mode = (retrieval_mode or "explain").strip().lower()
    if mode not in RETRIEVAL_MODES:
        raise ValueError(f"Unsupported retrieval mode: {retrieval_mode}")
    return mode


def build_public_surface(*, runtime_version: str) -> dict[str, Any]:
    return {
        "backend": "python",
        "surface_version": 1,
        "engine": {
            "name": "Aegis Python",
            "runtime_version": runtime_version,
            "local_first": True,
            "default_storage": "sqlite",
            "health_states": ["HEALTHY", "DEGRADED_SYNC", "BROKEN"],
        },
        "public_contract": {
            "owners": {
                "aegis_py.app": "canonical memory semantics and result shapes",
                "aegis_py.surface": "public contract assembly and context-pack payload shaping",
                "aegis_py.tool_registry": "canonical operation groups and runtime-owned tool metadata",
                "aegis_py.operations": "backup, restore, and scope-policy operational workflows",
                "aegis_py.mcp.server": "tool-oriented adapter over the Python contract",
                "src/python-adapter.ts": "TypeScript bridge to Python-owned tools",
                "index.ts": "OpenClaw host adapter that must not own memory-domain semantics",
            },
            "operations": PUBLIC_OPERATIONS,
            "guarantees": [
                "local_first_baseline",
                "explicit_scope_fields",
                "provenance_preserved",
                "conflict_visibility",
                "backup_restore_auditability",
                "governed_background_mutation_controls",
                "sqlite_link_source_of_truth",
                "bounded_health_state_reporting",
            ],
            "non_goals": [
                "host-owned-memory-semantics",
                "mandatory-cloud-service",
                "direct-storage-helper-coupling-for-external-hosts",
                "graph-native-source-of-truth",
            ],
        },
        "consumer_contract": {
            "default_operations": DEFAULT_OPERATIONS,
            "advanced_operations": ADVANCED_OPERATIONS,
            "registry_size": len(TOOL_REGISTRY),
            "default_scope": {
                "scope_type": "agent",
                "scope_id": "default",
            },
            "default_provenance": {
                "source_kind": "conversation",
                "source_ref": "consumer://default",
            },
            "guided_hygiene": {
                "ordinary_use": "background_or_triggered",
                "operator_commands_optional": True,
            },
            "ordinary_lane": {
                "description": "The narrow daily path for normal use.",
                "operations": ORDINARY_OPERATIONS,
                "workflow": ["remember", "inspect", "correct", "verify"],
            },
            "operator_lane": {
                "description": "Inspection and maintenance tools for advanced use.",
                "operations": OPERATOR_OPERATIONS,
                "default_hidden": True,
            },
        },
        "service_boundary": {
            "owner": "python",
            "deployment_model": "local_sidecar_process",
            "preferred_transport": "mcp_tool_process",
            "supported_transports": [
                "mcp_tool_process",
                "cli_json_process",
            ],
            "startup_contract": {
                "service_info_command": "PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v10 python -m aegis_py.mcp.server --service-info",
                "startup_probe_command": "PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v10 python -m aegis_py.mcp.server --startup-probe",
                "tool_invocation_pattern": "PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v10 python -m aegis_py.mcp.server --tool <tool-name> --args-json '{...}'",
            },
            "thin_host_guidance": [
                "spawn_local_python_process",
                "read_json_service_descriptor",
                "gate_on_startup_probe_before_tool_calls",
                "treat_python_as_semantic_owner",
            ],
        },
        "health_contract": {
            "states": {
                "HEALTHY": "Local runtime is available and no degraded optional-service issues are active.",
                "DEGRADED_SYNC": "Local runtime remains usable, but sync-adjacent or deferred workflows are degraded.",
                "BROKEN": "Core local runtime or storage is unavailable for safe operation.",
            },
            "capabilities": [
                "local_store",
                "local_search",
                "local_status",
                "backup_restore",
                "optional_sync",
            ],
        },
    }


def serialize_search_results(
    results: Iterable[SearchResult],
    *,
    retrieval_mode: str = "explain",
    locale: str = "vi",
) -> list[dict[str, Any]]:
    mode = normalize_retrieval_mode(retrieval_mode)
    return [serialize_search_result(result, retrieval_mode=mode, locale=locale) for result in results]


def serialize_search_result(
    result: SearchResult,
    *,
    retrieval_mode: str = "explain",
    locale: str = "vi",
) -> dict[str, Any]:
    mode = normalize_retrieval_mode(retrieval_mode)
    v10_state = result.v10_core_signals or (result.memory.metadata.get("v10_state", {}) if isinstance(result.memory.metadata, dict) else {})

    v10_trace = getattr(result, "v10_trace", None)
    v10_payload = {}
    if v10_trace:
        detail_level = "standard"
        if mode == "fast":
            detail_level = "standard"
        elif mode == "explain":
            detail_level = "explain"
        elif mode == "deep":
            detail_level = "deep"

        human_reason = V10_RENDERER.render(v10_trace, locale=locale, detail=detail_level)
        v10_payload = {
            "v10_score": getattr(result, "v10_score", 0.0),
            "decisive_factor": v10_trace.decisive_factor,
            "base_score": v10_trace.base_score,
            "judge_delta": v10_trace.judge_delta,
            "life_delta": v10_trace.life_delta,
            "hard_constraints_delta": getattr(v10_trace, "hard_constraints_delta", 0.0),
            "factors": v10_trace.factors,
        }
    else:
        human_reason = generate_human_reason(v10_state, locale=locale)

    v10_decision = getattr(result, "v10_decision", None)
    v10_payload = {}
    if v10_decision:
        v10_payload = {
            "truth_role": v10_decision.truth_role.value,
            "governance_status": v10_decision.governance_status.value,
            "policy_trace": v10_decision.policy_trace,
            "admissible": v10_decision.admissible,
            "decision_reason": v10_decision.decision_reason,
        }

    payload = {
        "memory": {
            "id": result.memory.id,
            "type": result.memory.type,
            "scope_type": result.memory.scope_type,
            "scope_id": result.memory.scope_id,
            "content": result.memory.content,
            "summary": result.memory.summary,
            "subject": result.memory.subject,
            "source_kind": result.memory.source_kind,
            "source_ref": result.memory.source_ref,
            "status": result.memory.status,
            "memory_state": getattr(result.memory, "memory_state", None),
            "score_profile": result.memory.metadata.get("score_profile", {}) if isinstance(result.memory.metadata, dict) else {},
        },
        "score": result.score,
        "reason": result.reason,
        "provenance": result.provenance,
        "conflict_status": result.conflict_status,
        "human_reason": human_reason,
        "v10_audit": v10_payload,
        "v10_governance": v10_payload,
        "unified_signals": unify_v10_signals(v10_state, locale=locale),
        "suppressed_candidates": result.suppressed_candidates,
        "hybrid_fusion": getattr(result, "hybrid_fusion", None),
    }
    if v10_payload:
        payload.update(v10_payload)
    if mode == "fast":
        payload["result_mode"] = "fast"
        return payload

    payload.update(
        {
            "result_mode": "explain",
            "trust_state": result.trust_state,
            "trust_reason": result.trust_reason,
            "reasons": result.reasons,
            "retrieval_stage": result.retrieval_stage,
            "relation_via_subject": result.relation_via_subject,
            "relation_via_link_type": result.relation_via_link_type,
            "relation_via_memory_id": result.relation_via_memory_id,
            "relation_via_link_metadata": result.relation_via_link_metadata,
            "relation_via_hops": result.relation_via_hops,
        }
    )
    return payload


def serialize_conflict_prompt(prompt: dict[str, Any]) -> dict[str, Any]:
    return {
        "conflict_id": prompt["conflict_id"],
        "classification": prompt["classification"],
        "conflict_type": prompt["conflict_type"],
        "subject": prompt["subject"],
        "score": prompt["score"],
        "reason": prompt["reason"],
        "decision": prompt.get("decision"),
        "decision_reason": prompt.get("decision_reason"),
        "decision_policy": prompt.get("decision_policy"),
        "status": prompt["status"],
        "resolution": prompt["resolution"],
        "same_scope": prompt["same_scope"],
        "recommended_action": prompt["recommended_action"],
        "actions": prompt["actions"],
        "memories": prompt["memories"],
    }


def build_context_pack(
    *,
    query: str,
    scope_type: str,
    scope_id: str,
    results: list[SearchResult],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    mode = normalize_retrieval_mode("explain")
    lexical_hits = sum(1 for result in results if result.retrieval_stage == "lexical")
    expanded_hits = sum(1 for result in results if result.retrieval_stage != "lexical")
    stage_counts = {
        "lexical": lexical_hits,
        "vector": sum(1 for result in results if result.retrieval_stage == "vector"),
        "link_expansion": sum(1 for result in results if result.retrieval_stage == "link_expansion"),
        "multi_hop_link_expansion": sum(1 for result in results if result.retrieval_stage == "multi_hop_link_expansion"),
        "entity_expansion": sum(1 for result in results if result.retrieval_stage == "entity_expansion"),
        "subject_expansion": sum(1 for result in results if result.retrieval_stage == "subject_expansion"),
    }
    return {
        "backend": "python",
        "query": query,
        "scope": {"scope_type": scope_type, "scope_id": scope_id},
        "boundary": boundary,
        "strategy": {
            "name": "mammoth_lexical_first",
            "steps": [
                "lexical_recall",
                "explicit_link_expansion",
                "bounded_multi_hop_link_expansion",
                "entity_structure_expansion",
                "subject_relationship_expansion",
                "explainable_context_pack",
            ],
        },
        "counts": {
            "results": len(results),
            "lexical_hits": lexical_hits,
            "expanded_hits": expanded_hits,
            "stage_counts": stage_counts,
            "payload_bytes": len(json.dumps(serialize_search_results(results, retrieval_mode=mode), ensure_ascii=False)),
        },
        "result_mode": mode,
        "results": serialize_search_results(results, retrieval_mode=mode),
        "trust_counts": {
            "strong": sum(1 for result in results if result.trust_state == "strong"),
            "weak": sum(1 for result in results if result.trust_state == "weak"),
            "uncertain": sum(1 for result in results if result.trust_state == "uncertain"),
            "conflicting": sum(1 for result in results if result.trust_state == "conflicting"),
        },
    }

