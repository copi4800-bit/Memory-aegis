# Implementation Plan: State-Aware Governed Operations

**Branch**: `068-state-aware-governed-operations` | **Date**: 2026-03-29 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/068-state-aware-governed-operations/spec.md)
**Input**: Feature specification from `/specs/068-state-aware-governed-operations/spec.md`

## Summary

Open the next bounded tranche after `067` by creating explicit architecture seams for governance, background mutation, operator surfaces, and storage hygiene. The goal is not a rewrite. The goal is to reduce the risk of further state-aware governed work by shrinking `AegisApp` and `StorageManager` responsibilities, and by naming one canonical contract owner for tool publication.

## Technical Context

**Language/Version**: Python 3.11+, TypeScript bridge for host bootstrap  
**Primary Dependencies**: `aegis_py/app.py`, `aegis_py/operations.py`, `aegis_py/mcp/server.py`, `aegis_py/storage/manager.py`, `aegis_py/v7/*`, `aegis_py/surface.py`, `src/python-adapter.ts`, `index.ts`, `openclaw.plugin.json`  
**Storage**: SQLite with one Python-owned connection manager and existing migrations  
**Testing**: pytest plus host bootstrap checks (`vitest`)  
**Target Platform**: current local-first Python-owned runtime and thin-host adapter path  
**Constraints**: preserve payload shapes, preserve Python semantic ownership, no broad rewrite, no resurrection of TS engine semantics, no speculative autonomy expansion beyond governed seams  
**Scale/Scope**: architecture hardening and runtime seam extraction for tranche `068`

## Constitution Check

- **Local-First Memory Engine**: Pass. The plan keeps semantics and storage local in Python.
- **Brownfield Refactor Over Rewrite**: Pass. Every step is an extraction or registry consolidation on top of the existing runtime.
- **Explainability Is Non-Negotiable**: Pass. Governed operations stay explanation-first and compatibility-first.
- **Safe Memory Mutation By Default**: Pass. Operator and background mutation surfaces remain bounded and test-driven.
- **Measured Simplicity**: Pass. The tranche is explicitly about reducing architecture drag, not opening new product scope.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── operations.py
│   ├── surface.py
│   ├── mcp/server.py
│   ├── storage/manager.py
│   └── v7/
├── src/
│   └── python-adapter.ts
├── index.ts
├── openclaw.plugin.json
├── tests/
│   ├── test_app_surface.py
│   ├── test_user_surface.py
│   ├── test_storage_growth_control.py
│   ├── test_v7_runtime.py
│   ├── test_python_only_runtime_contract.py
│   └── acceptance/, regression/, replication/
└── specs/
    └── 068-state-aware-governed-operations/
        ├── spec.md
        └── plan.md
```

## Current Architecture Risks

- `AegisApp` is carrying too many unrelated responsibilities: end-user flows, operator summaries, backup helpers, sync helpers, governed background flows, and convenience wrappers.
- `StorageManager` is carrying too many unrelated responsibilities: migrations, memory persistence, evidence rows, governance rows, link storage, and storage compaction.
- Public tool declarations are duplicated across `aegis_py/surface.py`, `aegis_py/mcp/server.py`, `src/python-adapter.ts`, `index.ts`, and `openclaw.plugin.json`.
- The TypeScript layer is correctly transitional, but the current publication path still requires careful multi-file edits for every tool change.

## Refactor Strategy

### Slice 1: Extract Python Runtime Surface Facades

Create smaller Python-owned facades beneath `aegis_py/` and delegate from `AegisApp` rather than continuing to add methods directly to the god file.

Target seams:

- `health_surface.py`: `status`, `doctor`, summaries, startup probe helpers
- `operator_surface.py`: storage footprint, compaction, governance listing, evidence artifact inspection
- `backup_surface.py`: backup, preview, restore, manifests
- `sync_surface.py`: scope policy, sync export/preview/import
- `governed_background_surface.py`: background plan, shadow, apply, rollback

Rules:

- `AegisApp` remains the assembly root and compatibility shim.
- Public method names remain stable.
- The first extraction should move implementation bodies, not redesign payloads.

### Slice 2: Split Storage Responsibilities Without Splitting Connection Ownership

Keep one connection owner but introduce internal storage slices so governed operations and storage hygiene stop depending on a single giant class.

Target slices:

- `MemoryRepository`: memory rows, search-adjacent fetches, transitions, link neighbors
- `EvidenceRepository`: evidence events, evidence artifacts, evidence coverage helpers
- `GovernanceRepository`: governance events, background runs, audit logs
- `StorageHygieneRepository`: footprint, compaction, retention policy, vacuum helpers

Rules:

- `StorageManager` becomes a composition root and compatibility facade.
- Migrations and `_get_connection()` stay centralized.
- No schema churn is required for this tranche by default.

### Slice 3: Introduce a Runtime-Owned Contract Registry

Reduce drift by defining the canonical public operations and tool metadata once in Python-owned runtime space, then consume or generate derived adapter bindings from it.

Near-term target:

- keep `aegis_py/surface.py` as the semantic owner for operation lists and public ownership notes
- add an explicit tool metadata registry for names, descriptions, and argument ownership
- use that registry to drive `mcp/server.py` dispatch review and to reduce copy-paste pressure in TS/plugin layers

This tranche does not need full code generation if that is too much change at once. A single canonical registry plus adapter assertions is enough.

### Slice 4: Lock Public Contract Invariants While Refactoring

Every extraction slice should be validated against the same high-signal surface suites so architecture work cannot hide a product regression.

Minimum invariants:

- `status()` and `doctor()` remain fail-safe when storage is degraded
- backup/sync/background tool payloads remain shape-compatible
- storage operator surfaces stay visible through Python CLI, MCP, TS adapter, and plugin metadata

## Structure Decision

Keep `068` focused on architecture seams and contract ownership, not on new product breadth. The right outcome is a cleaner runtime that makes later state-aware governance and production-discipline slices cheaper to land.

## Execution Order

1. Extract `status`/`doctor`/summary logic into a health facade and keep `AegisApp` as compatibility wrapper.
2. Extract storage footprint/compaction and adjacent operator helpers into an operator facade.
3. Introduce internal storage slice classes behind `StorageManager`.
4. Add a canonical contract registry and use it to review or trim duplicated adapter definitions.
5. Re-run Python and host contract suites after each extraction slice.

## Validation Plan

For architecture slices in this tranche, keep using the current high-signal command set:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_app_surface.py tests/test_user_surface.py tests/test_storage_growth_control.py
PYTHONPATH=. .venv/bin/python -m pytest -q tests/acceptance tests/regression tests/test_observability_runtime.py tests/replication/test_sync.py tests/test_python_only_runtime_contract.py tests/test_v7_runtime.py
npm run build
npm run test:bootstrap
```

For lightweight iteration during extraction:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_app_surface.py -k "status or doctor"
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_user_surface.py -k "storage or doctor or status"
```

## Expected Evidence

- Smaller Python-owned runtime surface modules with unchanged public method names
- `AegisApp` reduced toward orchestration and compatibility delegation
- `StorageManager` reduced toward connection ownership and composed storage slices
- One explicit canonical contract registry or equivalent reviewable source of truth
- Green Python and host contract validation after each slice

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Add internal facades before deleting old methods | Needed to preserve public contracts while shrinking god files | Direct in-place rewrites would blur regressions and make rollback harder |
| Keep TypeScript adapter layer during cleanup | Needed because OpenClaw still loads the built plugin bridge | Deleting adapter layers now would break the thin-host path rather than simplify it |
| Keep one storage compatibility facade while composing repositories | Needed to avoid a high-risk persistence rewrite mid-tranche | Splitting connection ownership early would create migration and lifecycle risk |

## Out of Scope

- Replacing SQLite
- Rewriting the retrieval pipeline
- Returning to a TypeScript-owned engine
- Broad autonomy expansion beyond governed, explanation-first seams
- Full manifest code generation if a lighter registry-first step is sufficient

## Residual Architecture Debt After 068

- `StorageManager` now has a real storage-hygiene slice, but memory, evidence, and governance repositories are still concentrated in one compatibility facade.
- The Python runtime now owns operation groups and metadata through `aegis_py.tool_registry`, but TypeScript/plugin layers still consume derived copies rather than generated artifacts.
- `AegisApp` is materially slimmer for health, operator, backup, sync, and governed-background paths, but it still holds a large amount of user-flow and helper logic that could be decomposed later only if runtime evidence justifies it.
