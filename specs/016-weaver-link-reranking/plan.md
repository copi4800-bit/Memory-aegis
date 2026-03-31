# Implementation Plan: Weaver Link Reranking

**Branch**: `016-weaver-link-reranking` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/016-weaver-link-reranking/spec.md)
**Input**: Feature specification from `/specs/016-weaver-link-reranking/spec.md`

## Summary

Refine Weaver link expansion scoring so nearer hops and stronger link types are prioritized more deliberately.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: existing retrieval pipeline and Weaver link layer  
**Storage**: local SQLite  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: preserve lexical-first behavior, keep scoring explainable, stay bounded and local-only  

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

- link expansion scoring now runs through a dedicated reranking helper
- first-hop links outrank second-hop links under similar conditions
- stronger typed links now score above weaker generic links

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/016-weaver-link-reranking`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `80 passed in 1.75s`
