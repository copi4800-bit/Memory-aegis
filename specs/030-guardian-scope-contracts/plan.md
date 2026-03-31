# Implementation Plan: Guardian Scope Contracts

**Branch**: `030-guardian-scope-contracts` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/030-guardian-scope-contracts/spec.md)
**Input**: Feature specification from `/specs/030-guardian-scope-contracts/spec.md`

## Summary

Implement the first Guardian slice by making scope boundary contracts explicit in retrieval reasons and context-pack payloads.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/retrieval/contract.py`, `aegis_py/retrieval/engine.py`, `aegis_py/app.py`, `aegis_py/surface.py`  
**Storage**: existing local SQLite scope fields and global-scope fallback behavior  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: preserve existing result ordering, keep payload additions additive, and make scope contracts explicit without adding a new retrieval subsystem  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- expose guardian-style scope signals through additive metadata and reason tags
- keep exact-scope retrieval primary
- mark global fallback explicitly when enabled
- avoid changing search payload shape beyond added reasoning and context-pack metadata

## Work Plan

1. reconcile `.planning/STATE.md` to feature `030-guardian-scope-contracts`
2. add explicit global fallback reasoning in retrieval contract building
3. add boundary contract metadata to context packs
4. extend integration coverage for guardian scope signals
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 030-guardian-scope-contracts:

- retrieval reasons now mark global-scope fallback explicitly through `global_fallback`
- `memory_context_pack` now surfaces a `boundary` contract block describing exact scope lock and global fallback policy
- guardian scope signals are additive and do not change existing result ordering

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/030-guardian-scope-contracts`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `1.03s`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `89 passed in 2.80s`
