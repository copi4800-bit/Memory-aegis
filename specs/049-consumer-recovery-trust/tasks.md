# Tasks: Consumer Recovery Trust

**Input**: Design documents from `/specs/049-consumer-recovery-trust/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Python Summary Helpers

- [x] T001 [CORE] Add plain-language doctor and recovery summary helpers in `aegis_py/app.py`.
- [x] T002 [CORE] Keep underlying backup, preview, restore, and doctor payloads unchanged for machine consumers.

## Phase 2: CLI Trust Surface

- [x] T003 [CORE] Update `aegis_py/cli.py` so doctor and backup/restore commands are summary-first by default and support explicit JSON output.

## Phase 3: Plugin Trust Surface

- [x] T004 [CORE] Update `index.ts` so `memory_doctor` uses human-readable primary content while preserving structured `details`.

## Phase 4: Validation

- [x] T005 [TEST] Add or update user-surface tests in `tests/test_user_surface.py` for doctor and recovery summaries.
- [x] T006 [TEST] Add or update backup tests in `tests/operations/test_backup.py` where summary behavior matters.
- [x] T007 [TEST] Update `test/integration/python-adapter-plugin.test.ts` for the new `memory_doctor` primary content.

## Phase 5: Closeout

- [x] T008 [TEST] Re-run targeted tests and the full Python suite.
- [x] T009 [DOCS] Record validation evidence for `049-consumer-recovery-trust` in `plan.md`.
