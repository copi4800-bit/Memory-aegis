# Tasks: Snapshot Versioning And Scope Restore

**Input**: Design documents from `/specs/006-snapshot-versioning-and-scope-restore/`
**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Tests are required because backup and restore are high-risk operational paths.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel if write scopes do not overlap
- **[Story]**: `US1`, `US2`, `US3`, or `FOUNDATION`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Record the current backup/export/restore gaps in [specs/006-snapshot-versioning-and-scope-restore/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore/plan.md), [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), and [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)

## Phase 2: User Story 1 - Auditable Snapshot Backups (Priority: P1)

### Tests for User Story 1

- [x] T002 [P] [US1] Add Python regression coverage for backup manifests and listing in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 1

- [x] T003 [US1] Extend [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) to write manifest files for snapshot and export backups
- [x] T004 [US1] Extend [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) with a Python-owned backup listing surface

## Phase 3: User Story 2 - Safe Restore Preview (Priority: P1)

### Tests for User Story 2

- [x] T005 [P] [US2] Add Python regression coverage for restore dry-run in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

### Implementation for User Story 2

- [x] T006 [US2] Extend [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) with restore preview/dry-run validation for snapshot and export files
- [x] T007 [US2] Extend [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) and [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) with Python-owned restore preview and backup listing entrypoints

## Phase 4: User Story 3 - Snapshot History Navigation (Priority: P2)

### Tests for User Story 3

- [x] T008 [P] [US3] Add host/bootstrap regression coverage for backup listing and dry-run routing in [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts)

### Implementation for User Story 3

- [x] T009 [US3] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md), [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json), and [specs/006-snapshot-versioning-and-scope-restore/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore/plan.md) with manifest, listing, and dry-run semantics

## Phase 5: Polish

- [x] T010 [FOUNDATION] Run the Python-first validation workflow and record evidence in [specs/006-snapshot-versioning-and-scope-restore/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore/plan.md)
- [x] T011 [FOUNDATION] Reconcile completion state in [specs/006-snapshot-versioning-and-scope-restore/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore/tasks.md)
