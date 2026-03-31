# Implementation Plan: Internal Evidence Consumption

**Branch**: `064-internal-evidence-consumption` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/064-internal-evidence-consumption/spec.md`

## Summary

Build the narrow runtime seam after `063`: make evidence rows readable and inspectable through Python-owned helpers so later promotion logic can consume evidence without coupling directly to storage internals.

## Technical Context

**Language/Version**: Python, SQLite schema/runtime helpers, tests  
**Primary Dependencies**: `aegis_py/storage/manager.py`, `aegis_py/app.py`, `aegis_py/memory/core.py`, `aegis_py/surface.py`, relevant tests  
**Storage**: existing local SQLite evidence event store from `063-evidence-log-foundation`  
**Testing**: `pytest` runtime/storage/integration suites plus host contract validation  
**Target Platform**: current Python-owned local-first runtime and the next promotion-prep tranche  
**Constraints**: preserve public payloads; do not add admission gates, validation policy engines, promotion states, or retrieval rewrites in this slice  
**Scale/Scope**: internal helper methods, evidence inspection/reporting, and compatibility-first tests

## Constitution Check

- **Local-First Memory Engine**: Pass. Evidence access remains local and SQLite-native.
- **Brownfield Refactor Over Rewrite**: Pass. This tranche adds bounded helper seams on top of `063`.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Internal evidence consumption strengthens the provenance foundation without changing public retrieval output yet.
- **Safe Memory Mutation By Default**: Pass. The work is read/inspection-oriented and keeps evidence append-only.
- **Measured Simplicity**: Pass. This tranche stops at internal evidence access and reporting.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── memory/
│   │   └── core.py
│   └── storage/
│       ├── manager.py
│       └── models.py
├── tests/
│   ├── test_storage.py
│   ├── test_integration.py
│   └── test_memory_core.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 064-internal-evidence-consumption/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Design Notes

- Prefer narrow runtime helpers such as “get evidence for memory” and “summarize evidence coverage” over broad new public APIs.
- Keep public MCP/host/search payloads unchanged in this tranche.
- Make later promotion-gate work depend on these helpers rather than reaching directly into SQL from app/service code.
- Defer candidate representation, validator policy, and richer memory states to the following tranche.

## Validation Plan

- Add stable internal evidence lookup helpers.
- Add runtime inspection/reporting for evidence coverage.
- Add storage/runtime/integration tests for evidence consumption.
- Re-run:
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`

## Expected Evidence

- internal helper path from memory record to linked evidence event
- runtime-visible evidence coverage reporting
- no public retrieval contract drift
- test evidence showing compatibility remains green

## Complexity Tracking

Main risk: accidentally turning “internal evidence consumption” into an early promotion gate. Guard against that by keeping this slice read-oriented and compatibility-first.
