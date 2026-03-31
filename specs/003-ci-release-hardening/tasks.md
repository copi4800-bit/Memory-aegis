# Tasks: Aegis Python CI And Release Packaging Hardening

**Input**: Design documents from `/specs/003-ci-release-hardening/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required for this feature because the spec explicitly requires automated CI validation and release evidence.

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

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 [FOUNDATION] Review the validation and release gaps recorded in [specs/002-benchmark-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md) and restate the bounded scope in [specs/003-ci-release-hardening/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/spec.md) and [specs/003-ci-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/plan.md)

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 [FOUNDATION] Identify the canonical Python validation command and repository files that should become the CI/release source of truth in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md), [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md), and [requirements.txt](/home/hali/.openclaw/extensions/memory-aegis-v7/requirements.txt)

## Phase 3: User Story 1 - CI Validation Gate (Priority: P1)

- [x] T003 [P] [US1] Add or update repository CI workflow definitions under [.github/workflows/](/home/hali/.openclaw/extensions/memory-aegis-v7/.github/workflows) to run the canonical Python validation command
- [x] T004 [P] [US1] Add regression coverage or workflow assertions for the CI validation command in repository-facing tests or doc checks

## Phase 4: User Story 2 - Release Packaging Workflow (Priority: P2)

- [x] T005 [US2] Document the release packaging workflow in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and any related release artifact docs
- [x] T006 [P] [US2] Align release workflow language in [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md) and [specs/003-ci-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/plan.md)

## Phase 5: User Story 3 - Release Evidence Record (Priority: P3)

- [x] T007 [US3] Record CI/release validation evidence and remaining gaps in [specs/003-ci-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/plan.md)
- [x] T008 [US3] Reconcile task completion state and artifact links in [specs/003-ci-release-hardening/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/tasks.md)

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T009 [FOUNDATION] Run the final validation suite or workflow checks and record residual risks in [specs/003-ci-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/003-ci-release-hardening/plan.md)
