from __future__ import annotations

from typing import Any


DEFAULT_OPERATION_ORDER = [
    "memory_remember",
    "memory_recall",
    "memory_correct",
    "memory_forget",
    "memory_setup",
    "memory_stats",
    "memory_profile",
]

ADVANCED_OPERATION_ORDER = [
    "memory_search",
    "memory_context_pack",
    "memory_conflict_prompt",
    "memory_conflict_resolve",
    "memory_link_store",
    "memory_link_neighbors",
    "memory_get",
    "memory_scope_policy",
    "memory_sync_export",
    "memory_sync_preview",
    "memory_sync_import",
    "memory_doctor",
    "memory_clean",
    "memory_taxonomy_clean",
    "memory_rebuild",
    "memory_scan",
    "memory_visualize",
    "memory_governance",
    "memory_background_plan",
    "memory_background_shadow",
    "memory_background_apply",
    "memory_background_rollback",
    "memory_vector_inspect",
    "memory_evidence_artifacts",
    "memory_storage_footprint",
    "memory_storage_compact",
    "memory_backup_upload",
    "memory_backup_list",
    "memory_backup_preview",
    "memory_backup_download",
    "memory_surface",
]

PUBLIC_OPERATION_ORDER = [
    "memory_store",
    "memory_search",
    "memory_conflict_prompt",
    "memory_conflict_resolve",
    "memory_remember",
    "memory_recall",
    "memory_correct",
    "memory_forget",
    "memory_setup",
    "memory_context_pack",
    "memory_link_store",
    "memory_link_neighbors",
    "memory_get",
    "memory_profile",
    "memory_scope_policy",
    "memory_sync_export",
    "memory_sync_preview",
    "memory_sync_import",
    "memory_stats",
    "memory_doctor",
    "memory_clean",
    "memory_taxonomy_clean",
    "memory_rebuild",
    "memory_scan",
    "memory_visualize",
    "memory_governance",
    "memory_background_plan",
    "memory_background_shadow",
    "memory_background_apply",
    "memory_background_rollback",
    "memory_vector_inspect",
    "memory_evidence_artifacts",
    "memory_storage_footprint",
    "memory_storage_compact",
    "memory_backup_upload",
    "memory_backup_list",
    "memory_backup_preview",
    "memory_backup_download",
]

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "memory_store": {"audience": "public", "group": "public", "owner": "python_runtime"},
    "memory_search": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_conflict_prompt": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_conflict_resolve": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_remember": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_recall": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_correct": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_forget": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_setup": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_context_pack": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_link_store": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_link_neighbors": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_get": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_profile": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_scope_policy": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_sync_export": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_sync_preview": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_sync_import": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_stats": {"audience": "default", "group": "public", "owner": "python_runtime"},
    "memory_doctor": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_clean": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_taxonomy_clean": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_rebuild": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_scan": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_visualize": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_governance": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_background_plan": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_background_shadow": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_background_apply": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_background_rollback": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_vector_inspect": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_evidence_artifacts": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_storage_footprint": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_storage_compact": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_backup_upload": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_backup_list": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_backup_preview": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_backup_download": {"audience": "advanced", "group": "public", "owner": "python_runtime"},
    "memory_surface": {"audience": "advanced", "group": "advanced_only", "owner": "python_runtime"},
}

for tool_name, metadata in TOOL_REGISTRY.items():
    metadata.setdefault("host_bridge", f"tool:{tool_name}")

TOOL_REGISTRY["memory_stats"]["host_bridge"] = "tool:memory_status"
TOOL_REGISTRY["memory_setup"]["host_bridge"] = "cli:onboarding"


def operations_for_audience(audience: str) -> list[str]:
    order = {
        "default": DEFAULT_OPERATION_ORDER,
        "advanced": ADVANCED_OPERATION_ORDER,
    }.get(audience, [])
    return [name for name in order if name in TOOL_REGISTRY]


def public_operations() -> list[str]:
    return [name for name in PUBLIC_OPERATION_ORDER if name in TOOL_REGISTRY]


def registry_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())


def host_bridge_for_tool(tool_name: str) -> str:
    metadata = TOOL_REGISTRY.get(tool_name)
    if metadata is None:
        raise KeyError(tool_name)
    return str(metadata["host_bridge"])


def adapter_tool_targets() -> list[str]:
    targets = {
        bridge.split(":", 1)[1]
        for bridge in (host_bridge_for_tool(name) for name in TOOL_REGISTRY)
        if bridge.startswith("tool:")
    }
    return sorted(targets)
