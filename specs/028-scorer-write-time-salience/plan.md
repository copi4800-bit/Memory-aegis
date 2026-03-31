# Implementation Plan: Scorer Write-Time Salience

**Branch**: `028-scorer-write-time-salience` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/028-scorer-write-time-salience/spec.md)
**Input**: Feature specification from `/specs/028-scorer-write-time-salience/spec.md`

## Summary

Implement the final Tranche A slice by assigning conservative write-time confidence and activation scores when callers omit them, while preserving explicit score overrides.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/memory/ingest.py`, `aegis_py/memory/factory.py`, existing retrieval ordering on `activation_score`  
**Storage**: existing SQLite `memories.confidence` and `memories.activation_score` fields  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep scoring deterministic and bounded, preserve explicit score values, avoid opaque or overfit heuristics  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- add a small memory-local scorer helper
- infer only when callers omit `confidence` or `activation_score`
- keep scores within a narrow bounded range around the existing default
- pass explicit score values through unchanged

## Work Plan

1. reconcile `.planning/STATE.md` to feature `028-scorer-write-time-salience`
2. add a deterministic write-time scorer helper in the `memory` module
3. wire scoring into `IngestEngine` and allow `MemoryFactory` to accept inferred or explicit scores
4. extend integration coverage for inferred scoring and explicit preservation
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 028-scorer-write-time-salience:

- ingest now assigns conservative write-time `confidence` and `activation_score` values when callers omit them
- explicit caller-provided score values remain authoritative and unchanged
- write-time salience now varies in a bounded way by inferred lane and simple content cues without adding an opaque ranking subsystem

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/028-scorer-write-time-salience`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `789ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `87 passed in 2.83s`
