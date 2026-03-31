from __future__ import annotations

import argparse
import json
import sys

from aegis_py.app import AegisApp


def _to_json(payload):
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aegis backup drill helper")
    parser.add_argument("--db-path", help="Override the SQLite database path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a snapshot or export backup")
    create.add_argument("--mode", choices=["snapshot", "export"], default="snapshot")
    create.add_argument("--workspace-dir")

    preview = subparsers.add_parser("preview", help="Preview restore impact without mutation")
    preview.add_argument("--snapshot-path", required=True)
    preview.add_argument("--scope-type")
    preview.add_argument("--scope-id")

    restore = subparsers.add_parser("restore", help="Restore from a snapshot or export backup")
    restore.add_argument("--snapshot-path", required=True)
    restore.add_argument("--scope-type")
    restore.add_argument("--scope-id")

    listing = subparsers.add_parser("list", help="List known backups")
    listing.add_argument("--workspace-dir")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    app = AegisApp(db_path=args.db_path)
    try:
        if args.command == "create":
            print(_to_json(app.create_backup(mode=args.mode, workspace_dir=args.workspace_dir)))
            return 0
        if args.command == "preview":
            print(
                _to_json(
                    app.preview_restore(
                        args.snapshot_path,
                        scope_type=args.scope_type,
                        scope_id=args.scope_id,
                    )
                )
            )
            return 0
        if args.command == "restore":
            print(
                _to_json(
                    app.restore_backup(
                        args.snapshot_path,
                        scope_type=args.scope_type,
                        scope_id=args.scope_id,
                    )
                )
            )
            return 0
        if args.command == "list":
            print(_to_json(app.list_backups(workspace_dir=args.workspace_dir)))
            return 0
        parser.error(f"Unsupported command: {args.command}")
        return 2
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
