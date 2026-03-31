# Implementation Plan: Weaver Link Surface

**Branch**: `011-weaver-link-surface` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/011-weaver-link-surface/spec.md)
**Input**: Feature specification from `/specs/011-weaver-link-surface/spec.md`

## Summary

Implement real Weaver functionality by exposing explicit memory-link creation and neighbor inspection from the Python runtime, then use those links in lexical-first context expansion and visualization.

## Technical Context

**Language/Version**: Python 3.13.x, TypeScript for host adapter shell  
**Primary Dependencies**: existing `aegis_py` runtime, SQLite `memory_links` table, current MCP and TS adapter surfaces  
**Storage**: existing local SQLite database  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Target Platform**: local Python runtime, MCP tool routing, OpenClaw TS adapter shell, Python CLI  
**Project Type**: Brownfield feature addition on top of existing storage and public surfaces  
**Performance Goals**: lexical-first retrieval remains the baseline; link expansion is bounded and local-only  
**Constraints**: no cross-scope links, no host-owned semantics, no cloud dependency, no link-only retrieval without lexical seed  
**Scale/Scope**: storage helpers, app methods, MCP/CLI/TS routing, README/docs, and retrieval/visualization integration

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. All link storage and traversal stay local in SQLite.
- `Brownfield Refactor Over Rewrite`: Pass. The feature activates the existing `memory_links` table rather than replacing retrieval.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Linked expansion remains tagged and bounded.
- `Safe Memory Mutation By Default`: Pass. Relation writes are explicit operations and cross-scope writes are rejected.
- `Measured Simplicity`: Pass. Weaver is implemented as a small set of explicit surfaces rather than a broad graph subsystem.

## Project Structure

### Documentation (this feature)

```text
specs/011-weaver-link-surface/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── cli.py
├── mcp/server.py
├── retrieval/search.py
├── storage/manager.py
└── surface.py

src/
├── python-adapter.ts
└── ...
```

**Structure Decision**: Activate explicit relation storage through `StorageManager`, expose it through `AegisApp`, then route it through all existing Python-owned surfaces.

## Phase Plan

### Phase 0 - Feature Reconciliation

Objective: Anchor GSD and Spec Kit to `011-weaver-link-surface`.

### Phase 1 - Python Weaver Core

Objective: Add link upsert and neighbor inspection to `StorageManager` and `AegisApp`.

### Phase 2 - Retrieval And Visualization Integration

Objective: Use explicit links in bounded lexical-first expansion and graph visualization.

### Phase 3 - Public Surface Exposure

Objective: Route Weaver operations through MCP, CLI, TS adapter, plugin manifest, and README.

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- explicit Weaver operations now exist in the Python runtime for link creation and neighbor inspection
- lexical-first context-pack can add explicit linked neighbors after lexical seed recall
- visualization now includes explicit relation edges when applicable
- MCP, CLI, and TS adapter paths expose the same Python-owned Weaver contract

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/011-weaver-link-surface`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `74 passed in 2.64s`
