# Implementation Plan: Weaver Auto Linking

**Branch**: `012-weaver-auto-linking` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/012-weaver-auto-linking/spec.md)
**Input**: Feature specification from `/specs/012-weaver-auto-linking/spec.md`

## Summary

Add a narrow auto-linking rule for same-subject memories in the same scope, and backfill that structure through the rebuild flow for existing datasets.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: existing `aegis_py` runtime, `memory_links` table, current rebuild and ingest flows  
**Storage**: local SQLite  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Target Platform**: local Python runtime and existing public surfaces  
**Project Type**: Brownfield runtime enhancement  
**Performance Goals**: bounded auto-linking with no meaningful regression to ingest or rebuild flows  
**Constraints**: same-scope only, same-subject only, bounded peer count, no semantic guessing  
**Scale/Scope**: ingest path, rebuild path, storage helpers, docs, tests, workflow artifacts

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. All behavior stays in local SQLite.
- `Brownfield Refactor Over Rewrite`: Pass. The feature extends the existing Weaver link layer.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Auto-created links remain explicit rows and are surfaced as explicit link expansion later.
- `Safe Memory Mutation By Default`: Pass. Mutation rule is narrow, bounded, and scope-safe.
- `Measured Simplicity`: Pass. The rule is same-subject linking only, not open-ended semantic linking.

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- same-scope memories with the same non-empty subject now auto-create explicit `same_subject` links on ingest
- rebuild now backfills missing `same_subject` links for existing active memories
- docs now describe the auto-link rule as narrow and bounded

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/012-weaver-auto-linking`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `76 passed in 1.71s`
