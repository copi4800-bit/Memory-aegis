# Implementation Plan: Promotion Gate Primitives

**Branch**: `065-promotion-gate-primitives` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/065-promotion-gate-primitives/spec.md`

## Summary

Build the first bounded admission layer after `063` and `064`: introduce internal candidate and promotion-gate primitives that evaluate evidence-backed memory candidates before promotion, while keeping the current public retrieval/runtime contracts intact.

## Technical Context

**Language/Version**: Python, SQLite-backed runtime helpers, tests  
**Primary Dependencies**: `aegis_py/memory/ingest.py`, `aegis_py/memory/core.py`, `aegis_py/storage/manager.py`, `aegis_py/app.py`, contradiction/confidence helpers, relevant tests  
**Storage**: existing local SQLite memory and evidence stores from `063` and `064`  
**Testing**: `pytest` runtime/storage/integration suites plus host contract validation  
**Target Platform**: current Python-owned local-first runtime and the follow-on formal state-machine tranche  
**Constraints**: preserve public payloads; do not introduce the full richer state model; do not rewrite retrieval behavior in this slice  
**Scale/Scope**: internal candidate representation, promotion-gate helper logic, bounded admission checks, and compatibility-first tests

## Constitution Check

- **Local-First Memory Engine**: Pass. Promotion checks remain local and SQLite-native.
- **Brownfield Refactor Over Rewrite**: Pass. This tranche inserts an admission seam into the current runtime.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Promotion decisions become more explicit without changing public retrieval payloads yet.
- **Safe Memory Mutation By Default**: Pass. This tranche reduces implicit trust by separating extraction from promotion.
- **Measured Simplicity**: Pass. It stops at promotion primitives and defers the full formal state model.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── memory/
│   │   ├── core.py
│   │   └── ingest.py
│   └── storage/
│       ├── manager.py
│       └── models.py
├── tests/
│   ├── test_ingest.py
│   ├── test_integration.py
│   └── test_memory_core.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 065-promotion-gate-primitives/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Design Notes

- Introduce a candidate-first internal seam before storage promotion, rather than mixing promotion rules into raw storage helpers.
- Promotion checks should start narrow: evidence presence, contradiction visibility, and bounded confidence rules.
- Keep current public search/status payloads unchanged in this tranche.
- Defer richer explicit states such as `draft`, `validated`, `hypothesized`, `invalidated`, and `consolidated` to the following tranche.

## Validation Plan

- Add internal candidate and promotion-gate helpers.
- Thread canonical ingest through the new promotion seam.
- Add runtime/integration tests for promotable vs non-promotable candidate outcomes.
- Re-run:
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`

## Expected Evidence

- internal candidate representation before promotion
- promotion decisions grounded in evidence and bounded admission signals
- no public retrieval contract drift
- test evidence showing compatibility remains green

## Complexity Tracking

Main risk: accidentally jumping from bounded promotion primitives straight into the full state-machine tranche. Guard against that by keeping decision outputs narrow and by not introducing the richer state taxonomy yet.
