# Tasks: Aegis Python Benchmark And Release Hardening

**Input**: Design documents from `/specs/002-benchmark-release-hardening/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required for this feature because the spec explicitly requires benchmark gating, regression visibility, and contributor validation workflow evidence.

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
- `T011`
- `T012`
- `T013`
- `T014`
- `T015`
- `T016`
- `T017`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the new hardening feature with the existing benchmark and documentation baseline.

- [x] T001 [FOUNDATION] Review the release gaps recorded in [specs/001-aegis-vnext-memory-engine/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/001-aegis-vnext-memory-engine/plan.md) and restate the bounded scope in [specs/002-benchmark-release-hardening/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/spec.md) and [specs/002-benchmark-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md)
- [x] T002 [P] [FOUNDATION] Inventory current benchmark and regression coverage across [aegis_py/retrieval/benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py), [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py), [tests/test_retrieval.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py), and [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish one explicit benchmark and validation contract before broadening coverage.

**⚠️ CRITICAL**: No user story implementation should proceed until these tasks are complete

- [x] T003 [FOUNDATION] Define the canonical benchmark gate contract and threshold ownership in [aegis_py/retrieval/benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py)
- [x] T004 [P] [FOUNDATION] Add regression assertions that exercise threshold evaluation in [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)
- [x] T005 [P] [FOUNDATION] Align contributor-facing validation references in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md) with the active root-level `spec-kit` layout

**Checkpoint**: Benchmark and validation contracts are explicit and stable.

---

## Phase 3: User Story 1 - Broader Retrieval Regression Corpus (Priority: P1) 🎯 MVP

**Goal**: Expand the seeded benchmark corpus so retrieval regressions become visible across more than the minimal happy-path fixture.

**Independent Test**: Run the benchmark-oriented Python suite and confirm that broadened seeded cases cover multiple scopes, conflict-visible cases, punctuation-safe queries, and empty-result behavior while still producing explicit gate output.

### Tests for User Story 1

- [x] T006 [P] [US1] Expand benchmark fixture coverage for scoped retrieval and anti-leak behavior in [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)
- [x] T007 [P] [US1] Add benchmark-adjacent regression tests for punctuation-safe and empty-result retrieval behavior in [tests/test_retrieval.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py)

### Implementation for User Story 1

- [x] T008 [US1] Broaden seeded benchmark query cases and reporting support in [aegis_py/retrieval/benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py)
- [x] T009 [US1] Ensure benchmark failure output identifies violated metrics in [aegis_py/retrieval/benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py) and [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)

**Checkpoint**: Retrieval benchmark gating covers the broadened corpus and fails explicitly on regression.

---

## Phase 4: User Story 2 - Contributor Validation Workflow (Priority: P2)

**Goal**: Make the local validation path obvious, repeatable, and accurate for contributors.

**Independent Test**: Follow the documented commands from a clean local environment and verify they point to the current Python regression and benchmark gate workflow.

### Tests for User Story 2

- [x] T010 [P] [US2] Add documentation regression coverage for the published validation command and benchmark gate references in [tests/test_app_surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_app_surface.py) or another appropriate Python doc-facing test module if needed

### Implementation for User Story 2

- [x] T011 [US2] Update contributor validation workflow instructions in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md)
- [x] T012 [P] [US2] Update architecture and validation contract language in [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md)

**Checkpoint**: Contributors can identify and run the current validation workflow without tribal knowledge.

---

## Phase 5: User Story 3 - Release Readiness Summary (Priority: P3)

**Goal**: Record validated evidence and remaining gaps in the active `spec-kit` artifacts.

**Independent Test**: Complete the validation workflow, record the observed results, and verify that follow-up gaps are explicit in the active feature plan.

### Tests for User Story 3

- [x] T013 [P] [US3] Add or update validation-closeout assertions if a doc-facing regression test is used for release summary artifacts

### Implementation for User Story 3

- [x] T014 [US3] Record release-readiness validation results and remaining gaps in [specs/002-benchmark-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md)
- [x] T015 [US3] Run the full local validation workflow and capture the observed output in [specs/002-benchmark-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md)

**Checkpoint**: Benchmark/release hardening is evidenced in the active feature artifacts.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup across benchmark, docs, and release-readiness artifacts

- [x] T016 [P] [FOUNDATION] Reconcile task completion state and artifact links in [specs/002-benchmark-release-hardening/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/tasks.md)
- [x] T017 [FOUNDATION] Run the final Python regression suite and note any residual risks in [specs/002-benchmark-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md)

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** starts immediately
- **Foundational (Phase 2)** depends on Setup and blocks all user stories
- **US1 (Phase 3)** depends on Foundational completion
- **US2 (Phase 4)** depends on Foundational completion and should align with the benchmark contract from US1
- **US3 (Phase 5)** depends on completion of the validation workflow established in US1 and US2
- **Polish (Phase 6)** depends on the desired user stories being complete

### User Story Dependencies

- **US1 (P1)** is the MVP because broadened benchmark coverage is the core value of this feature
- **US2 (P2)** depends on the canonical validation workflow but should stay independently reviewable as a documentation increment
- **US3 (P3)** records observed evidence and should not redefine the benchmark or validation semantics established earlier

### Parallel Opportunities

- T001 and T002 can run in parallel
- T004 and T005 can run in parallel after T003
- T006 and T007 can run in parallel
- T011 and T012 can run in parallel
- T014 and T015 can run in parallel once validation output is available

## Implementation Strategy

### MVP First

1. Lock the benchmark gate contract
2. Expand the benchmark corpus and explicit failure output
3. Validate the broadened corpus locally

### Incremental Delivery

1. Benchmark gate contract
2. Broader regression corpus
3. Contributor validation workflow
4. Release-readiness evidence and final closeout

## Notes

- Keep this feature bounded to benchmark and release hardening
- Do not reopen core engine semantics already stabilized in feature `001`
- Prefer explicit validation evidence over narrative-only closeout text
