from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .app import AegisApp


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aegis Python CLI")
    parser.add_argument("--db-path", help="Override the SQLite database path for this invocation")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("surface", help="Describe the public Aegis memory contract")
    status = subparsers.add_parser("status", help="Return high-level engine status")
    status.add_argument("--json", action="store_true", help="Print the full status payload as JSON")

    onboarding = subparsers.add_parser("onboarding", help="Run first-time setup checks for Aegis")
    onboarding.add_argument("--workspace-dir")
    onboarding.add_argument("--json", action="store_true", help="Print the full onboarding payload as JSON")

    doctor = subparsers.add_parser("doctor", help="Run a user-facing health and diagnostics check")
    doctor.add_argument("--workspace-dir")
    doctor.add_argument("--json", action="store_true", help="Print the full doctor payload as JSON")

    storage_footprint = subparsers.add_parser("storage-footprint", help="Inspect storage growth and compaction policy")
    storage_footprint.add_argument("--json", action="store_true", help="Print the full storage footprint payload as JSON")

    storage_compact = subparsers.add_parser("storage-compact", help="Prune cold historical rows and reclaim SQLite space")
    storage_compact.add_argument("--archived-memory-days", type=int, default=30)
    storage_compact.add_argument("--superseded-memory-days", type=int, default=14)
    storage_compact.add_argument("--evidence-days", type=int, default=30)
    storage_compact.add_argument("--governance-days", type=int, default=30)
    storage_compact.add_argument("--replication-days", type=int, default=14)
    storage_compact.add_argument("--background-days", type=int, default=14)
    storage_compact.add_argument("--no-vacuum", action="store_true")
    storage_compact.add_argument("--json", action="store_true", help="Print the full compaction payload as JSON")

    store = subparsers.add_parser("store", help="Store a memory")
    store.add_argument("--content", required=True)
    store.add_argument("--type")
    store.add_argument("--scope-type", default="agent")
    store.add_argument("--scope-id", default="default")
    store.add_argument("--subject")
    store.add_argument("--source-kind", default="manual")
    store.add_argument("--source-ref")
    store.add_argument("--summary")
    store.add_argument("--session-id")

    search = subparsers.add_parser("search", help="Search memories")
    search.add_argument("--query", required=True)
    search.add_argument("--scope-type", default="agent")
    search.add_argument("--scope-id", default="default")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--include-global", action="store_true")
    search.add_argument("--retrieval-mode", choices=["fast", "explain"], default="explain")

    context = subparsers.add_parser("context-pack", help="Build a host-ready context pack")
    context.add_argument("--query", required=True)
    context.add_argument("--scope-type", default="agent")
    context.add_argument("--scope-id", default="default")
    context.add_argument("--limit", type=int, default=5)
    context.add_argument("--include-global", action="store_true")

    link_store = subparsers.add_parser("link-store", help="Create or update an explicit relation between two memories")
    link_store.add_argument("--source-id", required=True)
    link_store.add_argument("--target-id", required=True)
    link_store.add_argument("--link-type", required=True)
    link_store.add_argument("--weight", type=float, default=1.0)
    link_store.add_argument("--metadata-json")

    link_neighbors = subparsers.add_parser("link-neighbors", help="Inspect explicit linked neighbors for a memory")
    link_neighbors.add_argument("--memory-id", required=True)
    link_neighbors.add_argument("--limit", type=int, default=10)

    backup = subparsers.add_parser("backup-upload", help="Create a snapshot or export backup")
    backup.add_argument("--mode", choices=["snapshot", "export"], default="snapshot")
    backup.add_argument("--workspace-dir")
    backup.add_argument("--json", action="store_true", help="Print the full backup payload as JSON")

    preview = subparsers.add_parser("backup-preview", help="Preview restore impact without mutation")
    preview.add_argument("--snapshot-path", required=True)
    preview.add_argument("--scope-type")
    preview.add_argument("--scope-id")
    preview.add_argument("--json", action="store_true", help="Print the full preview payload as JSON")

    backup_list = subparsers.add_parser("backup-list", help="List known backups from manifest metadata")
    backup_list.add_argument("--workspace-dir")
    backup_list.add_argument("--json", action="store_true", help="Print the full backup-list payload as JSON")

    backup_download = subparsers.add_parser("backup-download", help="Restore from a snapshot or export backup")
    backup_download.add_argument("--snapshot-path", required=True)
    backup_download.add_argument("--scope-type")
    backup_download.add_argument("--scope-id")
    backup_download.add_argument("--json", action="store_true", help="Print the full restore payload as JSON")

    scope_policy = subparsers.add_parser("scope-policy", help="Inspect effective scope sync policy")
    scope_policy.add_argument("--scope-type")
    scope_policy.add_argument("--scope-id")
    scope_policy.add_argument("--sync-policy")

    sync_export = subparsers.add_parser("sync-export", help="Export a file-based sync envelope for a sync-eligible scope")
    sync_export.add_argument("--scope-type", required=True)
    sync_export.add_argument("--scope-id", required=True)
    sync_export.add_argument("--workspace-dir")

    sync_preview = subparsers.add_parser("sync-preview", help="Preview a sync envelope without mutating the DB")
    sync_preview.add_argument("--envelope-path", required=True)

    sync_import = subparsers.add_parser("sync-import", help="Import a sync envelope into the local DB")
    sync_import.add_argument("--envelope-path", required=True)

    remember = subparsers.add_parser("remember", help="Store a memory (simplified)")
    remember.add_argument("content_text", nargs="?")
    remember.add_argument("--content")

    recall = subparsers.add_parser("recall", help="Recall a memory (simplified)")
    recall.add_argument("query_text", nargs="?")
    recall.add_argument("--query")

    correct = subparsers.add_parser("correct", help="Correct a memory (simplified)")
    correct.add_argument("content_text", nargs="?")
    correct.add_argument("--content")

    forget = subparsers.add_parser("forget", help="Forget a memory (simplified)")
    forget.add_argument("query_text", nargs="?")
    forget.add_argument("--query")

    return parser


def _to_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _resolve_text_arg(flag_value: str | None, positional_value: str | None, *, field_name: str) -> str:
    value = flag_value or positional_value
    if value:
        return value
    raise ValueError(f"{field_name} is required")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    app = AegisApp(db_path=args.db_path)
    try:
        command = args.command
        try:
            if command == "surface":
                print(_to_json(app.public_surface()))
                return 0
            if command == "status":
                payload = app.status()
                if args.json:
                    print(_to_json(payload))
                else:
                    print(app.status_summary())
                return 0
            if command == "onboarding":
                payload = app.onboarding(workspace_dir=args.workspace_dir)
                if args.json:
                    print(_to_json(payload))
                else:
                    print(payload["summary"])
                return 0
            if command == "doctor":
                payload = app.doctor(workspace_dir=args.workspace_dir)
                if args.json:
                    print(_to_json(payload))
                else:
                    print(app.doctor_summary(workspace_dir=args.workspace_dir))
                return 0
            if command == "storage-footprint":
                payload = {
                    "backend": "python",
                    "footprint": app.storage_footprint(),
                    "compaction_policy": app.storage_compaction_policy(),
                }
                if args.json:
                    print(_to_json(payload))
                else:
                    print(
                        "\n".join(
                            [
                                "## Aegis Storage",
                                "",
                                f"Allocated storage: {payload['footprint']['allocated_bytes']} bytes",
                                f"Free storage inside DB: {payload['footprint']['free_bytes']} bytes",
                                f"Memory rows: {payload['footprint']['rows'].get('memories', 0)}",
                                f"Archived-memory retention: {payload['compaction_policy']['archived_memory_days']} days",
                            ]
                        )
                    )
                return 0
            if command == "storage-compact":
                payload = app.compact_storage(
                    archived_memory_days=args.archived_memory_days,
                    superseded_memory_days=args.superseded_memory_days,
                    evidence_days=args.evidence_days,
                    governance_days=args.governance_days,
                    replication_days=args.replication_days,
                    background_days=args.background_days,
                    vacuum=not args.no_vacuum,
                )
                if args.json:
                    print(_to_json(payload))
                else:
                    print(
                        "\n".join(
                            [
                                "## Aegis Storage Compaction",
                                "",
                                f"Vacuumed: {'yes' if payload['vacuumed'] else 'no'}",
                                f"Allocated storage before: {payload['before']['allocated_bytes']} bytes",
                                f"Allocated storage after: {payload['after']['allocated_bytes']} bytes",
                                f"Archived memories deleted: {payload['deleted']['archived_memories']}",
                                f"Superseded memories deleted: {payload['deleted']['superseded_memories']}",
                            ]
                        )
                    )
                return 0
            if command == "store":
                memory = app.put_memory(
                    args.content,
                    type=args.type,
                    scope_type=args.scope_type,
                    scope_id=args.scope_id,
                    session_id=args.session_id,
                    subject=args.subject,
                    source_kind=args.source_kind,
                    source_ref=args.source_ref,
                    summary=args.summary,
                )
                if memory is None:
                    print(_to_json({"stored": False, "backend": "python"}))
                    return 0
                print(
                    _to_json(
                        {
                            "stored": True,
                            "backend": "python",
                            "memory_id": memory.id,
                            "type": memory.type,
                            "scope_type": memory.scope_type,
                            "scope_id": memory.scope_id,
                        }
                    )
                )
                return 0
            if command == "search":
                print(
                    _to_json(
                        app.search_payload(
                            args.query,
                            scope_id=args.scope_id,
                            scope_type=args.scope_type,
                            limit=args.limit,
                            include_global=args.include_global,
                            retrieval_mode=args.retrieval_mode,
                        )
                    )
                )
                return 0
            if command == "context-pack":
                print(
                    _to_json(
                        app.search_context_pack(
                            args.query,
                            scope_id=args.scope_id,
                            scope_type=args.scope_type,
                            limit=args.limit,
                            include_global=args.include_global,
                        )
                    )
                )
                return 0
            if command == "link-store":
                metadata = json.loads(args.metadata_json) if args.metadata_json else None
                print(
                    _to_json(
                        app.link_memories(
                            args.source_id,
                            args.target_id,
                            link_type=args.link_type,
                            weight=args.weight,
                            metadata=metadata,
                        )
                    )
                )
                return 0
            if command == "link-neighbors":
                print(_to_json(app.memory_neighbors(args.memory_id, limit=args.limit)))
                return 0
            if command == "backup-upload":
                payload = app.create_backup(mode=args.mode, workspace_dir=args.workspace_dir)
                if args.json:
                    print(_to_json(payload))
                else:
                    print(app.backup_create_summary(payload))
                return 0
            if command == "backup-preview":
                payload = app.preview_restore(
                    args.snapshot_path,
                    scope_type=args.scope_type,
                    scope_id=args.scope_id,
                )
                if args.json:
                    print(_to_json(payload))
                else:
                    print(app.restore_preview_summary(payload))
                return 0
            if command == "backup-list":
                payload = app.list_backups(workspace_dir=args.workspace_dir)
                if args.json:
                    print(_to_json(payload))
                else:
                    print(app.backup_list_summary(payload))
                return 0
            if command == "backup-download":
                payload = app.restore_backup(
                    args.snapshot_path,
                    scope_type=args.scope_type,
                    scope_id=args.scope_id,
                )
                if args.json:
                    print(_to_json(payload))
                else:
                    print(app.restore_result_summary(payload))
                return 0
            if command == "scope-policy":
                print(
                    _to_json(
                        app.get_scope_policy(
                            scope_type=args.scope_type,
                            scope_id=args.scope_id,
                            sync_policy=args.sync_policy,
                        )
                    )
                )
                return 0
            if command == "sync-export":
                print(
                    _to_json(
                        app.export_sync_envelope(
                            scope_type=args.scope_type,
                            scope_id=args.scope_id,
                            workspace_dir=args.workspace_dir,
                        )
                    )
                )
                return 0
            if command == "sync-preview":
                print(_to_json(app.preview_sync_envelope(args.envelope_path)))
                return 0
            if command == "sync-import":
                print(_to_json(app.import_sync_envelope(args.envelope_path)))
                return 0
            if command == "remember":
                print(app.memory_remember(_resolve_text_arg(args.content, args.content_text, field_name="content")))
                return 0
            if command == "recall":
                print(app.memory_recall(_resolve_text_arg(args.query, args.query_text, field_name="query")))
                return 0
            if command == "correct":
                print(app.memory_correct(_resolve_text_arg(args.content, args.content_text, field_name="content")))
                return 0
            if command == "forget":
                print(app.memory_forget(_resolve_text_arg(args.query, args.query_text, field_name="query")))
                return 0
        except ValueError as exc:
            parser.error(str(exc))
        parser.error(f"Unsupported command: {command}")
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
