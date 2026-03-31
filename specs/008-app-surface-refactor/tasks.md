# Tasks: App Surface Refactor

**Input**: Design documents from `/specs/008-app-surface-refactor/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Existing Python and bootstrap integration tests must stay green to prove behavior preservation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/008-app-surface-refactor/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/008-app-surface-refactor/spec.md) and [specs/008-app-surface-refactor/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/008-app-surface-refactor/plan.md)
- [x] T002 [FOUNDATION] Audit ownership inside [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and mark which methods should move into surface helpers versus operational services

## Phase 2: User Story 1 - Extract Public Surface Helpers (Priority: P1)

### Tests for User Story 1

- [x] T003 [P] [US1] Preserve surface payload coverage in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) and [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts)

### Implementation for User Story 1

- [x] T004 [US1] Create Python-owned surface helper modules under [aegis_py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py) for public contract assembly and retrieval payload shaping
- [x] T005 [US1] Refactor [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) to delegate `public_surface`, result serialization, and context-pack shaping to those helpers

## Phase 3: User Story 2 - Extract Operational Services (Priority: P1)

### Tests for User Story 2

- [x] T006 [P] [US2] Preserve backup/restore and scope-policy regression coverage in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 2

- [x] T007 [US2] Create Python-owned operational service helpers for backup/restore and scope-policy workflows under [aegis_py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py)
- [x] T008 [US2] Refactor [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) to delegate backup/restore and scope-policy operations to those helpers without changing return payloads

## Phase 4: User Story 3 - Codify Refactor Boundary (Priority: P2)

- [x] T009 [US3] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [specs/008-app-surface-refactor/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/008-app-surface-refactor/plan.md) with the new ownership boundary

## Phase 5: Polish

- [x] T010 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/008-app-surface-refactor/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/008-app-surface-refactor/plan.md)
- [x] T011 [FOUNDATION] Reconcile completion state in [specs/008-app-surface-refactor/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/008-app-surface-refactor/tasks.md)
