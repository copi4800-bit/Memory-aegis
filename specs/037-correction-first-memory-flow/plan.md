# Implementation Plan: Correction-First Memory Flow

**Branch**: `037-correction-first-memory-flow` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)

## Summary

Implement a correction-first memory architecture that allows new information to supersede older, incorrect information. This involves adding correction signal detection to the ingest pipeline, enhancing the conflict manager to identify correction candidates, and implementing a recency-based resolution policy in the consolidator.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/memory`, `aegis_py/conflict`, `aegis_py/hygiene`  
**Storage**: SQLite (`memory_aegis.db`, `conflicts` table)  
**Testing**: `pytest` with temporal contradiction pairs  
**Performance Goals**: Correction detection should be integrated into the O(1) or O(N_subject) ingest path.

## Implementation Steps

### Phase 1: Correction Signal Detection
1. Create `aegis_py/memory/correction.py` to define `CorrectionDetector`.
2. Implement regex patterns for English and Vietnamese (e.g., "no longer", "instead of", "corrected to", "không còn là", "thay vì").
3. Update `IngestEngine.ingest` to run `CorrectionDetector` and tag memories with `is_correction: True` if signals are found.

### Phase 2: Enhanced Conflict Detection (Meerkat)
1. Update `ConflictManager.scan_conflicts` in `aegis_py/conflict/core.py` to check for `is_correction` tags.
2. If a new memory is a correction, prioritize finding the older active memory in the same subject as its target.
3. If no explicit tag, but a direct contradiction is detected, mark it as a `type: correction_candidate`.

### Phase 3: Consolidator Beast (Resolution)
1. Implement `ConsolidatorBeast` in `aegis_py/hygiene/consolidator.py`.
2. Implement `resolve_corrections` logic:
    - If a conflict is a `correction_candidate` or has an explicit `is_correction` tag:
    - Automatically transition the older memory to `superseded`.
    - Update the new memory's metadata with `corrected_from: [old_id]`.
    - Close the conflict as `resolved_by_correction`.

### Phase 4: Retrieval Filtering
1. Update `run_scoped_search` in `aegis_py/retrieval/engine.py` to explicitly filter out `status = 'superseded'` records by default.
2. Ensure `SearchPipeline` preserves this filter.

### Phase 5: Validation
1. Create tests for:
    - Explicit correction (User Story 1).
    - Implicit contradiction (User Story 2).
    - Multi-step correction (Verifying the latest version is the only active one).

## Validation Evidence

Observed on 2026-03-24 after reconciling and completing feature `037-correction-first-memory-flow`:

- `CorrectionDetector` is active in the ingest path with English and Vietnamese trigger coverage.
- same-subject contradiction candidates now resolve through the bounded recency-preference policy during maintenance, not only explicit correction-tag flows.
- correction lineage remains visible through `corrected_from` metadata and `corrected_by_newer_info` lifecycle events.
- the feature directory now follows canonical Spec Kit filenames: `spec.md`, `plan.md`, and `tasks.md`.

Validation results:

- `SPECIFY_FEATURE=037-correction-first-memory-flow ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/037-correction-first-memory-flow`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/memory/test_correction_detector.py tests/memory/test_fact_correction.py tests/hygiene/test_contradiction_resolve.py`
  - passed
  - `6 passed`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `107 passed in 2.50s`
