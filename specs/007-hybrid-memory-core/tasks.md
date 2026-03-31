# Tasks: Hybrid Memory Core

**Input**: Design documents from `/specs/007-hybrid-memory-core/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Contract and integration coverage are required wherever public surface behavior changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/007-hybrid-memory-core/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/spec.md) and [specs/007-hybrid-memory-core/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/plan.md)
- [x] T002 [FOUNDATION] Audit current public-vs-private boundaries across [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts), and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts)

## Phase 2: User Story 1 - Stable Local Core Boundary (Priority: P1)

### Tests for User Story 1

- [x] T003 [P] [US1] Add contract coverage for public Python and host-facing memory surfaces in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) and [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts)

### Implementation for User Story 1

- [x] T004 [US1] Define and document the stable public memory surface in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json)
- [x] T005 [US1] Refactor Python integration surfaces so public semantics live in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), not in host-only glue
- [x] T006 [US1] Reduce host coupling in [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) so they act as adapters over the Python-owned contract

## Phase 3: User Story 2 - Optional Hybrid Sync Model (Priority: P1)

### Tests for User Story 2

- [x] T007 [P] [US2] Add schema and policy regression coverage for local-only versus sync-eligible scope handling in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 2

- [x] T008 [US2] Add minimal sync-policy metadata and scope classification scaffolding in [aegis_py/storage/schema.sql](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) and related storage helpers under [aegis_py/storage](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage)
- [x] T009 [US2] Surface sync-policy inspection through Python-owned runtime paths in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)
- [x] T010 [US2] Document hybrid non-goals, trust boundaries, and migration stance in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [specs/007-hybrid-memory-core/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/plan.md)

## Phase 4: User Story 3 - Mammoth Retrieval Strategy (Priority: P2)

### Tests for User Story 3

- [x] T011 [P] [US3] Add retrieval benchmark or integration fixtures that protect lexical-first recall and explainable relationship expansion in [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py) or adjacent benchmark fixtures

### Implementation for User Story 3

- [x] T012 [US3] Define lexical-first plus relationship-expansion retrieval hooks in [aegis_py/retrieval](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval) without reducing explanation fidelity
- [x] T013 [US3] Add context-pack shaping rules for host models in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and adapter callers in [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts)
- [x] T014 [US3] Document the Mammoth retrieval flow and ranking rationale in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md)

## Phase 5: Polish

- [x] T015 [FOUNDATION] Run the canonical validation workflow and benchmark checks required by the implemented slices, then record evidence in [specs/007-hybrid-memory-core/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/plan.md)
- [x] T016 [FOUNDATION] Reconcile completion state in [specs/007-hybrid-memory-core/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/tasks.md)
- [x] T017 [FOUNDATION] Capture the architectural findings from [1.md](/home/hali/.openclaw/1.md) into [specs/007-hybrid-memory-core/research.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/research.md) and align them with the active spec and constitution
