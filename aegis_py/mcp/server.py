from __future__ import annotations

import argparse
import json
import os
from typing import Any

from aegis_py.app import AegisApp
from aegis_py.tool_registry import TOOL_REGISTRY


class AegisMCPServer:
    """Compact MCP-oriented wrapper around the Python Aegis core."""

    def __init__(self, db_path: str | None = None):
        final_db_path = db_path or os.environ.get("AEGIS_DB_PATH") or "memory_aegis.db"
        self.app = AegisApp(final_db_path)

    def memory_store(
        self,
        m_type: str | None,
        content: str,
        subject: str | None = None,
        *,
        scope_type: str = "agent",
        scope_id: str = "default",
        source_kind: str = "manual",
        source_ref: str | None = None,
        summary: str | None = None,
        session_id: str | None = None,
    ) -> str:
        memory = self.app.put_memory(
            content,
            type=m_type,
            scope_type=scope_type,
            scope_id=scope_id,
            session_id=session_id,
            source_kind=source_kind,
            source_ref=source_ref,
            subject=subject,
            summary=summary,
        )
        if memory is None:
            return "No memory stored."
        stored_type = memory.type if memory is not None else m_type
        return f"Stored {stored_type} memory {memory.id}."

    def memory_search(
        self,
        text: str,
        *,
        limit: int = 5,
        scope_type: str | None = None,
        scope_id: str | None = None,
        include_global: bool = True,
        semantic: bool = False,
        semantic_model: str | None = None,
        retrieval_mode: str = "explain",
    ) -> str:
        payload = self.app.search_payload(
            text,
            scope_type=scope_type,
            scope_id=scope_id,
            limit=limit,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
            retrieval_mode=retrieval_mode,
        )
        if not payload:
            return self._to_json([])
        return self._to_json(payload)

    def memory_conflict_prompt(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        subject: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.conflict_resolution_prompts(
                scope_type=scope_type,
                scope_id=scope_id,
                subject=subject,
            )
        )

    def memory_conflict_resolve(
        self,
        conflict_id: str,
        *,
        action: str,
        rationale: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.resolve_conflict(
                conflict_id,
                action=action,
                rationale=rationale,
            )
        )

    def memory_context_pack(
        self,
        text: str,
        *,
        limit: int = 5,
        scope_type: str | None = None,
        scope_id: str | None = None,
        include_global: bool = True,
        semantic: bool = False,
        semantic_model: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.search_context_pack(
                text,
                scope_type=scope_type,
                scope_id=scope_id,
                limit=limit,
                include_global=include_global,
                semantic=semantic,
                semantic_model=semantic_model,
            )
        )

    def memory_link_store(
        self,
        source_id: str,
        target_id: str,
        *,
        link_type: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return self._to_json(
            self.app.link_memories(
                source_id,
                target_id,
                link_type=link_type,
                weight=weight,
                metadata=metadata,
            )
        )

    def memory_link_neighbors(self, memory_id: str, *, limit: int = 10) -> str:
        return self._to_json(self.app.memory_neighbors(memory_id, limit=limit))

    def memory_get(
        self,
        rel_path: str,
        *,
        from_line: int = 0,
        lines: int | None = None,
        workspace_dir: str | None = None,
    ) -> str:
        payload = self.app.read_memory(
            rel_path,
            from_line=from_line,
            line_count=lines,
            workspace_dir=workspace_dir,
        )
        return self._to_json(payload)

    def memory_status(self) -> str:
        return json.dumps(self.app.status(), indent=2, ensure_ascii=False)

    def memory_stats(self) -> str:
        return self.memory_status()

    def memory_doctor(self, workspace_dir: str | None = None) -> str:
        return self._to_json(self.app.doctor(workspace_dir=workspace_dir))

    def memory_clean(self, subject: str | None = None) -> str:
        return json.dumps(self.app.clean(subject), indent=2, ensure_ascii=False)

    def memory_export(self, format_type: str = "json") -> str:
        return self.app.export_memories(format_type)

    def memory_backup_upload(self, mode: str = "snapshot", workspace_dir: str | None = None) -> str:
        return self._to_json(self.app.create_backup(mode=mode, workspace_dir=workspace_dir))

    def memory_backup_list(self, workspace_dir: str | None = None) -> str:
        return self._to_json(self.app.list_backups(workspace_dir=workspace_dir))

    def memory_backup_preview(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.preview_restore(snapshot_path, scope_type=scope_type, scope_id=scope_id)
        )

    def memory_backup_download(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.restore_backup(snapshot_path, scope_type=scope_type, scope_id=scope_id)
        )

    def memory_profile(self, scope_id: str = "default", scope_type: str = "agent") -> str:
        return self.app.render_profile(scope_id=scope_id, scope_type=scope_type)

    def memory_setup(self, workspace_dir: str | None = None) -> str:
        return self._to_json(self.app.onboarding(workspace_dir=workspace_dir))

    def memory_surface(self) -> str:
        return self._to_json(self.app.public_surface())

    def memory_registry(self) -> str:
        return self._to_json({"backend": "python", "tools": TOOL_REGISTRY})

    def service_info(self, workspace_dir: str | None = None) -> str:
        surface = self.app.public_surface()
        doctor = self.app.doctor(workspace_dir=workspace_dir)
        boundary = surface.get("service_boundary", {})
        consumer = surface.get("consumer_contract", {})
        return self._to_json(
            {
                "backend": "python",
                "service": {
                    "name": "Aegis Python MCP Service",
                    "runtime_version": surface["engine"]["runtime_version"],
                    "deployment_model": boundary.get("deployment_model", "local_sidecar_process"),
                    "preferred_transport": boundary.get("preferred_transport", "mcp_tool_process"),
                    "supported_transports": boundary.get("supported_transports", []),
                },
                "startup_contract": boundary.get("startup_contract", {}),
                "thin_host_guidance": boundary.get("thin_host_guidance", []),
                "default_operations": consumer.get("default_operations", []),
                "advanced_operations": consumer.get("advanced_operations", []),
                "health": doctor["health"],
            }
        )

    def startup_probe(self, workspace_dir: str | None = None) -> str:
        doctor = self.app.doctor(workspace_dir=workspace_dir)
        health = doctor["health"]
        ready = health["state"] in {"HEALTHY", "DEGRADED_SYNC"} and bool(health["capabilities"].get("local_store"))
        return self._to_json(
            {
                "backend": "python",
                "ready": ready,
                "service_state": "READY" if ready else "BROKEN",
                "health_state": health["state"],
                "health": health,
                "workspace": doctor["workspace"],
                "database": doctor["database"],
                "recommended_next_step": "call service_info then invoke tools" if ready else "inspect memory_doctor output before tool calls",
            }
        )

    def memory_scope_policy(
        self,
        scope_type: str | None = None,
        scope_id: str | None = None,
        sync_policy: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.get_scope_policy(
                scope_type=scope_type,
                scope_id=scope_id,
                sync_policy=sync_policy,
            )
        )

    def memory_sync_export(
        self,
        scope_type: str,
        scope_id: str,
        workspace_dir: str | None = None,
    ) -> str:
        return self._to_json(
            self.app.export_sync_envelope(
                scope_type=scope_type,
                scope_id=scope_id,
                workspace_dir=workspace_dir,
            )
        )

    def memory_sync_preview(self, envelope_path: str) -> str:
        return self._to_json(self.app.preview_sync_envelope(envelope_path))

    def memory_sync_import(self, envelope_path: str) -> str:
        return self._to_json(self.app.import_sync_envelope(envelope_path))

    def memory_taxonomy_clean(self) -> str:
        return self._to_json(self.app.taxonomy_clean())

    def memory_rebuild(self) -> str:
        return self._to_json(self.app.rebuild())

    def memory_scan(self) -> str:
        return self._to_json(self.app.scan())

    def memory_visualize(self, limit: int = 1000, *, include_analysis: bool = False) -> str:
        return self._to_json(self.app.visualize(limit=limit, include_analysis=include_analysis))

    def memory_governance(self, scope_type: str | None = None, scope_id: str | None = None, memory_id: str | None = None, limit: int = 50) -> str:
        return self._to_json(
            self.app.inspect_governance(
                scope_type=scope_type,
                scope_id=scope_id,
                memory_id=memory_id,
                limit=limit,
            )
        )

    def memory_background_plan(self, scope_type: str, scope_id: str) -> str:
        return self._to_json(self.app.plan_background_intelligence(scope_type=scope_type, scope_id=scope_id))

    def memory_background_shadow(self, run_id: str) -> str:
        return self._to_json(self.app.shadow_background_intelligence_run(run_id))

    def memory_background_apply(self, run_id: str, *, max_mutations: int = 5) -> str:
        return self._to_json(self.app.background_intelligence.apply_run(run_id, max_mutations=max_mutations))

    def memory_background_rollback(self, run_id: str) -> str:
        return self._to_json(self.app.rollback_background_intelligence_run(run_id))

    def memory_vector_inspect(
        self,
        query: str,
        *,
        scope_type: str,
        scope_id: str,
        include_global: bool = False,
        limit: int = 10,
    ) -> str:
        return self._to_json(
            self.app.inspect_vector_store(
                query=query,
                scope_type=scope_type,
                scope_id=scope_id,
                include_global=include_global,
                limit=limit,
            )
        )

    def memory_evidence_artifacts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> str:
        return self._to_json(
            self.app.evidence_artifacts(
                scope_type=scope_type,
                scope_id=scope_id,
                memory_id=memory_id,
                limit=limit,
            )
        )

    def memory_storage_footprint(self) -> str:
        return self._to_json(
            {
                "backend": "python",
                "footprint": self.app.storage_footprint(),
                "compaction_policy": self.app.storage_compaction_policy(),
            }
        )

    def memory_storage_compact(
        self,
        *,
        archived_memory_days: int = 30,
        superseded_memory_days: int = 14,
        evidence_days: int = 30,
        governance_days: int = 30,
        replication_days: int = 14,
        background_days: int = 14,
        vacuum: bool = True,
    ) -> str:
        return self._to_json(
            self.app.compact_storage(
                archived_memory_days=archived_memory_days,
                superseded_memory_days=superseded_memory_days,
                evidence_days=evidence_days,
                governance_days=governance_days,
                replication_days=replication_days,
                background_days=background_days,
                vacuum=vacuum,
            )
        )

    def memory_remember(self, content: str) -> str:
        return self.app.memory_remember(content)

    def memory_recall(self, query: str, *, scope_type: str | None = None, scope_id: str | None = None) -> str:
        return self.app.memory_recall(query, scope_type=scope_type, scope_id=scope_id)

    def memory_correct(self, content: str) -> str:
        return self.app.memory_correct(content)

    def memory_forget(self, query: str) -> str:
        return self.app.memory_forget(query)

    def run_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        if tool_name == "memory_store":
            return self.memory_store(
                args.get("type"),
                args.get("content"),
                args.get("subject"),
                scope_type=args.get("scope_type", "agent"),
                scope_id=args.get("scope_id", "default"),
                source_kind=args.get("source_kind", "manual"),
                source_ref=args.get("source_ref"),
                summary=args.get("summary"),
                session_id=args.get("session_id"),
            )
        if tool_name == "memory_search":
            return self.memory_search(
                args.get("text"),
                limit=args.get("limit", 5),
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                include_global=args.get("include_global", True),
                semantic=args.get("semantic", False),
                semantic_model=args.get("semantic_model"),
                retrieval_mode=args.get("retrieval_mode", "explain"),
            )
        if tool_name == "memory_context_pack":
            return self.memory_context_pack(
                args.get("text"),
                limit=args.get("limit", 5),
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                include_global=args.get("include_global", True),
                semantic=args.get("semantic", False),
                semantic_model=args.get("semantic_model"),
            )
        if tool_name == "memory_conflict_prompt":
            return self.memory_conflict_prompt(
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                subject=args.get("subject"),
            )
        if tool_name == "memory_conflict_resolve":
            return self.memory_conflict_resolve(
                args.get("conflict_id"),
                action=args.get("action"),
                rationale=args.get("rationale"),
            )
        if tool_name == "memory_link_store":
            return self.memory_link_store(
                args.get("source_id"),
                args.get("target_id"),
                link_type=args.get("link_type"),
                weight=args.get("weight", 1.0),
                metadata=args.get("metadata"),
            )
        if tool_name == "memory_link_neighbors":
            return self.memory_link_neighbors(
                args.get("memory_id"),
                limit=args.get("limit", 10),
            )
        if tool_name == "memory_get":
            return self.memory_get(
                args.get("rel_path"),
                from_line=args.get("from", 0),
                lines=args.get("lines"),
                workspace_dir=args.get("workspace_dir"),
            )
        if tool_name in {"memory_status", "memory_stats"}:
            return self.memory_status()
        if tool_name == "memory_doctor":
            return self.memory_doctor(args.get("workspace_dir"))
        if tool_name == "memory_clean":
            return self.memory_clean(args.get("subject"))
        if tool_name == "memory_export":
            return self.memory_export(args.get("format", "json"))
        if tool_name == "memory_backup_upload":
            return self.memory_backup_upload(
                args.get("mode", "snapshot"),
                workspace_dir=args.get("workspace_dir"),
            )
        if tool_name == "memory_backup_list":
            return self.memory_backup_list(workspace_dir=args.get("workspace_dir"))
        if tool_name == "memory_backup_preview":
            return self.memory_backup_preview(
                args.get("snapshot_path"),
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
            )
        if tool_name == "memory_backup_download":
            return self.memory_backup_download(
                args.get("snapshot_path"),
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
            )
        if tool_name == "memory_profile":
            return self.memory_profile(
                scope_id=args.get("scope_id", "default"),
                scope_type=args.get("scope_type", "agent"),
            )
        if tool_name == "memory_setup":
            return self.memory_setup(args.get("workspace_dir"))
        if tool_name == "memory_surface":
            return self.memory_surface()
        if tool_name == "memory_registry":
            return self.memory_registry()
        if tool_name == "service_info":
            return self.service_info(args.get("workspace_dir"))
        if tool_name == "startup_probe":
            return self.startup_probe(args.get("workspace_dir"))
        if tool_name == "memory_scope_policy":
            return self.memory_scope_policy(
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                sync_policy=args.get("sync_policy"),
            )
        if tool_name == "memory_sync_export":
            return self.memory_sync_export(
                args.get("scope_type"),
                args.get("scope_id"),
                workspace_dir=args.get("workspace_dir"),
            )
        if tool_name == "memory_sync_preview":
            return self.memory_sync_preview(args.get("envelope_path"))
        if tool_name == "memory_sync_import":
            return self.memory_sync_import(args.get("envelope_path"))
        if tool_name == "memory_taxonomy_clean":
            return self.memory_taxonomy_clean()
        if tool_name == "memory_rebuild":
            return self.memory_rebuild()
        if tool_name == "memory_scan":
            return self.memory_scan()
        if tool_name == "memory_visualize":
            return self.memory_visualize(
                limit=args.get("limit", 1000),
                include_analysis=args.get("include_analysis", False),
            )
        if tool_name == "memory_governance":
            return self.memory_governance(
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                memory_id=args.get("memory_id"),
                limit=args.get("limit", 50),
            )
        if tool_name == "memory_background_plan":
            return self.memory_background_plan(
                args.get("scope_type"),
                args.get("scope_id"),
            )
        if tool_name == "memory_background_shadow":
            return self.memory_background_shadow(args.get("run_id"))
        if tool_name == "memory_background_apply":
            return self.memory_background_apply(
                args.get("run_id"),
                max_mutations=args.get("max_mutations", 5),
            )
        if tool_name == "memory_background_rollback":
            return self.memory_background_rollback(args.get("run_id"))
        if tool_name == "memory_vector_inspect":
            return self.memory_vector_inspect(
                args.get("query"),
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                include_global=args.get("include_global", False),
                limit=args.get("limit", 10),
            )
        if tool_name == "memory_evidence_artifacts":
            return self.memory_evidence_artifacts(
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
                memory_id=args.get("memory_id"),
                limit=args.get("limit", 50),
            )
        if tool_name == "memory_storage_footprint":
            return self.memory_storage_footprint()
        if tool_name == "memory_storage_compact":
            return self.memory_storage_compact(
                archived_memory_days=args.get("archived_memory_days", 30),
                superseded_memory_days=args.get("superseded_memory_days", 14),
                evidence_days=args.get("evidence_days", 30),
                governance_days=args.get("governance_days", 30),
                replication_days=args.get("replication_days", 14),
                background_days=args.get("background_days", 14),
                vacuum=args.get("vacuum", True),
            )
        if tool_name == "memory_remember":
            return self.memory_remember(args.get("content"))
        if tool_name == "memory_recall":
            return self.memory_recall(
                args.get("query"),
                scope_type=args.get("scope_type"),
                scope_id=args.get("scope_id"),
            )
        if tool_name == "memory_correct":
            return self.memory_correct(args.get("content"))
        if tool_name == "memory_forget":
            return self.memory_forget(args.get("query"))
        return self._error("tool_not_found", tool=tool_name)

    def close(self) -> None:
        self.app.close()

    def _to_json(self, payload: Any) -> str:
        return json.dumps(payload, indent=2, ensure_ascii=False)

    def _error(self, code: str, **details: Any) -> str:
        return self._to_json({"error": code, **details})


def main() -> None:
    parser = argparse.ArgumentParser(description="Aegis Python MCP Server")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--service-info", action="store_true", help="Print the stable local-service descriptor as JSON")
    parser.add_argument("--startup-probe", action="store_true", help="Print a startup readiness probe as JSON")
    parser.add_argument("--tool", help="Run a single tool and print its output")
    parser.add_argument("--args-json", default="{}", help="JSON payload for --tool")
    parser.add_argument("--workspace-dir", help="Optional workspace path for health and startup checks")
    args = parser.parse_args()

    server = AegisMCPServer()
    try:
        if args.service_info:
            print(server.service_info(workspace_dir=args.workspace_dir))
            return
        if args.startup_probe:
            print(server.startup_probe(workspace_dir=args.workspace_dir))
            return
        if args.tool:
            payload = json.loads(args.args_json)
            if args.workspace_dir and "workspace_dir" not in payload:
                payload["workspace_dir"] = args.workspace_dir
            print(server.run_tool(args.tool, payload))
            return
        if args.test:
            print("Running Aegis MCP Self-Test...")
            print(
                server.memory_store(
                    "semantic",
                    "Aegis uses SQLite FTS5 for local retrieval.",
                    "technical.storage",
                    scope_type="project",
                    scope_id="aegis-v4",
                    source_kind="manual",
                    source_ref="self-test",
                )
            )
            print(server.memory_search("SQLite retrieval", scope_type="project", scope_id="aegis-v4"))
            print(server.memory_status())
        else:
            print("Aegis Python MCP Server is ready.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
