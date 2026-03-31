# Implementation Plan: Entity Structure Lite

**Branch**: `017-entity-structure-lite` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/017-entity-structure-lite/spec.md)
**Input**: Feature specification from `/specs/017-entity-structure-lite/spec.md`

## Summary

Add heuristic entity extraction on ingest and use shared entity tags as one bounded context expansion signal.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: existing Python ingest and retrieval pipeline  
**Storage**: local SQLite with metadata JSON already available on memories  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: no LLM dependency, bounded entity expansion, explainable payloads, preserve lexical-first behavior  

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

- ingest now stores lightweight normalized entity tags in memory metadata
- context-pack now supports bounded `entity_expansion` after link expansion
- docs now describe the entity-structure-lite step

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/017-entity-structure-lite`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `81 passed in 2.85s`
