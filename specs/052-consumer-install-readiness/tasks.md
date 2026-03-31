# Tasks: Consumer Install Readiness

**Input**: Design documents from `/specs/052-consumer-install-readiness/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Install Preflight

- [x] T001 [CORE] Add a Python install readiness helper that checks Python, SQLite FTS5, Node, and npm.
- [x] T002 [CORE] Update `bin/aegis-setup` to print the install preflight before onboarding.

## Phase 2: User Guidance

- [x] T003 [DOCS] Add a short “use both” quickstart to `README.md`.

## Phase 3: Validation

- [x] T004 [TEST] Add install-readiness coverage in `tests/test_user_surface.py`.
- [x] T005 [TEST] Update `tests/test_python_only_runtime_contract.py` for the install/quickstart contract.
- [x] T006 [TEST] Re-run targeted tests and the full Python suite.
