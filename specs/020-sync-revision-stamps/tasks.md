# Tasks: Sync Revision Stamps

**Input**: Design documents from `/specs/020-sync-revision-stamps/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/020-sync-revision-stamps/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/020-sync-revision-stamps/spec.md) and [specs/020-sync-revision-stamps/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/020-sync-revision-stamps/plan.md)

## Phase 2: Revision Storage

- [x] T002 [US1] Add Python integration coverage for scope revision stamps in sync flows in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add lightweight scope revision persistence in [aegis_py/storage/schema.sql](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) and [aegis_py/storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)

## Phase 3: Sync Integration

- [x] T004 [US2] Route revision stamps through [aegis_py/operations.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/operations.py)
- [x] T005 [US2] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to document scope revision stamps

## Phase 4: Polish

- [x] T006 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/020-sync-revision-stamps/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/020-sync-revision-stamps/plan.md)
- [x] T007 [FOUNDATION] Reconcile completion state in [specs/020-sync-revision-stamps/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/020-sync-revision-stamps/tasks.md)
