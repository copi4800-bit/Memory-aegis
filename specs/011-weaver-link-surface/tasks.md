# Tasks: Weaver Link Surface

**Input**: Design documents from `/specs/011-weaver-link-surface/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Python integration coverage and TS adapter routing coverage are required because the feature adds new public operations and changes retrieval expansion behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/011-weaver-link-surface/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/011-weaver-link-surface/spec.md) and [specs/011-weaver-link-surface/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/011-weaver-link-surface/plan.md)

## Phase 2: User Story 1 - Persist Explicit Memory Relations (Priority: P1)

- [x] T002 [P] [US1] Add Python integration coverage for link creation and neighbor inspection in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add explicit link upsert and neighbor inspection to [aegis_py/storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [x] T004 [US1] Expose Python-owned Weaver app methods in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)

## Phase 3: User Story 2 - Use Explicit Links In Retrieval And Visualization (Priority: P1)

- [x] T005 [P] [US2] Add Python integration coverage for link-aware context-pack and visualization in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T006 [US2] Extend [aegis_py/retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) to add bounded link expansion after lexical seed recall
- [x] T007 [US2] Extend [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) visualization output with explicit relation edges

## Phase 4: User Story 3 - Expose Weaver Through Public Surfaces (Priority: P2)

- [x] T008 [P] [US3] Add TS adapter/plugin routing coverage for Weaver tools in [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts)
- [x] T009 [US3] Route Weaver operations through [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py), [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts), [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts), and [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json)
- [x] T010 [US3] Update [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py) and [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to include Weaver public operations

## Phase 5: Polish

- [x] T011 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/011-weaver-link-surface/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/011-weaver-link-surface/plan.md)
- [x] T012 [FOUNDATION] Reconcile completion state in [specs/011-weaver-link-surface/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/011-weaver-link-surface/tasks.md)
