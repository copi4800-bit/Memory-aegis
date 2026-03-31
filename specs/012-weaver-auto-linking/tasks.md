# Tasks: Weaver Auto Linking

**Input**: Design documents from `/specs/012-weaver-auto-linking/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Python integration coverage is required because this feature changes ingest and rebuild behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/012-weaver-auto-linking/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/012-weaver-auto-linking/spec.md) and [specs/012-weaver-auto-linking/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/012-weaver-auto-linking/plan.md)

## Phase 2: User Story 1 - Auto Link Same-Subject Memories On Ingest (Priority: P1)

- [x] T002 [P] [US1] Add Python integration coverage for same-subject auto-linking on ingest in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add bounded same-subject peer lookup and auto-link helpers in [aegis_py/storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [x] T004 [US1] Trigger same-subject auto-linking from the Python write path in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)

## Phase 3: User Story 2 - Rebuild Missing Same-Subject Links (Priority: P1)

- [x] T005 [P] [US2] Add Python integration coverage for rebuild backfill in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T006 [US2] Extend the Python rebuild flow in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) to backfill missing `same_subject` links

## Phase 4: User Story 3 - Document Auto-Link Behavior (Priority: P2)

- [x] T007 [US3] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to document the narrow same-subject auto-link rule

## Phase 5: Polish

- [x] T008 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/012-weaver-auto-linking/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/012-weaver-auto-linking/plan.md)
- [x] T009 [FOUNDATION] Reconcile completion state in [specs/012-weaver-auto-linking/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/012-weaver-auto-linking/tasks.md)
