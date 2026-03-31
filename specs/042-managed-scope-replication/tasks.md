
# Tasks: Managed Scope Replication And Operational Audit

**Input**: Design documents from `/specs/042-managed-scope-replication/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Storage & Identity

- [x] T001 [DB] Update SQLite schema in `aegis_py/storage/schema.sql` and `aegis_py/storage/models.py` to support node identity and replication provenance.
- [x] T002 [DB] Create migration script for existing local-only databases.
- [x] T003 [CORE] Implement node identity generation and retrieval in `aegis_py/replication/identity.py`.
- [x] T004 [TEST] Write tests for identity generation and DB migrations.

## Phase 2: Replication Payloads & Replay Safety

- [x] T005 [SYNC] Define `ReplicationPayload` data structures for exporting/importing batches of memory mutations.
- [x] T006 [SYNC] Implement idempotent mutation application logic in `aegis_py/replication/sync.py`.
- [x] T007 [TEST] Write integration tests simulating payload interruptions and duplicate replays.

## Phase 3: Conflict Visibility

- [x] T008 [SYNC] Implement concurrent edit detection when applying payloads in `aegis_py/replication/conflict.py`.
- [x] T009 [CORE] Surface `reconcile-required` state via API/CLI instead of silent merges.
- [x] T010 [TEST] Write tests ensuring conflicting edits trigger a visible conflict state.

## Phase 4: Operational Observability

- [ ] [OBS] Implement metrics tracking for sync lag, success/failure counts in `aegis_py/observability/metrics.py`.
- [ ] [OBS] Ensure failures are logged with full context (node identity, payload size, error type).

## Phase 5: GSD & Validation

- [x] T011 [GSD] Update `.planning/STATE.md` to reflect ongoing work on `042-managed-scope-replication`.
- [ ] T012 [DOCS] Draft migration notes for operators updating to the distributed schema.
