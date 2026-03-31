# Tasks: Decay Type-Aware Retention

**Input**: Design documents from `/specs/033-decay-type-aware-retention/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/033-decay-type-aware-retention/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/033-decay-type-aware-retention/spec.md) and [specs/033-decay-type-aware-retention/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/033-decay-type-aware-retention/plan.md)

## Phase 2: Decay Slice

- [x] T002 [US1] Add type-aware retention defaults in [aegis_py/hygiene/engine.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py)
- [x] T003 [US1] Extend decay execution to support type-aware half-lives in [aegis_py/storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [x] T004 [US2] Add hygiene test coverage for type-aware and override decay behavior in [tests/test_hygiene.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_hygiene.py)

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/033-decay-type-aware-retention/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/033-decay-type-aware-retention/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/033-decay-type-aware-retention/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/033-decay-type-aware-retention/tasks.md)
