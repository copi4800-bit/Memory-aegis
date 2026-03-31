# Implementation Plan: Decay Type-Aware Retention

**Branch**: `033-decay-type-aware-retention` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/033-decay-type-aware-retention/spec.md)
**Input**: Feature specification from `/specs/033-decay-type-aware-retention/spec.md`

## Summary

Implement the first Tranche C slice by applying type-aware decay half-lives during maintenance while preserving the explicit uniform override path.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/hygiene/engine.py`, `aegis_py/storage/manager.py`, current lifecycle tests  
**Storage**: existing SQLite `memories.activation_score`, `last_accessed_at`, and `updated_at` fields  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep decay deterministic and local-only, preserve existing explicit override behavior, avoid destructive lifecycle automation  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- define default half-lives by memory type in the hygiene layer
- let storage decay apply either the type-aware map or one explicit override
- keep episodic at the current baseline to minimize behavioral surprise
- verify with lifecycle tests rather than changing public host surfaces

## Work Plan

1. reconcile `.planning/STATE.md` to feature `033-decay-type-aware-retention`
2. add default type-aware half-lives in the hygiene engine
3. extend storage decay to accept per-type half-lives or a uniform override
4. add hygiene test coverage for type-aware decay and explicit override behavior
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

- `./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`: pass
  - resolved `FEATURE_DIR` to `/home/hali/.openclaw/extensions/memory-aegis-v7/specs/033-decay-type-aware-retention`
  - reported `AVAILABLE_DOCS` containing `tasks.md`
- `npm run lint`: pass
- `npm run test:bootstrap`: pass, 17 tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`: pass, 93 passed in 1.99s
