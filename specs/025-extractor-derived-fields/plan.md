# Implementation Plan: Extractor Derived Fields

**Branch**: `025-extractor-derived-fields` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/025-extractor-derived-fields/spec.md)
**Input**: Feature specification from `/specs/025-extractor-derived-fields/spec.md`

## Summary

Implement the first real Extractor Beast slice by deriving stable fallback `subject` and `summary` fields during ingest while preserving explicit caller-provided values.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/memory/ingest.py`, `aegis_py/memory/factory.py`, current Python integration tests  
**Storage**: existing SQLite `memories` rows with `subject` and `summary` columns  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: use deterministic local heuristics only, preserve explicit caller values, keep logic inside the `memory` module  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- add a small local extractor helper for derived fields
- derive only when caller omits `subject` and `summary`
- keep heuristics deterministic and bounded
- validate through integration coverage rather than introducing a new runtime surface

## Work Plan

1. reconcile `.planning/STATE.md` to feature `025-extractor-derived-fields`
2. add a memory-local extractor helper for fallback subject and summary derivation
3. wire `IngestEngine` to apply fallback derived fields without overriding explicit values
4. extend integration coverage for derived fields and explicit override preservation
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 025-extractor-derived-fields:

- ingest now derives fallback `subject` and `summary` through a deterministic local extractor helper when callers omit those fields
- explicit caller-provided `subject` and `summary` still win unchanged
- Python integration coverage now proves both derived-field behavior and explicit override preservation

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/025-extractor-derived-fields`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `732ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `84 passed in 2.84s`
