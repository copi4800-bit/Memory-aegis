# Tasks: Aegis Python-Only Runtime

**Input**: Design documents from `/specs/005-python-only-engine/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required because this feature is a breaking runtime migration and must prove that Python owns the production path.

**Organization**: Tasks are grouped by user story so each story can be validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`
- Every task includes concrete file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lock the feature scope and verify the host-loading constraint before destructive cleanup.

- [x] T001 [FOUNDATION] Record the current host-loading constraint and active runtime entrypoints in [specs/005-python-only-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md), [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json), and [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json)
- [x] T002 [P] [FOUNDATION] Inventory which TypeScript modules still own memory-domain logic across [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts), [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts), [src/aegis-manager.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/aegis-manager.ts), and [src/](/home/hali/.openclaw/extensions/memory-aegis-v7/src)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the Python runtime can own the complete core memory contract before removing the TS engine.

**⚠️ CRITICAL**: No broad TypeScript deletion should proceed until these tasks are complete.

- [x] T003 [FOUNDATION] Extend the Python runtime surface in [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), [aegis_py/main.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/main.py), and [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) so all core plugin behaviors have Python-owned entrypoints
- [x] T004 [P] [FOUNDATION] Add regression coverage for Python-owned core tool flows in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) and/or new Python-facing tests under [tests/](/home/hali/.openclaw/extensions/memory-aegis-v7/tests)
- [x] T005 [FOUNDATION] Define the acceptable host bootstrap boundary in [specs/005-python-only-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md) and ensure no TypeScript domain semantics remain outside that boundary

**Checkpoint**: Python is feature-complete enough to become the only engine owner.

## Phase 3: User Story 1 - Python Owns The Runtime Contract (Priority: P1) 🎯 MVP

**Goal**: Make Python the only owner of core runtime behavior.

**Independent Test**: Run the core memory tools and hook paths and verify they execute entirely through Python-owned semantics.

### Tests for User Story 1

- [x] T006 [P] [US1] Add adapter/bootstrap regression tests that prove core tools route to Python and do not fall back to TypeScript domain logic in [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts) or successor host-bootstrap tests
- [x] T007 [P] [US1] Add Python runtime smoke tests for store/search/status/clean/profile parity in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 1

- [x] T008 [US1] Remove TypeScript ownership of retrieval, storage, status, clean, and profile behavior from [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) and [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts), keeping only host bootstrap logic if required
- [x] T009 [US1] Replace remaining TypeScript memory-engine calls in [src/aegis-manager.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/aegis-manager.ts) and related `src/` runtime modules with Python-owned execution or remove those modules from runtime use
- [x] T010 [US1] Ensure recall/session hook behavior is Python-owned or explicitly retired in [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts), [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts), and [aegis_py/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py)

**Checkpoint**: Core plugin behavior is Python-owned in production.

## Phase 4: User Story 2 - Python Packaging Replaces TypeScript Packaging (Priority: P2)

**Goal**: Make packaging and startup Python-first.

**Independent Test**: Follow the documented install/start path and verify runtime ownership does not depend on the TS engine.

### Tests for User Story 2

- [x] T011 [P] [US2] Add packaging/startup validation coverage for the Python-first runtime contract in repository-facing tests or doc-facing checks

### Implementation for User Story 2

- [x] T012 [US2] Update [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json), [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json), and any startup scripts so the shipped runtime path points at Python ownership
- [x] T013 [P] [US2] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md), [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md), and [specs/005-python-only-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md) with the Python-first install and validation workflow

**Checkpoint**: Packaging and contributor workflow point to Python-first runtime ownership.

## Phase 5: User Story 3 - Legacy TypeScript Runtime Removal (Priority: P3)

**Goal**: Delete or quarantine the TS runtime so no hidden second engine remains.

**Independent Test**: Audit the shipped runtime and verify TS memory-engine modules are gone or non-semantic.

### Tests for User Story 3

- [x] T014 [P] [US3] Add regression or file-layout assertions that the removed TS runtime modules are no longer required on the production path

### Implementation for User Story 3

- [x] T015 [US3] Remove legacy TypeScript memory-engine implementation files under [src/](/home/hali/.openclaw/extensions/memory-aegis-v7/src) that are no longer needed after the Python migration, or relocate unavoidable host bootstrap code into a clearly bounded compatibility layer
- [x] T016 [US3] Remove or update outdated TypeScript tests, build assumptions, and release artifacts across [test/](/home/hali/.openclaw/extensions/memory-aegis-v7/test), [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json), and related docs

**Checkpoint**: The old TS engine is removed or explicitly quarantined.

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T017 [P] [FOUNDATION] Run the final Python-first validation workflow and record results plus residual host-loader risks in [specs/005-python-only-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md)
- [x] T018 [FOUNDATION] Reconcile task completion state and artifact links in [specs/005-python-only-engine/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/tasks.md)

## Phase 7: Python Surface Completion Extension

**Purpose**: Replace the remaining unsupported compatibility tools with Python-owned readback and backup flows.

- [x] T019 [P] [US1] Add Python regression coverage for `memory_get`, backup/export, and restore flows in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) and [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts)
- [x] T020 [US1] Extend [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts), and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) so `memory_get`, backup upload/export, and backup restore are Python-owned
- [x] T021 [FOUNDATION] Update [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json), [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md), and [specs/005-python-only-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md) with the completed Python surface status and validation evidence

## Phase 8: Python Ops/Inspection Surface Completion

**Purpose**: Replace the remaining unsupported maintenance and inspection tools with Python-owned surfaces.

- [x] T022 [P] [US1] Add Python regression coverage for `memory_doctor`, `memory_taxonomy_clean`, `memory_rebuild`, `memory_scan`, and `memory_visualize` in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) and [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts)
- [x] T023 [US1] Extend [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts), and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) so the remaining maintenance and inspection tools are Python-owned
- [x] T024 [FOUNDATION] Update [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json), [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md), and [specs/005-python-only-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/plan.md) with the completed Python ops/inspection surface status and validation evidence

## Dependencies & Execution Order

### Phase Dependencies

- Setup starts immediately
- Foundational work blocks broad TS deletion
- US1 depends on Foundational completion
- US2 depends on US1 being stable enough to package
- US3 depends on US1 and US2 because removal should follow validated Python ownership
- Polish depends on the intended migration scope being complete

### Implementation Strategy

1. Prove the Python runtime surface is complete
2. Lock the host bootstrap boundary
3. Move startup/packaging to Python-first
4. Delete the TS engine only after validation proves it is no longer needed
