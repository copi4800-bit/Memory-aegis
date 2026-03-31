# Project: Aegis v4 (Python)

## Vision
Aegis Python is a local-first memory engine for OpenClaw and MCP-based agents. It provides durable, scope-aware, and explainable memory storage and retrieval.

## Core Values
- **Reliability**: Recalls the right memory for the current scope without corruption.
- **Explainability**: Every result must be traceable to provenance and clear reasoning.
- **Hygiene**: Bounded reinforcement and decay to keep memory fresh and relevant.
- **Privacy**: Local-first storage (SQLite) with strict scope isolation.

## Workflow
- **Feature Truth**: `specs/*`
- **Governance**: `.specify/memory/constitution.md`
- **Execution Layer**: `.planning/*`
- **Workflow Contract**: `specs/*` + `.specify/memory/constitution.md`, with `.planning/*` as orchestration only

## Tech Stack
- **Runtime**: Python 3.11+
- **Database**: SQLite + FTS5
- **Interface**: MCP / OpenClaw host bootstrap

## Current Direction
- Python is the only intended engine owner.
- Any remaining TypeScript is transitional host/bootstrap code only.
- `.planning/` is derivative and must be kept aligned with active feature specs.
- Legacy implementation detail belongs in `specs/*` or code, not in `.planning/*`.
