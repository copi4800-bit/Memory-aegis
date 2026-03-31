# Tasks: Internal Evidence Consumption

**Input**: Design documents from `/specs/064-internal-evidence-consumption/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Internal Runtime Helpers

- [x] T001 [CORE] Add stable internal helpers for resolving evidence rows linked to a memory.
- [x] T002 [CORE] Add bounded runtime inspection/reporting for evidence coverage without changing public retrieval payloads.

## Phase 2: Validation

- [x] T003 [TEST] Add storage/runtime tests for evidence lookup and evidence coverage reporting.
- [x] T004 [TEST] Add integration tests showing evidence consumption works while public contracts stay stable.
- [x] T005 [TEST] Re-run Python and host contract suites.

## Phase 3: GSD Integration

- [x] T006 [DOCS] Update `.planning/ROADMAP.md` so `064` becomes the active architecture tranche after `063`.
- [x] T007 [DOCS] Update `.planning/STATE.md` so the next architecture focus points at internal evidence consumption rather than full promotion gating.
