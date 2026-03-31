# Implementation Plan: State-Aware Internal Retrieval

**Branch**: `067-state-aware-internal-retrieval` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/067-state-aware-internal-retrieval/spec.md`

## Summary

Build the next bounded tranche after `066`: let retrieval and policy internals consume `admission_state` for bounded filtering and shaping, while preserving the current public runtime and retrieval contracts.

## Technical Context

**Language/Version**: Python, SQLite-backed retrieval/runtime helpers, tests  
**Primary Dependencies**: `aegis_py/retrieval/search.py`, `aegis_py/retrieval/engine.py`, `aegis_py/app.py`, `aegis_py/storage/manager.py`, relevant tests  
**Storage**: existing local SQLite memory/evidence stores plus admission-aware state contracts from `066`  
**Testing**: `pytest` runtime/retrieval/integration suites plus host contract validation  
**Target Platform**: current Python-owned local-first runtime and later deeper retrieval-state work  
**Constraints**: preserve public payloads; do not attempt a broad retrieval rewrite; keep scope bounded to state-aware internal consumption  
**Scale/Scope**: internal retrieval/policy shaping, state-aware helpers, and compatibility-first tests

## Constitution Check

- **Local-First Memory Engine**: Pass. State-aware retrieval remains local and SQLite-native.
- **Brownfield Refactor Over Rewrite**: Pass. This tranche hardens internals on top of `066`.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Explicit state-aware internals improve trust shaping without changing public payloads yet.
- **Safe Memory Mutation By Default**: Pass. This tranche is primarily read/filter/shaping oriented.
- **Measured Simplicity**: Pass. It stops at bounded internal retrieval-state consumption.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── retrieval/
│   │   ├── engine.py
│   │   └── search.py
│   └── storage/
│       └── manager.py
├── tests/
│   ├── test_retrieval.py
│   ├── test_integration.py
│   └── test_storage.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 067-state-aware-internal-retrieval/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Design Notes

- Prefer bounded filtering/trust shaping rules over broad search pipeline redesign.
- Let internal consumers read `admission_state` through stable helpers.
- Keep public payloads unchanged in this tranche.
- Defer deeper ranking/routing redesign to later work if still needed.

## Validation Plan

- Add state-aware internal retrieval and policy helpers.
- Add bounded retrieval shaping that consumes `admission_state`.
- Add storage/retrieval/integration tests for state-aware internal behavior.
- Re-run:
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`

## Expected Evidence

- internal retrieval helpers that consume `admission_state`
- bounded state-aware shaping without payload drift
- green Python and host contract validation

## Complexity Tracking

Main risk: turning “state-aware internal retrieval” into a broad retrieval rewrite. Guard against that by constraining changes to bounded internal shaping and compatibility-first tests.
