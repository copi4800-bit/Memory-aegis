# Tasks: Production Observability

**Input**: Design documents from `/specs/071-production-observability/`
**Prerequisites**: plan.md, spec.md

## Phase 1: Setup

- [x] T001 Create feature spec and plan in `specs/071-production-observability/`
- [x] T002 Define the validation command set for the tranche

## Phase 2: Foundation

- [x] T003 Add a shared runtime observability module under `aegis_py/observability/`
- [x] T004 Export the new observability helpers through the package surface

## Phase 3: User Story 1 - Structured Runtime Events (Priority: P1)

- [x] T005 [US1] Add a stable structured event builder for runtime actions
- [x] T006 [US1] Add focused tests for the event contract in `tests/test_observability_runtime.py`

## Phase 4: User Story 2 - Operator Metrics Snapshot (Priority: P1)

- [x] T007 [US2] Add a bounded process-local metrics registry
- [x] T008 [US2] Expose an observability snapshot surface from `AegisApp`
- [x] T009 [US2] Add tests for counters, latency summaries, and recent-event ordering

## Phase 5: User Story 3 - Core Flow Instrumentation (Priority: P2)

- [x] T010 [US3] Instrument memory write and search flows
- [x] T011 [US3] Instrument background plan/apply/rollback flows
- [x] T012 [US3] Instrument backup and restore flows
- [x] T013 [US3] Expand instrumentation to consumer-facing summary helpers if signal is still missing

## Phase 6: Validation

- [x] T014 Run the observability-focused validation command set
- [x] T015 Record remaining gaps for a later observability tranche
