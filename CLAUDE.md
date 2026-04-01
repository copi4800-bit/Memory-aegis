# Memory Aegis v9 (The Fortress Edition)

Mathematical truth-alignment and judgment engine for AI agents.

## Build & Run
- Setup: `pip install -r requirements.txt`
- Run MCP: `export PYTHONPATH=$PYTHONPATH:. && python3 aegis_py/mcp/server.py`
- Test: `export PYTHONPATH=$PYTHONPATH:. && python3 -m pytest tests/` (To be implemented)

## Workflow Contract
- Feature truth: `specs/*`
- Constitution: `.specify/memory/constitution.md`
- Orchestration/status: `.planning/*`
- Workflow contract: `specs/*` + `.specify/memory/constitution.md` with `.planning/*` as orchestration only

## Rule
- Use GSD to map, sequence, and execute work.
- Use Spec Kit to define scope, plan, and tasks.
- Check the active feature in `specs/*` before using `/gsd:*` for material work.
- If no active feature fits, update or create the Spec Kit artifacts first.
- Do not implement major feature work from `.planning/` alone.
- If `.planning/` and `specs/*` disagree, `specs/*` wins.

## Tech Stack
- Python 3.11+
- SQLite + FTS5
- MCP Python SDK

## Coding Conventions
- Standard Library first (Zero-dependency goal)
- Type hints for all functions
- Dataclasses for memory models
- SQL migrations in `aegis_py/storage/schema.sql`
