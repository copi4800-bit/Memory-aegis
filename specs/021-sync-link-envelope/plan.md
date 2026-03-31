# Implementation Plan: Sync Link Envelope

**Branch**: `021-sync-link-envelope` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/021-sync-link-envelope/spec.md)
**Input**: Feature specification from `/specs/021-sync-link-envelope/spec.md`

## Summary

Extend sync envelopes to carry explicit `memory_links`, preview link diffs, and import links after memories.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: current sync envelope and Weaver link flows  
**Storage**: local SQLite plus file-based JSON envelopes  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: scope-safe links only, local-first, file-based sync, preserve existing sync behavior for memories  

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

Observed on 2026-03-24 after implementing 021-sync-link-envelope:

- sync envelopes now carry both memories and explicit scope-local links
- sync preview/import now report link counts and import links after memories
- docs now describe link-aware sync envelopes

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/021-sync-link-envelope`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `332ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `83 passed in 1.94s`
