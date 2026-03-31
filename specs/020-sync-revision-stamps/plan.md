# Implementation Plan: Sync Revision Stamps

**Branch**: `020-sync-revision-stamps` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/020-sync-revision-stamps/spec.md)
**Input**: Feature specification from `/specs/020-sync-revision-stamps/spec.md`

## Summary

Add a lightweight scope revision counter and include it in sync envelopes, preview, and import results.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: current sync envelope flows and SQLite storage  
**Storage**: local SQLite plus file-based JSON envelopes  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: local-first, file-based sync, simple monotonic revision counters, no remote backend  

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

- sync-eligible scopes now maintain lightweight local revision counters
- sync envelopes now carry scope revision
- preview and import now expose local versus incoming scope revision

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/020-sync-revision-stamps`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `83 passed in 2.67s`
