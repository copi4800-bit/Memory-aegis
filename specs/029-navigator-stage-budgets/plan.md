# Implementation Plan: Navigator Stage Budgets

**Branch**: `029-navigator-stage-budgets` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/029-navigator-stage-budgets/spec.md)
**Input**: Feature specification from `/specs/029-navigator-stage-budgets/spec.md`

## Summary

Implement the first Tranche B slice by adding explicit per-stage budgets for retrieval expansion and surfacing stage counts in context packs.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/retrieval/search.py`, `aegis_py/surface.py`, current context-pack contract  
**Storage**: existing local SQLite retrieval data and explicit link/entity/subject expansion sources  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep navigation lexical-first, enforce small deterministic stage budgets, and avoid adding a broad retrieval orchestration subsystem  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- add explicit stage budgets inside the retrieval pipeline
- count results by retrieval stage and expose those counts in context packs
- keep lexical recall primary and expansion bounded
- avoid changing public tool names or introducing a new retrieval service layer

## Work Plan

1. reconcile `.planning/STATE.md` to feature `029-navigator-stage-budgets`
2. add per-stage expansion budgets in the retrieval pipeline
3. surface stage counts in the context-pack payload
4. extend integration coverage for bounded expansion and stage counts
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 029-navigator-stage-budgets:

- retrieval expansion stages now respect explicit per-stage budgets for link, multi-hop, entity, and subject expansion
- lexical recall remains primary while expansion stages stay bounded
- context packs now report `stage_counts` so bounded navigation is visible and reviewable

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/029-navigator-stage-budgets`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `747ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `88 passed in 2.73s`
