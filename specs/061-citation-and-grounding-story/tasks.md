# Tasks: Citation And Grounding Story

**Input**: Design documents from `/specs/061-citation-and-grounding-story/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Grounding Demo

- [x] T001 [CORE] Add one runnable grounding demo that prints provenance, trust state, trust reason, and reasons from the current runtime.
- [x] T002 [DOCS] Add README trust/grounding copy tied to `search` and `context-pack`.

## Phase 2: Shipping

- [x] T003 [CORE] Ship the grounding demo in the published package and release bundle.

## Phase 3: Validation

- [x] T004 [TEST] Update runtime/package contract tests for the grounding story.
- [x] T005 [TEST] Add grounding demo output coverage.
- [x] T006 [TEST] Re-run targeted coverage and the full Python suite.

## Phase 4: GSD Integration

- [x] T007 [DOCS] Update `.planning/ROADMAP.md` for the grounding-story slice.
- [x] T008 [DOCS] Update `.planning/STATE.md` so this slice is recorded as the tranche-closing trust step.
