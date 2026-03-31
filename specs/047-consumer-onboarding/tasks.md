# Tasks: Consumer Onboarding

**Input**: Design documents from `/specs/047-consumer-onboarding/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Python-Owned Onboarding Contract

- [x] T001 [CORE] Add a bounded onboarding report in `aegis_py/app.py` with DB, write, recall, and health checks.
- [x] T002 [CORE] Add a CLI command in `aegis_py/cli.py` that prints a plain-language onboarding summary and a machine-readable payload.

## Phase 2: Setup Wrapper Alignment

- [x] T003 [CORE] Update `src/cli/setup.ts` so `aegis-setup` invokes the Python onboarding command instead of the raw MCP self-test.
- [x] T004 [CORE] Keep the wrapper Python-first and ensure it does not route through `AegisMemoryManager` or TS engine state.

## Phase 3: Validation

- [x] T005 [TEST] Add onboarding success coverage in `tests/test_user_surface.py`.
- [x] T006 [TEST] Add onboarding degraded or failure explanation coverage in `tests/test_user_surface.py`.
- [x] T007 [TEST] Update `tests/test_python_only_runtime_contract.py` to lock the new setup-wrapper contract.

## Phase 4: Closeout

- [x] T008 [TEST] Re-run targeted onboarding tests and the full Python suite.
- [x] T009 [DOCS] Record validation evidence for `047-consumer-onboarding` in `plan.md`.
