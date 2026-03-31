# Tasks: Aegis Python vNext Memory Engine

**Input**: Design documents from `/specs/001-aegis-vnext-memory-engine/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required for this feature because the spec explicitly demands repeatable automated coverage and benchmark gating for retrieval, lifecycle, schema, and integration behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently after the foundational phase is complete.

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
- `T011`
- `T012`
- `T013`
- `T014`
- `T015`
- `T016`
- `T017`
- `T018`
- `T019`
- `T020`
- `T021`
- `T022`
- `T023`
- `T024`
- `T025`
- `T026`
- `T027`
- `T028`
- `T029`
- `T030`
- `T031`
- `T032`
- `T033`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if task owners avoid the same files
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`
- Every task includes concrete file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the feature working area and align documentation artifacts with the current brownfield codebase.

- [x] T001 [FOUNDATION] Verify the feature documentation set in [`aegis_py/specs/001-aegis-vnext-memory-engine/spec.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/specs/001-aegis-vnext-memory-engine/spec.md) and [`aegis_py/specs/001-aegis-vnext-memory-engine/plan.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/specs/001-aegis-vnext-memory-engine/plan.md) stays aligned with the active constitution in [`aegis_py/.specify/memory/constitution.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/.specify/memory/constitution.md)
- [x] T002 [P] [FOUNDATION] Audit current test coverage and map which scenarios belong to storage, retrieval, lifecycle, and integration in [`tests/test_storage.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_storage.py), [`tests/test_retrieval.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py), [`tests/test_memory_core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_core.py), [`tests/test_memory_lifecycle.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_lifecycle.py), [`tests/test_hygiene.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_hygiene.py), and [`tests/test_integration.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [P] [FOUNDATION] Capture the current schema and model mismatch inventory across [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql), [`aegis_py/storage/schema.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.py), [`aegis_py/storage/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py), and [`aegis_py/memory/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/models.py)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish one canonical domain/storage contract before changing feature behavior

**⚠️ CRITICAL**: No user story implementation should proceed until these tasks are complete

- [x] T004 [FOUNDATION] Define the canonical memory, link, conflict, and lifecycle contract in [`aegis_py/memory/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/models.py) and [`aegis_py/storage/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py) so both layers agree on scope, provenance, status, and timestamps
- [x] T005 [FOUNDATION] Align SQLite schema and Python schema wrappers with the canonical contract in [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) and [`aegis_py/storage/schema.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.py)
- [x] T006 [FOUNDATION] Consolidate low-level persistence semantics in [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py) and [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) so storage concerns are explicit and non-duplicated
- [x] T007 [P] [FOUNDATION] Add or update schema and persistence regression tests in [`tests/test_storage.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_storage.py) for statuses, provenance fields, scope fields, and lifecycle-safe persistence behavior
- [x] T008 [P] [FOUNDATION] Add integration coverage proving the canonical storage contract works through the current engine entrypoints in [`tests/test_integration.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

**Checkpoint**: Canonical storage/domain contract is stable and all stories can now build on it

---

## Phase 3: User Story 1 - Scope-Safe Explainable Retrieval (Priority: P1) 🎯 MVP

**Goal**: Deliver one canonical retrieval path that is scope-safe, explainable, and benchmarkable

**Independent Test**: Seed scoped memories with known provenance and conflicts, run retrieval through the canonical search path, and verify ranking, explanation, and leakage behavior without depending on hygiene or profile work

### Tests for User Story 1

- [x] T009 [P] [US1] Expand scope-isolation and result-shape tests in [`tests/test_retrieval.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py) to cover project/session/global filtering and empty-result behavior
- [x] T010 [P] [US1] Add retrieval explainability and conflict-visibility tests in [`tests/test_memory_core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_core.py) and [`tests/test_retrieval.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py)
- [x] T011 [P] [US1] Add benchmark-oriented assertions for relevance, leakage, and explanation completeness in [`tests/test_benchmark_core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)

### Implementation for User Story 1

- [x] T012 [US1] Choose the canonical retrieval path and adapt competing code in [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py) and [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) so the engine exposes one consistent search contract
- [x] T013 [P] [US1] Formalize search query and result contracts, including explanation and provenance fields, in [`aegis_py/retrieval/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py) and [`aegis_py/memory/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/models.py)
- [x] T014 [US1] Implement stable scope filtering, optional global fallback, and active-status selection in [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) and/or [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py)
- [x] T015 [US1] Implement explanation construction for score reasons, provenance, scope, and conflict state in [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py) and [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)
- [x] T016 [US1] Update retrieval benchmarks and fixtures in [`aegis_py/retrieval/benchmark.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py) to reflect the canonical search path and report the spec metrics

**Checkpoint**: User Story 1 is independently functional as the MVP retrieval engine

---

## Phase 4: User Story 2 - Safe Memory Lifecycle And Hygiene (Priority: P2)

**Goal**: Make lifecycle, archival, decay, and conflict handling explicit, bounded, and provenance-preserving

**Independent Test**: Create memories with different types, statuses, and session affinity; run lifecycle and hygiene operations; verify transitions and traceability without needing MCP or UI integration

### Tests for User Story 2

- [x] T017 [P] [US2] Strengthen session conclusion and working-memory lifecycle coverage in [`tests/test_memory_lifecycle.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_lifecycle.py)
- [x] T018 [P] [US2] Add hygiene and conflict safety tests in [`tests/test_hygiene.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_hygiene.py) for decay, archival, and non-destructive conflict handling
- [x] T019 [P] [US2] Add regression tests for superseded, archived, expired, and conflict-candidate visibility in [`tests/test_memory_core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_core.py) and [`tests/test_storage.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_storage.py)

### Implementation for User Story 2

- [x] T020 [US2] Separate lifecycle operations from ad hoc storage updates in [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py) and [`aegis_py/hygiene/engine.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py)
- [x] T021 [P] [US2] Standardize decay, archival, and session-end transitions in [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) and [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py)
- [x] T022 [US2] Refine conflict detection and safe resolution/suggestion flows in [`aegis_py/conflict/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py) and [`aegis_py/evolve/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/evolve/core.py)
- [x] T023 [US2] Ensure provenance-preserving status mutation and traceability for archived, expired, superseded, and conflict-candidate records in [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql), [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py), and [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)

**Checkpoint**: User Stories 1 and 2 both work independently, and the store can age safely over time

---

## Phase 5: User Story 3 - Product-Grade Local Engine Surface (Priority: P3)

**Goal**: Expose a compact, stable local engine surface for app, CLI, and MCP workflows

**Independent Test**: Initialize a fresh local database, run store/search/status/clean/export through the integration surfaces, and verify consistent outputs without cloud dependencies

### Tests for User Story 3

- [x] T024 [P] [US3] Expand integration tests for store, search, status, clean, and export flows in [`tests/test_integration.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T025 [P] [US3] Add MCP-facing output and error-shape regression tests in [`tests/test_integration.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T026 [P] [US3] Add local initialization and smoke coverage for the current runtime entrypoints in [`tests/test_integration.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) and [`tests/test_ingest.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_ingest.py)

### Implementation for User Story 3

- [x] T027 [US3] Refactor [`aegis_py/mcp/server.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) to depend on the canonical memory and retrieval services instead of duplicating domain behavior
- [x] T028 [P] [US3] Align entrypoint orchestration and thin-adapter behavior in [`aegis_py/app.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and [`aegis_py/main.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/main.py)
- [x] T029 [US3] Normalize JSON responses, empty-result semantics, and operational output in [`aegis_py/mcp/server.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), with any required support changes in [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)
- [x] T030 [US3] Ensure local initialization and configuration defaults remain cloud-free and operational in [`aegis_py/mcp/server.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py), and [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)

**Checkpoint**: All user stories are independently functional and available through stable local integration surfaces

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tighten quality gates, documentation, and release readiness across all stories

- [x] T031 [P] [FOUNDATION] Finalize benchmark reporting and regression thresholds in [`aegis_py/retrieval/benchmark.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py) and [`tests/test_benchmark_core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)
- [x] T032 [P] [FOUNDATION] Update architecture and contributor-facing documentation in [`/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md) and [`/home/hali/.openclaw/extensions/memory-aegis-v7/README.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to reflect the canonical engine contract
- [x] T033 [FOUNDATION] Run the full validation workflow across retrieval, lifecycle, storage, and integration tests and record remaining gaps in [`aegis_py/specs/001-aegis-vnext-memory-engine/plan.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/specs/001-aegis-vnext-memory-engine/plan.md) or follow-up spec artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies and starts immediately
- **Phase 2: Foundational** depends on Setup and blocks all user stories
- **Phase 3: US1** depends on Foundational completion
- **Phase 4: US2** depends on Foundational completion and should build on the canonical retrieval/domain contract from US1 where lifecycle behavior touches result visibility
- **Phase 5: US3** depends on Foundational completion and should preferably consume the canonical services stabilized in US1 and US2
- **Phase 6: Polish** depends on the desired stories being complete

### User Story Dependencies

- **US1 (P1)** is the MVP and should be delivered first
- **US2 (P2)** depends on the canonical contract and benefits from the retrieval result/status shape established in US1
- **US3 (P3)** should not invent new semantics; it wraps the canonical engine behavior from US1 and US2

### Within Each User Story

- Tests should be updated first and should fail before implementation where practical
- Model and schema alignment comes before service refactors
- Storage semantics come before retrieval/hygiene/integration adapters
- Core implementation comes before integration cleanup

## Parallel Opportunities

- T002 and T003 can run in parallel
- T007 and T008 can run in parallel after T004-T006 stabilize
- T009, T010, and T011 can run in parallel
- T013 can run in parallel with the early retrieval consolidation work in T012 if interfaces are agreed
- T017, T018, and T019 can run in parallel
- T021 and T022 can run in parallel once lifecycle contracts are defined
- T024, T025, and T026 can run in parallel
- T028 can run in parallel with T027 if the canonical service contract is already stable
- T031 and T032 can run in parallel near the end

## Implementation Strategy

### MVP First

1. Finish Setup and Foundational work
2. Deliver US1 as the first real product increment
3. Validate retrieval quality, explanation completeness, and scope isolation
4. Only then move to lifecycle hardening and integration cleanup

### Incremental Delivery

1. Canonical contract and storage foundation
2. Scope-safe explainable retrieval
3. Safe lifecycle and hygiene
4. Stable local app/MCP integration
5. Benchmarks, docs, and release gating

### Notes

- Avoid rewriting the codebase wholesale; converge overlapping paths step by step
- Prefer deleting duplicate behavior only after the canonical path is test-covered
- Keep mutation flows auditable and suggestion-first
- Treat benchmark and explanation regressions as blocking quality issues, not optional cleanup
