# Implementation Plan: Guardian Partial Scope Rejection

**Branch**: `031-guardian-partial-scope-rejection` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/031-guardian-partial-scope-rejection/spec.md)
**Input**: Feature specification from `/specs/031-guardian-partial-scope-rejection/spec.md`

## Summary

Implement the next Guardian slice by rejecting ambiguous partial retrieval scopes while preserving valid full-scope and default-scope behavior.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/app.py`, `aegis_py/mcp/server.py`, current retrieval surfaces  
**Storage**: existing local scope fields and current default retrieval scope behavior  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep the contract additive and strict, preserve valid retrieval flows, avoid changing public tool names  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- normalize retrieval scope pairs in one app-owned helper
- reject partial scope inputs explicitly
- preserve default scope behavior when both fields are omitted
- preserve normal retrieval when both fields are present

## Work Plan

1. reconcile `.planning/STATE.md` to feature `031-guardian-partial-scope-rejection`
2. add a retrieval scope-pair normalizer in the app layer
3. wire search and context-pack surfaces through the normalizer
4. extend integration coverage for partial-scope rejection and valid-scope acceptance
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 031-guardian-partial-scope-rejection:

- retrieval surfaces now reject partial scope inputs instead of silently accepting ambiguous boundary contracts
- valid full-scope retrieval still works unchanged
- omitting both scope fields still falls back to the stable default scope pair

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/031-guardian-partial-scope-rejection`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `760ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `90 passed in 2.93s`
