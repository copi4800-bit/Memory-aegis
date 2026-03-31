# Implementation Plan: Normalizer Subject Canonicalization

**Branch**: `026-normalizer-subject-canonicalization` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/026-normalizer-subject-canonicalization/spec.md)
**Input**: Feature specification from `/specs/026-normalizer-subject-canonicalization/spec.md`

## Summary

Implement the second Tranche A slice by canonicalizing subject keys during ingest while preserving explicit unlabeled-memory semantics.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/memory/ingest.py`, Extractor slice from `025`, Python integration tests  
**Storage**: existing SQLite `memories.subject` field  
**Testing**: canonical prerequisite check, `npm run lint`, `npm run test:bootstrap`, `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`  
**Constraints**: keep normalization deterministic and local, normalize only non-empty strings, preserve explicit `None` semantics for taxonomy flows  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- add a small memory-local subject normalizer
- apply normalization to both explicit and derived non-empty subjects
- keep explicit `None` untouched
- use integration tests to guard against regressions in taxonomy cleanup and subject-dependent behavior

## Work Plan

1. reconcile `.planning/STATE.md` to feature `026-normalizer-subject-canonicalization`
2. add a deterministic subject normalizer helper in the `memory` module
3. wire `IngestEngine` to normalize non-empty subjects after extraction or explicit input
4. extend integration coverage for subject canonicalization and explicit null preservation
5. run canonical validation and record evidence

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24 after implementing 026-normalizer-subject-canonicalization:

- ingest now canonicalizes non-empty subject strings into a stable dotted lowercase form through a deterministic local normalizer
- derived subjects and explicit subject strings now share the same canonicalization path
- explicit `subject=None` still remains unlabeled so taxonomy cleanup semantics are preserved

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/026-normalizer-subject-canonicalization`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed
  - `1` file passed, `17` tests passed
  - duration: `672ms`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `85 passed in 2.83s`
