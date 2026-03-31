# Implementation Plan: Classifier Lane Assignment

**Branch**: `027-classifier-lane-assignment` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/027-classifier-lane-assignment/spec.md)
**Input**: Feature specification from `/specs/027-classifier-lane-assignment/spec.md`

## Summary

Implement the third Tranche A slice by inferring conservative memory lanes when callers omit `type`, while preserving explicit lane choices.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/memory/ingest.py`, app/MCP/CLI store surfaces, Tranche A slices from `025` and `026`  
**Storage**: existing SQLite `memories.type` field  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep inference deterministic and conservative, do not override explicit types, bias weak signals to `episodic`  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- add a small memory-local lane classifier
- infer only when callers omit `type` or pass `None`
- keep heuristics narrow and bias weak signals to `episodic`
- update the public Python-owned store surfaces so omitted lane selection can actually reach the classifier

## Work Plan

1. reconcile `.planning/STATE.md` to feature `027-classifier-lane-assignment`
2. add a deterministic lane classifier helper in the `memory` module
3. wire `IngestEngine` to infer type only when callers omit it
4. allow Python-owned store surfaces to pass omitted `type` through instead of forcing `"episodic"`
5. extend integration coverage for inferred lanes and explicit preservation
6. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 027-classifier-lane-assignment:

- ingest now infers conservative memory lanes when callers omit `type`
- explicit caller-provided lanes still remain authoritative and unchanged
- Python-owned store surfaces now allow omitted `type` to reach the classifier instead of forcing `"episodic"` up front

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/027-classifier-lane-assignment`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `615ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `86 passed in 3.04s`
