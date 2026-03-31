# Implementation Plan: Navigator Lexical Subject Gating

**Branch**: `032-navigator-lexical-subject-gating` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/032-navigator-lexical-subject-gating/spec.md)
**Input**: Feature specification from `/specs/032-navigator-lexical-subject-gating/spec.md`

## Summary

Implement the next Navigator slice by restricting subject expansion seeds to lexical hits so secondary expansion stages cannot recursively widen recall.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/retrieval/search.py`, current entity/link/subject expansion flow  
**Storage**: existing local SQLite retrieval data and same-subject expansion behavior  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep lexical-first behavior intact, change only the subject-expansion seed rule, avoid broad retrieval redesign  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- seed subject expansion from lexical hits only
- preserve link and entity expansion as retrieval stages, but do not let them spawn subject-expansion cascades
- keep same-subject lexical expansion behavior intact
- validate with one regression-style integration test plus existing retrieval coverage

## Work Plan

1. reconcile `.planning/STATE.md` to feature `032-navigator-lexical-subject-gating`
2. restrict subject-expansion seed subjects in the retrieval pipeline
3. add integration coverage for lexical-only subject seeding
4. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 032-navigator-lexical-subject-gating:

- subject expansion now seeds only from lexical hits
- link and entity expansion results no longer introduce new subject-expansion seed subjects
- lexical-led same-subject expansion still remains active

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/032-navigator-lexical-subject-gating`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `781ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `91 passed in 2.86s`
