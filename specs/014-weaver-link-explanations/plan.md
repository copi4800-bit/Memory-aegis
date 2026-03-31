# Implementation Plan: Weaver Link Explanations

**Branch**: `014-weaver-link-explanations` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/014-weaver-link-explanations/spec.md)
**Input**: Feature specification from `/specs/014-weaver-link-explanations/spec.md`

## Summary

Add richer explanation fields for explicit link-driven expansions so context-pack payloads clearly show which link and which seed memory caused an expansion.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: existing Weaver link layer, retrieval search pipeline, Python surface serializers  
**Storage**: local SQLite  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: preserve current public shapes, do not invent link fields for lexical-only results, keep Python-owned semantics  

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

- context-pack link expansions now expose link type, source seed memory ID, and link metadata
- serialized Python retrieval payloads now preserve those explanation fields
- docs now describe richer Weaver explanation behavior

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/014-weaver-link-explanations`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `78 passed in 1.93s`
