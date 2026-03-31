# Tasks: Guided Host Integration

**Input**: Design documents from `/specs/051-guided-host-integration/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Consumer Host Surface

- [x] T001 [DOCS] Add explicit consumer/default tool surface metadata to `openclaw.plugin.json`.
- [x] T002 [DOCS] Align `README.md` with the same default versus advanced host path.

## Phase 2: Legacy Boundary Cleanup

- [x] T003 [CORE] Convert `src/ux/onboarding.ts` into an explicit legacy stub that redirects to the Python-owned onboarding path.

## Phase 3: Validation

- [x] T004 [TEST] Update `tests/test_python_only_runtime_contract.py` to lock the consumer surface metadata.
- [x] T005 [TEST] Update `tests/test_python_only_runtime_contract.py` to lock the legacy onboarding stub behavior.

## Phase 4: Closeout

- [x] T006 [TEST] Re-run the contract test suite for this feature.
- [x] T007 [DOCS] Record validation evidence for `051-guided-host-integration` in `plan.md`.
