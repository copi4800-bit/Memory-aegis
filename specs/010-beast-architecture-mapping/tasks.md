# Tasks: Beast Architecture Mapping

**Input**: Design documents from `/specs/010-beast-architecture-mapping/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`

**Tests**: No new runtime tests are required because this feature is documentation and workflow reconciliation only. Canonical repo validation still runs for non-regression.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/010-beast-architecture-mapping/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/spec.md) and [specs/010-beast-architecture-mapping/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/plan.md)
- [x] T002 [FOUNDATION] Review [1.md](/home/hali/.openclaw/1.md), [specs/007-hybrid-memory-core/research.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/research.md), and current `aegis_py/` boundaries for beast-map reconciliation

## Phase 2: User Story 1 - Canonical Internal Beast Map (Priority: P1)

- [x] T003 [US1] Add [aegis_py/ARCHITECTURE_BEAST_MAP.md](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/ARCHITECTURE_BEAST_MAP.md) with all 23 beasts mapped into the six-module model
- [x] T004 [US1] Mark each beast entry with `current`, `partial`, `target`, or `deferred` ownership notes so contributors can tell which parts already exist

## Phase 3: User Story 2 - Align Repo Docs With The Six-Module Model (Priority: P1)

- [x] T005 [US2] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to describe the six-module architecture and point contributors to the internal beast map
- [x] T006 [US2] Document explicitly that beast naming is internal architecture vocabulary and not part of the public runtime/tool surface

## Phase 4: User Story 3 - Reconcile GSD + Spec Kit Artifacts (Priority: P2)

- [x] T007 [US3] Add [specs/010-beast-architecture-mapping/research.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/research.md) capturing the source-note interpretation
- [x] T008 [US3] Run the Spec Kit prerequisite check and record the result in [specs/010-beast-architecture-mapping/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/plan.md)

## Phase 5: Polish

- [x] T009 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/010-beast-architecture-mapping/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/plan.md)
- [x] T010 [FOUNDATION] Reconcile completion state in [specs/010-beast-architecture-mapping/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/tasks.md)
