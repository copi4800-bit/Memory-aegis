# Implementation Plan: Aegis v7 Runtime

**Branch**: `069-aegis-v7-runtime` | **Date**: 2026-03-28 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/069-aegis-v7-runtime/spec.md)
**Input**: Feature specification from `/specs/069-aegis-v7-runtime/spec.md`

## Summary

Upgrade the Python-owned runtime from the current v4-shaped engine to an explicit v7 flow by hardening evidence-first ingest, adding a validation and policy gate, persisting explicit memory states plus transition history, exposing specialized storage facades, introducing a governed background planning layer, and routing retrieval through a retrieval orchestrator.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: stdlib, sqlite3, pytest  
**Storage**: SQLite with FTS5 and incremental SQL migrations  
**Testing**: pytest  
**Target Platform**: Linux local runtime  
**Project Type**: library plus CLI/MCP runtime  
**Performance Goals**: Preserve current local-first behavior and keep retrieval bounded by existing stage budgets  
**Constraints**: Offline-capable, backward-compatible enough for current tests and runtime surfaces, no destructive autonomous mutation in background mode  
**Scale/Scope**: Incremental runtime architecture upgrade inside `aegis_py`

## Constitution Check

- Preserve Python-owned semantics as the production runtime.
- Keep changes explainable and test-backed.
- Prefer additive architecture over destructive rewrite because the repo is already mid-migration and dirty.

## Project Structure

### Documentation (this feature)

```text
specs/069-aegis-v7-runtime/
├── plan.md
├── spec.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── memory/
├── retrieval/
├── storage/
├── hygiene/
├── governance/
└── v7/

tests/
├── test_ingest.py
├── test_retrieval.py
└── test_v7_runtime.py
```

**Structure Decision**: Keep the existing six-module runtime intact and add a focused `aegis_py/v7/` layer that composes new architecture primitives instead of forking the whole engine.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Additive `v7` facade layer | Needed to upgrade architecture without destabilizing the repo-wide Python migration | Rewriting the existing modules in place would create higher regression risk in a dirty worktree |
