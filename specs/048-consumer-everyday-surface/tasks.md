# Tasks: Consumer Everyday Surface

**Input**: Design documents from `/specs/048-consumer-everyday-surface/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Python Status Summary

- [x] T001 [CORE] Add a plain-language status summary in `aegis_py/app.py` that explains healthy, degraded, and broken states for ordinary users.
- [x] T002 [CORE] Update `aegis_py/cli.py` so the default `status` command prints the plain-language summary and supports explicit JSON output.

## Phase 2: Plugin Everyday Content

- [x] T003 [CORE] Update `index.ts` so `memory_stats` returns human-readable primary content while keeping structured details for hosts.
- [x] T004 [CORE] Preserve the machine-readable health payload for integrations rather than removing it.

## Phase 3: Validation

- [x] T005 [TEST] Add or update user-surface tests in `tests/test_user_surface.py` for plain-language status output.
- [x] T006 [TEST] Add or update runtime surface assertions in `tests/test_app_surface.py` for the status summary behavior.
- [x] T007 [TEST] Update `test/integration/python-adapter-plugin.test.ts` for the new `memory_stats` primary content.

## Phase 4: Closeout

- [x] T008 [TEST] Re-run targeted Python and adapter tests plus the full Python suite.
- [x] T009 [DOCS] Record validation evidence for `048-consumer-everyday-surface` in `plan.md`.
