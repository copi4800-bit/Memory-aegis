# Tasks: Evidence Log Foundation

**Input**: Design documents from `/specs/063-evidence-log-foundation/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Schema And Models

- [x] T001 [CORE] Add append-only evidence event storage to the SQLite schema.
- [x] T002 [CORE] Extend storage models and manager APIs for evidence event persistence and lookup.

## Phase 2: Canonical Ingest Linkage

- [x] T003 [CORE] Update canonical ingest/memory persistence so new memory writes create evidence events.
- [x] T004 [CORE] Add stable evidence linkage from memory records without breaking current public payloads.

## Phase 3: Validation

- [x] T005 [TEST] Add storage tests for append-only evidence behavior.
- [x] T006 [TEST] Add integration tests for evidence-backed memory ingest and backward-compatible retrieval.
- [x] T007 [TEST] Re-run Python and host contract suites.

## Phase 4: GSD Integration

- [x] T008 [DOCS] Update `.planning/ROADMAP.md` as `063` becomes the active architecture implementation tranche.
- [x] T009 [DOCS] Update `.planning/STATE.md` to reflect active execution against the v4-to-v7 roadmap.
