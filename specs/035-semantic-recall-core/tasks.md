# Tasks: Semantic Recall Core

**Input**: Design documents from `/specs/035-semantic-recall-core/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Models & Interface (Foundational)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T001 [US1, US2] Update `SearchQuery` in `aegis_py/retrieval/models.py` to include `semantic: bool = False` and `semantic_model: str | None = None`.
- [x] T002 [US1] Ensure `CanonicalSearchResult` in `aegis_py/retrieval/engine.py` supports the `retrieval_stage` field correctly.
- [x] T003 [US1] Update `serialize_search_result` in `aegis_py/surface.py` to ensure `retrieval_stage` is consistently serialized.

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 2: User Story 1 - Meaning-based Recall (Priority: P1) 🎯 MVP

**Goal**: Implement the `Oracle Beast` role to perform query expansion for semantic search.

**Independent Test**: Perform a search for "Vietnamese beef noodle soup" and find a memory about "phở bò" without lexical overlap.

### Implementation for User Story 1

- [x] T004 [P] [US1] Create `aegis_py/retrieval/oracle.py` and define the `OracleBeast` role.
- [x] T005 [US1] Implement `OracleBeast.expand_query(query: str) -> list[str]` using a synonym-based expansion (baseline) or LLM-based expansion (if configured).
- [x] T006 [US1] Update `SearchPipeline` in `aegis_py/retrieval/search.py` to integrate `OracleBeast`.
- [x] T007 [US1] Implement `SearchPipeline._expand_semantic_oracle` method to fetch candidates based on expanded terms.
- [x] T008 [US1] Update `SearchPipeline.search_with_expansion` to call the semantic expansion stage.
- [x] T009 [US1] Implement result blending logic in `search_with_expansion` to merge semantic hits with lexical hits.

### Tests for User Story 1

- [x] T010 [P] [US1] Unit test for `OracleBeast` expansion logic in `tests/retrieval/test_oracle.py`.
- [x] T011 [US1] Integration test for end-to-end semantic recall in `tests/retrieval/test_semantic_recall.py`.

**Checkpoint**: User Story 1 (Semantic Recall) is functional.

---

## Phase 3: User Story 2 - Optional Semantic Toggle (Priority: P2)

**Goal**: Allow users to enable/disable semantic expansion per query.

**Independent Test**: Search with `semantic=false` should NOT trigger the `Oracle Beast`.

### Implementation for User Story 2

- [x] T012 [US2] Update `AegisApp.search` and `AegisApp.search_context_pack` in `aegis_py/app.py` to accept and pass the `semantic` flag.
- [x] T013 [US2] Update `AegisMCPServer.memory_search` and `AegisMCPServer.memory_context_pack` in `aegis_py/mcp/server.py` to expose the `semantic` parameter.
- [x] T014 [US2] Ensure `SearchPipeline` respects the `semantic` flag from `SearchQuery`.

**Checkpoint**: Semantic recall is now optional and toggleable.

---

## Phase 4: Polish & Performance (US3)

**Purpose**: Improvements that affect multiple user stories and ensure system stability.

- [x] T015 [US3] Benchmark semantic expansion latency and document findings in `benchmark/oracle_perf.md`.
- [x] T016 [P] Add error handling for failed semantic expansion (e.g., API timeouts) in `OracleBeast`.
- [x] T017 Update `ARCHITECTURE_BEAST_MAP.md` to reflect that `Oracle Beast` is now implemented and active.
- [x] T018 Reconcile completion state in `specs/035-semantic-recall-core/tasks.md`.

---

## Dependencies & Execution Order

1. **Phase 1 (Models)** must be done first to allow other parts to compile/run.
2. **Phase 2 (US1)** is the core implementation.
3. **Phase 3 (US2)** adds the user control layer.
4. **Phase 4 (Polish)** ensures production readiness.
