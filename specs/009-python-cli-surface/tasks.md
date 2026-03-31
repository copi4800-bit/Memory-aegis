# Tasks: Python CLI Surface

**Input**: Design documents from `/specs/009-python-cli-surface/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: CLI integration coverage is required because this feature defines a new public entrypoint.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/009-python-cli-surface/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/009-python-cli-surface/spec.md) and [specs/009-python-cli-surface/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/009-python-cli-surface/plan.md)
- [x] T002 [FOUNDATION] Map existing Python public surfaces to CLI commands in [aegis_py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py)

## Phase 2: User Story 1 - Call Public Memory Surface From Shell (Priority: P1)

### Tests for User Story 1

- [x] T003 [P] [US1] Add CLI integration coverage for surface/status/store/search/context-pack in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 1

- [x] T004 [US1] Add a Python CLI entrypoint in [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py) that wraps existing public runtime surfaces
- [x] T005 [US1] Ensure structured CLI commands emit stable JSON payloads aligned with the Python runtime contract

## Phase 3: User Story 2 - Operational Workflows Via CLI (Priority: P1)

### Tests for User Story 2

- [x] T006 [P] [US2] Add CLI integration coverage for backup preview and scope-policy inspection in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 2

- [x] T007 [US2] Extend [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py) with backup and scope-policy commands over existing `AegisApp` methods

## Phase 4: User Story 3 - Document Standalone Usage (Priority: P2)

- [x] T008 [US3] Document standalone CLI usage in [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [specs/009-python-cli-surface/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/009-python-cli-surface/plan.md)

## Phase 5: Polish

- [x] T009 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/009-python-cli-surface/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/009-python-cli-surface/plan.md)
- [x] T010 [FOUNDATION] Reconcile completion state in [specs/009-python-cli-surface/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/009-python-cli-surface/tasks.md)
