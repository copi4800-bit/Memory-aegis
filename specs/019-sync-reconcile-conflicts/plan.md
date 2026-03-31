# Implementation Plan: Sync Reconcile Conflicts

**Branch**: `019-sync-reconcile-conflicts` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/019-sync-reconcile-conflicts/spec.md)
**Input**: Feature specification from `/specs/019-sync-reconcile-conflicts/spec.md`

## Summary

Add detailed reconcile diffs for sync envelope preview and richer reconcile stats for sync import.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: current sync envelope flows in `aegis_py/operations.py`  
**Storage**: local SQLite plus file-based JSON envelopes  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: preserve file-based sync, local-first authority, no remote backend  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- sync preview now returns categorized reconcile diffs
- sync import now reports inserted/replaced/unchanged counts
- docs now describe the richer reconcile behavior

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/019-sync-reconcile-conflicts`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `83 passed in 2.74s`
