# Implementation Plan: Formal Memory State Machine

**Branch**: `066-formal-memory-state-machine` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/066-formal-memory-state-machine/spec.md`

## Summary

Build the next bounded tranche after `065`: introduce an explicit internal admission-aware memory state model that records promotion outcomes directly while preserving the current public runtime and retrieval contracts.

## Technical Context

**Language/Version**: Python, SQLite-backed runtime/storage helpers, tests  
**Primary Dependencies**: `aegis_py/storage/models.py`, `aegis_py/storage/manager.py`, `aegis_py/memory/ingest.py`, `aegis_py/hygiene/transitions.py`, `aegis_py/app.py`, relevant tests  
**Storage**: existing local SQLite memory and evidence stores plus promotion metadata from `065`  
**Testing**: `pytest` runtime/storage/integration suites plus host contract validation  
**Target Platform**: current Python-owned local-first runtime and later retrieval/policy slices  
**Constraints**: preserve public payloads; do not rewrite retrieval behavior in this slice; keep lifecycle compatibility intact  
**Scale/Scope**: internal state taxonomy, persistence mapping, compatibility helpers, and tests

## Constitution Check

- **Local-First Memory Engine**: Pass. State remains local and SQLite-native.
- **Brownfield Refactor Over Rewrite**: Pass. This tranche extends the current runtime/persistence path.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Explicit states improve internal explainability without changing public retrieval payloads yet.
- **Safe Memory Mutation By Default**: Pass. Admission outcomes become more explicit and auditable.
- **Measured Simplicity**: Pass. It stops at internal state modeling and defers retrieval consumption changes.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── hygiene/
│   │   └── transitions.py
│   ├── memory/
│   │   └── ingest.py
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
    └── 066-formal-memory-state-machine/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Design Notes

- Add an explicit admission-aware state field or equivalent stable internal contract.
- Keep current lifecycle status semantics available during the transition.
- Map `065` promotion outcomes into the new state model rather than re-deriving them later.
- Defer retrieval/ranking consumption of the new states to a later tranche.

## Validation Plan

- Add the state model and compatibility mapping.
- Thread canonical ingest/promotion decisions into the new state path.
- Add storage/runtime/integration tests for state transitions and compatibility.
- Re-run:
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`

## Expected Evidence

- explicit internal state model for admission outcomes
- compatibility mapping from current lifecycle behavior
- no public retrieval contract drift
- green validation across Python and host contract suites

## Complexity Tracking

Main risk: mixing the state-model tranche with retrieval behavior changes. Guard against that by keeping the state work internal and compatibility-first.
