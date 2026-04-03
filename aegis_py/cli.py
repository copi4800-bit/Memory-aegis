from __future__ import annotations

import argparse
import json
import io
import sys
from typing import Any, Sequence

from .app import AegisApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truthkeep",
        description="TruthKeep Memory CLI: correctness-first local memory for AI agents.",
    )
    parser.add_argument(
        "--db-path",
        default="memory_aegis.db",
        help="SQLite database path. Defaults to ./memory_aegis.db",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    remember = subparsers.add_parser("remember", help="Store a memory using the consumer path.")
    remember.add_argument("content", help="Content to remember.")

    recall = subparsers.add_parser("recall", help="Recall memories using the consumer path.")
    recall.add_argument("query", help="What to recall.")
    recall.add_argument("--scope-type")
    recall.add_argument("--scope-id")

    correct = subparsers.add_parser("correct", help="Correct an existing fact.")
    correct.add_argument("content", help="Corrected content.")

    status = subparsers.add_parser("status", help="Show runtime status.")
    status.add_argument("--json", action="store_true", help="Emit structured JSON.")

    field = subparsers.add_parser("field-snapshot", help="Show Xi(t) whole-system v10 field snapshot.")
    field.add_argument("--scope-type")
    field.add_argument("--scope-id")

    prove = subparsers.add_parser("prove-it", help="Run the short proof flow and print its summary.")
    prove.add_argument("--json", action="store_true", help="Emit structured JSON instead of a short summary.")

    mcp = subparsers.add_parser("mcp", help="Print the MCP startup hint.")
    mcp.add_argument("--json", action="store_true", help="Emit startup probe JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "prove-it":
        from scripts.prove_it import build_proof_summary

        summary = build_proof_summary(db_path=args.db_path)
        if args.json:
            emit_output(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            emit_output(render_proof_summary(summary))
        return 0

    if args.command == "mcp":
        if args.json:
            from .mcp.server import AegisMCPServer

            server = AegisMCPServer(args.db_path)
            try:
                emit_output(server.startup_probe())
            finally:
                server.close()
        else:
            emit_output("Run `aegis-mcp` to start the MCP server, or `truthkeep mcp --json` for a startup probe.")
        return 0

    app = AegisApp(args.db_path)
    try:
        if args.command == "remember":
            emit_output(app.memory_remember(args.content))
            return 0
        if args.command == "recall":
            emit_output(app.memory_recall(args.query, scope_type=args.scope_type, scope_id=args.scope_id))
            return 0
        if args.command == "correct":
            emit_output(app.memory_correct(args.content))
            return 0
        if args.command == "status":
            payload = app.status()
            emit_output(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else render_status(payload))
            return 0
        if args.command == "field-snapshot":
            payload = app.v10_field_snapshot(scope_type=args.scope_type, scope_id=args.scope_id)
            emit_output(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
    finally:
        app.close()
    parser.print_help(sys.stderr)
    return 1


def render_status(payload: dict[str, Any]) -> str:
    health = payload.get("health", {})
    counts = payload.get("counts", {})
    return "\n".join(
        [
            f"State: {health.get('state', 'UNKNOWN')}",
            f"Memories: {counts.get('total', 0)} total",
            f"Capabilities: {', '.join(sorted((health.get('capabilities') or {}).keys()))}",
        ]
    )


def render_proof_summary(summary: dict[str, Any]) -> str:
    metrics = summary.get("metrics", {})
    verdict = "PASS" if summary.get("passed") else "CHECK"
    return "\n".join(
        [
            f"TruthKeep proof: {verdict}",
            f"Correction-safe truth: {metrics.get('correction_top1_preserved')}",
            f"Why-not available: {metrics.get('why_not_available')}",
            f"V10 field snapshot available: {metrics.get('field_snapshot_available')}",
            f"Compressed tier available: {metrics.get('compressed_tier_available')}",
            f"Summary: {summary.get('summary')}",
        ]
    )


def emit_output(text: str, *, stream: io.TextIOBase | None = None) -> None:
    target = stream or sys.stdout
    try:
        print(text, file=target)
        return
    except UnicodeEncodeError:
        pass

    payload = f"{text}\n"
    encoding = getattr(target, "encoding", None) or "utf-8"
    buffer = getattr(target, "buffer", None)
    if buffer is not None:
        buffer.write(payload.encode(encoding, errors="replace"))
        buffer.flush()
        return
    target.write(payload.encode("ascii", errors="replace").decode("ascii"))
    target.flush()


if __name__ == "__main__":
    raise SystemExit(main())
