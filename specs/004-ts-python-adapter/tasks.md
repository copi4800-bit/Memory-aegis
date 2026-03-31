# Tasks: Aegis TypeScript Adapter To Python Engine

**Input**: Design documents from `/specs/004-ts-python-adapter/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required for this feature because the migration must keep existing plugin behavior explicit and avoid silent parity claims.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently after the foundational phase is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if task owners avoid the same files
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`
- Every task includes concrete file paths

## Progress Snapshot

Completed so far:

- `T001`
- `T002`
- `T003`
- `T004`
- `T005`
- `T006`
- `T007`
- `T008`
- `T009`
- `T010`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 [FOUNDATION] Review the TS-vs-Python capability gap and restate the bounded migration scope in [specs/004-ts-python-adapter/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/spec.md) and [specs/004-ts-python-adapter/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/plan.md)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 [FOUNDATION] Inventory the current TypeScript plugin tool surface across [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts), [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts), and [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json)
- [x] T003 [P] [FOUNDATION] Inventory the current Python canonical engine surface across [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), and [aegis_py/main.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/main.py)

## Phase 3: User Story 1 - TS Plugin Uses Python Retrieval Core (Priority: P1)

- [x] T004 [P] [US1] Define the first safe routing slice and adapter contract in [specs/004-ts-python-adapter/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/plan.md)
- [x] T005 [P] [US1] Add regression coverage or adapter-facing validation for the chosen routing slice in repository tests

## Phase 4: User Story 2 - TS Plugin Tool Parity Map (Priority: P2)

- [x] T006 [US2] Record the per-tool parity map in [specs/004-ts-python-adapter/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/plan.md)
- [x] T007 [P] [US2] Update contributor-facing migration notes in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) or related docs if needed

## Phase 5: User Story 3 - Incremental Replacement Strategy (Priority: P3)

- [x] T008 [US3] Record the staged replacement strategy and remaining gaps in [specs/004-ts-python-adapter/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/plan.md)
- [x] T009 [US3] Reconcile task completion state and artifact links in [specs/004-ts-python-adapter/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/tasks.md)

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T010 [FOUNDATION] Run the relevant validation suites and record residual migration risks in [specs/004-ts-python-adapter/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/plan.md)
