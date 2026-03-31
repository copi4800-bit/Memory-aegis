# Tasks: Production Hardening

**Input**: Design documents from `/specs/070-production-hardening/`
**Prerequisites**: plan.md, spec.md

**Tests**: This feature is test-heavy by design. Every task should either add or strengthen acceptance, regression, or invariant coverage.

**Organization**: Tasks are grouped by user story to keep the tranche independently verifiable.

## Phase 1: Setup

- [x] T001 Create feature spec and plan in `specs/070-production-hardening/`
- [x] T002 Define the validation command set for this tranche in `specs/070-production-hardening/plan.md` or repo docs

## Phase 2: Foundational

- [x] T003 Create focused acceptance test layout under `tests/acceptance/`
- [x] T004 Create focused regression test layout under `tests/regression/`
- [ ] T005 Add shared temporary-db and temporary-workspace helpers only where existing test helpers are insufficient

## Phase 3: User Story 1 - Critical Flow Acceptance Coverage (Priority: P1)

**Goal**: Cover the highest-signal production flows end-to-end.

**Independent Test**: Run the focused acceptance suite against temporary databases and workspaces.

- [x] T006 [P] [US1] Add acceptance coverage for remember/recall in `tests/acceptance/test_acceptance_memory_flows.py`
- [x] T007 [P] [US1] Add acceptance coverage for backup/restore in `tests/acceptance/test_acceptance_recovery_flows.py`
- [x] T008 [P] [US1] Add acceptance coverage for sync export/preview/import in `tests/acceptance/test_acceptance_sync_flows.py`
- [x] T009 [P] [US1] Add acceptance coverage for background apply/rollback in `tests/acceptance/test_acceptance_background_flows.py`

## Phase 4: User Story 2 - Historical Regression Locking (Priority: P1)

**Goal**: Prevent old high-signal failures from returning.

**Independent Test**: Run the regression suite and confirm the known failure classes remain fixed.

- [x] T010 [P] [US2] Add regression coverage for dry-run non-mutation in `tests/regression/test_regression_dry_run_safety.py`
- [x] T011 [P] [US2] Add regression coverage for rollback completeness in `tests/regression/test_regression_rollback_integrity.py`
- [x] T012 [P] [US2] Add regression coverage for scope-policy and sync contract stability in `tests/regression/test_regression_scope_policy_sync_contract.py`
- [x] T013 [US2] Document the selected regression classes and why they matter in `specs/070-production-hardening/plan.md`

## Phase 5: User Story 3 - Data-Safety Invariants (Priority: P2)

**Goal**: Prove the runtime obeys non-negotiable safety rules.

**Independent Test**: Run the invariant-focused suite and confirm scope isolation and mutation safety.

- [x] T014 [P] [US3] Add scope-isolation invariants in `tests/acceptance/test_acceptance_scope_isolation.py`
- [x] T015 [P] [US3] Add restore-safety invariants in `tests/regression/test_regression_restore_contract.py`
- [x] T016 [P] [US3] Add preview/dry-run state-stability checks in `tests/regression/test_regression_preview_state_stability.py`

## Phase 6: Polish

- [x] T017 Add a one-command focused validation recipe for the tranche
- [x] T018 Run the focused acceptance and regression command set
- [x] T019 Summarize any remaining hardening gaps discovered during the tranche
