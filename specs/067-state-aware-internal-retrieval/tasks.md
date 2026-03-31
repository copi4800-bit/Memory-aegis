# Tasks: State-Aware Internal Retrieval

**Input**: Design documents from `/specs/067-state-aware-internal-retrieval/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Internal State-Aware Retrieval

- [x] T001 [CORE] Add bounded internal retrieval helpers that consume `admission_state`.
- [x] T002 [CORE] Add bounded policy or trust shaping that uses `admission_state` without changing public payloads.

## Phase 2: Validation

- [x] T003 [TEST] Add retrieval and integration tests for state-aware internal behavior.
- [x] T004 [TEST] Re-run Python and host contract suites.

## Phase 3: GSD Integration

- [x] T005 [DOCS] Update `.planning/ROADMAP.md` so `067` becomes the active architecture tranche after `066`.
- [x] T006 [DOCS] Update `.planning/STATE.md` so the next architecture focus points at state-aware internal retrieval rather than broad retrieval rewrite.
