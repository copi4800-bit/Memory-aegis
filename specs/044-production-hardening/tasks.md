# Tasks: Production Hardening And SRE-Grade Guarantees

**Input**: Design documents from `/specs/044-production-hardening/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Validation Baseline And Surface Contract

- [x] T001 [SPEC] Record the canonical validation baseline in `specs/044-production-hardening/plan.md` and closure evidence, including the Python runtime suite and TypeScript adapter suite commands.
- [x] T002 [CORE] Reconcile the public contract across `README.md`, `openclaw.plugin.json`, `aegis_py/surface.py`, `aegis_py/mcp/server.py`, and `index.ts` so Python remains the single owner of memory semantics.
- [x] T003 [TEST] Lock adapter parity with `test/integration/python-adapter-plugin.test.ts` and any missing surface assertions required by the reconciled contract.

## Phase 2: Red Test Recovery For Core Runtime

- [x] T004 [MEM] Fix semantic deduplication behavior exercised by `tests/memory/test_semantic_dedupe.py`.
- [x] T005 [RETR] Fix semantic recall behavior exercised by `tests/retrieval/test_semantic_recall.py`.
- [x] T006 [RETR] Fix trust/conflict visibility and lexical-first subject expansion behavior exercised by `tests/test_integration.py`.
- [x] T007 [LINK] Fix Weaver explicit link, auto-link, and bounded multi-hop behavior exercised by `tests/test_integration.py`.

## Phase 3: Migration Management And Legacy Repair

- [x] T008 [OPS] Create or harden `MigrationManager` in `aegis_py/ops/migration.py` or the canonical migration owner so it reads `PRAGMA user_version` and applies sequential SQL scripts.
- [x] T009 [DB] Extract and maintain the current schema as versioned migration artifacts under `aegis_py/storage/migrations/`.
- [x] T010 [DB] Update storage initialization/repair to use the versioned migration path and support in-place legacy repair.
- [x] T011 [TEST] Write tests verifying incremental schema updates and the legacy repair path in `tests/test_storage.py`.

## Phase 4: Safe Backups, Scoped Preview, And Restores

- [x] T012 [OPS] Implement or harden `BackupManager` in the Python operations layer utilizing `sqlite3`'s native `.backup()` method.
- [x] T013 [OPS] Create or update CLI/runtime entrypoints to trigger and verify backup drills.
- [x] T014 [OPS] Fix scoped preview and scoped restore count/reporting behavior exercised by `tests/test_integration.py`.
- [x] T015 [TEST] Write tests asserting backups complete successfully without blocking concurrent writes and that scope-limited restore leaves untouched scopes intact.

## Phase 5: Health, Degradation States, And Benchmarks

- [ ] T016 [OPS] Create or harden `HealthMonitor` to track `HEALTHY`, `DEGRADED_SYNC`, and any other bounded degraded modes required by the spec.
- [ ] T017 [CORE] Integrate health-state handling into sync or optional remote features so local writes remain non-blocking during degraded states.
- [x] T018 [TEST] Verify offline-first operations remain unobstructed during a degraded state.
- [x] T019 [TEST] Add benchmark and regression gates for latency, semantic recall, and trust visibility.

## Phase 6: GSD Coordination And Closure

- [x] T020 [GSD] Update `.planning/STATE.md` and `.planning/ROADMAP.md` so execution notes remain derivative of `044-production-hardening`.
- [x] T021 [DOCS] Write closure evidence confirming the final validation counts and that the Python-owned runtime contract is stable.
