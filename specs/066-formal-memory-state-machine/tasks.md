# Tasks: Formal Memory State Machine

**Input**: Design documents from `/specs/066-formal-memory-state-machine/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: State Model

- [x] T001 [CORE] Add an explicit internal admission-aware state taxonomy.
- [x] T002 [CORE] Map canonical ingest and promotion outcomes into the new state model.
- [x] T003 [CORE] Preserve compatibility with existing lifecycle-oriented statuses during the transition.

## Phase 2: Validation

- [x] T004 [TEST] Add storage/runtime/integration tests for explicit states and compatibility mapping.
- [x] T005 [TEST] Re-run Python and host contract suites.

## Phase 3: GSD Integration

- [x] T006 [DOCS] Update `.planning/ROADMAP.md` so `066` becomes the active architecture tranche after `065`.
- [x] T007 [DOCS] Update `.planning/STATE.md` so the next architecture focus points at the formal state model rather than retrieval rewrite.
