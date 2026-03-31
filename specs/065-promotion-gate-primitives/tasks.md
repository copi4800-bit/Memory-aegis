# Tasks: Promotion Gate Primitives

**Input**: Design documents from `/specs/065-promotion-gate-primitives/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Candidate And Gate Primitives

- [x] T001 [CORE] Add a bounded internal candidate representation before promotion into normal memory storage.
- [x] T002 [CORE] Add a promotion-gate helper that evaluates evidence presence and bounded admission signals.
- [x] T003 [CORE] Thread canonical ingest through the promotion seam without changing public retrieval payloads.

## Phase 2: Validation

- [x] T004 [TEST] Add runtime and integration tests for promotable and non-promotable candidate outcomes.
- [x] T005 [TEST] Re-run Python and host contract suites.

## Phase 3: GSD Integration

- [x] T006 [DOCS] Update `.planning/ROADMAP.md` so `065` becomes the active architecture tranche after `064`.
- [x] T007 [DOCS] Update `.planning/STATE.md` so the next architecture focus points at promotion-gate primitives rather than the full state-machine slice.
