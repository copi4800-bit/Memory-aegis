# Implementation Plan: Weaver Multi-Hop Bounded

**Branch**: `015-weaver-multi-hop-bounded` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/015-weaver-multi-hop-bounded/spec.md)
**Input**: Feature specification from `/specs/015-weaver-multi-hop-bounded/spec.md`

## Summary

Add one bounded extra explicit-link hop after lexical seed recall so context packs can widen context slightly without losing explainability or control.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: existing Weaver link layer, retrieval pipeline, Python serializers  
**Storage**: local SQLite  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: lexical-first only, max extra hop = 1, scope-safe, budget-bounded, explainable payloads only  

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

- context-pack now supports one bounded extra explicit-link hop after lexical seed recall
- multi-hop results expose hop count and link explanation metadata
- docs now describe the bounded multi-hop rule

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/015-weaver-multi-hop-bounded`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `79 passed in 1.83s`
