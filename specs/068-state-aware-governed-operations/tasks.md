# Tasks: State-Aware Governed Operations

**Input**: Design documents from `/specs/068-state-aware-governed-operations/`  
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Keep the current Python and host contract suites green after each extraction slice.

**Organization**: Tasks are grouped by refactor slice so tranche `068` can execute as brownfield architecture work without pretending it is a rewrite.

## Phase 1: Setup

- [x] T001 Create feature spec and implementation plan in `specs/068-state-aware-governed-operations/`
- [x] T002 Document the bounded validation command set for tranche `068`

## Phase 2: User Story 1 - Isolate Governed Runtime Surfaces (Priority: P1)

**Goal**: Shrink orchestration sprawl in `AegisApp` by extracting coherent Python-owned facades.

**Independent Test**: Inspect the runtime layout and verify governed/background/operator/health responsibilities have named owners while public method names remain stable.

- [x] T003 [US1] Extract health/status/doctor implementation bodies from `aegis_py/app.py` into a dedicated Python-owned facade
- [x] T004 [P] [US1] Extract storage/governance/evidence operator helpers from `aegis_py/app.py` into a dedicated operator facade
- [x] T005 [P] [US1] Extract backup and restore workflows behind a dedicated facade while preserving existing `AegisOperationalService` behavior
- [x] T006 [P] [US1] Extract sync and governed-background behaviors behind dedicated facades or service seams instead of continuing to grow `AegisApp`

## Phase 3: User Story 2 - Preserve Public Contract Stability While Refactoring (Priority: P1)

**Goal**: Make architecture cleanup safe for operators and host integrators.

**Independent Test**: Re-run the high-signal Python and host surface suites after each slice and confirm stable payload shapes.

- [x] T007 [US2] Keep `status()` and `doctor()` fail-safe while extracting internal helpers
- [x] T008 [P] [US2] Preserve storage operator surfaces across Python CLI, MCP, TS adapter, and plugin metadata during refactors
- [x] T009 [P] [US2] Re-run `tests/test_app_surface.py`, `tests/test_user_surface.py`, and `tests/test_storage_growth_control.py` after each extraction slice
- [x] T010 [US2] Re-run broader Python and host contract checks before closing the tranche

## Phase 4: User Story 3 - Reduce Storage and Contract Duplication (Priority: P2)

**Goal**: Create cleaner extension points for later governed-operation work.

**Independent Test**: Inspect the resulting architecture and verify storage slices and one canonical contract owner are explicit.

- [x] T011 [US3] Introduce internal storage slice classes behind `aegis_py/storage/manager.py` while preserving one SQLite connection owner
- [x] T012 [P] [US3] Move storage footprint, compaction, and retention-policy behavior behind a storage-hygiene slice
- [x] T013 [P] [US3] Define one canonical runtime-owned contract registry for public operation names and tool metadata
- [x] T014 [US3] Reduce copy-paste drift pressure across `aegis_py/surface.py`, `aegis_py/mcp/server.py`, `src/python-adapter.ts`, `index.ts`, and `openclaw.plugin.json`

## Phase 5: GSD Integration

- [x] T015 [DOCS] Keep `.planning/STATE.md` and `.planning/ROADMAP.md` aligned only if tranche `068` execution materially changes coordination status
- [x] T016 [DOCS] Summarize residual architecture debt discovered during execution so later production-excellence slices build on real seams instead of ad hoc cleanup
