# Tasks: Correction-First Memory Flow

**Input**: Design documents from `spec.md`, `plan.md`

## Phase 1: Setup & Signal Detection

- [x] T001 [P] [US1] Create `aegis_py/memory/correction.py` and implement `CorrectionDetector`.
- [x] T002 [US1] Add English triggers to `CorrectionDetector` (Regex).
- [x] T003 [US1] Add Vietnamese triggers to `CorrectionDetector` (Regex).
- [x] T004 [US1] Integrate `CorrectionDetector` into `IngestEngine.ingest` and add `is_correction` tag to metadata.

**Checkpoint**: Ingest engine can now recognize when a user is attempting to correct a fact.

---

## Phase 2: Conflict Manager Enhancement (Meerkat)

- [x] T005 [US2] Update `ConflictManager.scan_conflicts` to prioritize `is_correction` tagged memories.
- [x] T006 [US2] Implement `type: correction_candidate` logging in `conflicts` table.
- [x] T007 [US2] Implement recency detection (comparing `created_at`) within `ConflictManager` to identify which memory is the newer "truth".

**Checkpoint**: `Meerkat` can now identify correction candidates automatically.

---

## Phase 3: Consolidator Beast Implementation

- [x] T008 [P] [US2] Create `aegis_py/hygiene/consolidator.py` and define `ConsolidatorBeast`.
- [x] T009 [US2] Implement `ConsolidatorBeast.resolve_corrections` to transition older memories to `superseded`.
- [x] T010 [US2, US3] Implement `_link_correction_history` to update the new memory's metadata with `corrected_from`.
- [x] T011 [US2] Hook `ConsolidatorBeast` into `HygieneEngine.run_maintenance`.

**Checkpoint**: Background resolution of corrections is functional.

---

## Phase 4: Retrieval & Validation

- [x] T012 [US1] Update `run_scoped_search` in `aegis_py/retrieval/engine.py` to filter out `superseded` memories.
- [x] T013 [P] [US1] Unit test for `CorrectionDetector` in `tests/memory/test_correction_detector.py`.
- [x] T014 [US1] Integration test for explicit correction in `tests/memory/test_fact_correction.py`.
- [x] T015 [US2] Integration test for implicit contradiction resolution in `tests/hygiene/test_contradiction_resolve.py`.

**Checkpoint**: Slice 037 is validated.
