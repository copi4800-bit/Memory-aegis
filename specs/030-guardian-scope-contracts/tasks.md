# Tasks: Guardian Scope Contracts

**Input**: Design documents from `/specs/030-guardian-scope-contracts/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/030-guardian-scope-contracts/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/030-guardian-scope-contracts/spec.md) and [specs/030-guardian-scope-contracts/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/030-guardian-scope-contracts/plan.md)

## Phase 2: Guardian Slice

- [x] T002 [US1] Add explicit global fallback reason tagging in [aegis_py/retrieval/contract.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/contract.py) and [aegis_py/retrieval/engine.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/engine.py)
- [x] T003 [US2] Add context-pack boundary contract metadata in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py)
- [x] T004 [US2] Add Python integration coverage for guardian scope signals in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/030-guardian-scope-contracts/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/030-guardian-scope-contracts/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/030-guardian-scope-contracts/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/030-guardian-scope-contracts/tasks.md)
