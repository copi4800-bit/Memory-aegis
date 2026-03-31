# Implementation Plan: Weaver Link Types

**Branch**: `013-weaver-link-types` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/013-weaver-link-types/spec.md)
**Input**: Feature specification from `/specs/013-weaver-link-types/spec.md`

## Summary

Add a second narrow auto-link rule that ties same-subject procedural and semantic memories together in the same scope, and backfill that structure through rebuild.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: existing Aegis Python runtime and Weaver link layer  
**Storage**: local SQLite  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: same-scope only, same-subject only, procedural/semantic only, bounded peer count  

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

- same-subject procedural and semantic memories now auto-create explicit typed links in the same scope
- rebuild now backfills missing typed links for existing active memories
- docs now describe the typed auto-link rule

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/013-weaver-link-types`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `78 passed in 2.67s`
