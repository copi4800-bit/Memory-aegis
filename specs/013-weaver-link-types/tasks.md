# Tasks: Weaver Link Types

**Input**: Design documents from `/specs/013-weaver-link-types/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/013-weaver-link-types/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/013-weaver-link-types/spec.md) and [specs/013-weaver-link-types/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/013-weaver-link-types/plan.md)

## Phase 2: Typed Auto-Linking

- [x] T002 [US1] Add Python integration coverage for typed procedural/semantic auto-linking in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add bounded same-subject typed-link helpers in [aegis_py/storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [x] T004 [US1] Trigger typed auto-linking from the Python write path in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)

## Phase 3: Rebuild Backfill

- [x] T005 [US2] Add Python integration coverage for rebuild typed-link backfill in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T006 [US2] Extend rebuild in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) to backfill procedural/semantic typed links

## Phase 4: Documentation

- [x] T007 [US3] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to describe typed auto-link behavior

## Phase 5: Polish

- [x] T008 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/013-weaver-link-types/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/013-weaver-link-types/plan.md)
- [x] T009 [FOUNDATION] Reconcile completion state in [specs/013-weaver-link-types/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/013-weaver-link-types/tasks.md)
