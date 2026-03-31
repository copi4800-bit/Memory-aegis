# Tasks: Guardian Partial Scope Rejection

**Input**: Design documents from `/specs/031-guardian-partial-scope-rejection/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/031-guardian-partial-scope-rejection/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/031-guardian-partial-scope-rejection/spec.md) and [specs/031-guardian-partial-scope-rejection/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/031-guardian-partial-scope-rejection/plan.md)

## Phase 2: Guardian Validation Slice

- [x] T002 [US1] Add retrieval scope-pair validation in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)
- [x] T003 [US1] Wire search and context-pack surfaces through the validated scope-pair contract in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)
- [x] T004 [US2] Add Python integration coverage for partial-scope rejection and valid-scope acceptance in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/031-guardian-partial-scope-rejection/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/031-guardian-partial-scope-rejection/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/031-guardian-partial-scope-rejection/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/031-guardian-partial-scope-rejection/tasks.md)
