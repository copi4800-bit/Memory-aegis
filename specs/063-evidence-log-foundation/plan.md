# Implementation Plan: Evidence Log Foundation

**Branch**: `063-evidence-log-foundation` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/063-evidence-log-foundation/spec.md`

## Summary

Add the first real v7 migration primitive to Aegis v4: an immutable local evidence log plus stable evidence linkage from memory records, while keeping the current retrieval/runtime interfaces intact.

## Technical Context

**Language/Version**: Python, SQLite schema/migration SQL, tests  
**Primary Dependencies**: `aegis_py/storage/migrations/001_baseline.sql`, `aegis_py/storage/manager.py`, `aegis_py/storage/models.py`, `aegis_py/memory/ingest.py`, `aegis_py/memory/core.py`, integration/storage tests  
**Storage**: local SQLite, append-only evidence table plus memory-to-evidence linkage  
**Testing**: `pytest` storage/integration/runtime suite and relevant host contract tests  
**Target Platform**: current local-first runtime and future v7 migration slices  
**Constraints**: preserve current public contract; do not introduce promotion gating or retrieval rewrites in this tranche; evidence must remain local-first and SQLite-native  
**Scale/Scope**: schema extension, ingest persistence changes, model updates, and backward-compatible tests

## Constitution Check

- **Local-First Memory Engine**: Pass. Evidence storage is local and SQLite-native.
- **Brownfield Refactor Over Rewrite**: Pass. This tranche extends the current persistence path.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Evidence linkage strengthens explainability without changing payload shape.
- **Safe Memory Mutation By Default**: Pass. Evidence rows are append-only and support safer future validation.
- **Measured Simplicity**: Pass. This tranche adds one foundational store without attempting the whole v7 state model at once.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── memory/
│   │   ├── core.py
│   │   └── ingest.py
│   └── storage/
│       ├── manager.py
│       ├── models.py
│       ├── schema.py
│       └── migrations/001_baseline.sql
├── tests/
│   ├── test_storage.py
│   ├── test_integration.py
│   └── test_memory_core.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 063-evidence-log-foundation/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Design Notes

- Introduce a dedicated evidence table rather than encoding raw evidence only in free-form `metadata_json`.
- Keep evidence linkage additive and backward-compatible:
  - either direct columns such as `evidence_event_id`
  - or a structured metadata contract that is first-class enough to migrate later
- Preserve current retrieval payloads while making evidence queryable internally.
- Defer promotion gating, state machine, and admission thresholds to later slices.

## Validation Plan

- Extend the SQLite schema with evidence event storage.
- Update canonical ingest/memory persistence so evidence is recorded for new writes.
- Add storage/integration tests for append-only evidence and memory linkage.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_storage.py`
  - `.venv/bin/python -m pytest -q tests/test_integration.py -k "provenance or evidence or runtime"`
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`

## Expected Evidence

- append-only evidence table in local SQLite
- canonical ingest writes evidence rows
- memory records carry evidence linkage
- existing public retrieval/runtime contracts remain green

## Complexity Tracking

Main risk: leaking the future v7 state/admission design into this foundation slice. Guard against that by keeping this tranche storage-first and compatibility-first.
