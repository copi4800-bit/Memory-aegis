# Tasks: Governance Automation With Human Override

**Input**: Design documents from `/specs/043-governance-automation/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Policy Configuration & Storage

- [x] T001 [DB] Update SQLite schema in `aegis_py/storage/schema.sql` to store `PolicyMatrix` configuration and an `autonomous_audit_log`.
- [x] T002 [GOV] Implement `PolicyMatrix` loading and saving in `aegis_py/governance/policy.py`.
- [x] T003 [TEST] Write tests for policy matrix serialization and evaluation logic.

## Phase 2: Autonomous Execution & Explanations

- [x] T004 [GOV] Create `AutonomousExecutor` in `aegis_py/governance/automation.py` to wrap any automated mutation.
- [x] T005 [GOV] Implement confidence/quorum gates inside the executor for operations like `auto_resolve`.
- [x] T006 [GOV] Ensure the executor writes an explanation payload to the `autonomous_audit_log` before committing changes.
- [x] T007 [TEST] Write tests to ensure blocked operations fail gracefully and approved operations leave an audit trail.

## Phase 3: Rollback Mechanisms

- [x] T008 [GOV] Implement `RollbackManager` in `aegis_py/governance/rollback.py`.
- [x] T009 [GOV] Add logic to parse a specific `autonomous_audit_log` entry and reverse the database operations (e.g., un-consolidate, un-archive).
- [x] T010 [TEST] Write integration tests proving byte-for-byte state restoration after a rollback.

## Phase 4: Integration & Status

- [x] T011 [GSD] Update `.planning/STATE.md` to reflect ongoing work on `043-governance-automation`.
- [x] T012 [DOCS] Write usage documentation for the new governance controls.