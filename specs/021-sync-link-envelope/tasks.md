# Tasks: Sync Link Envelope

**Input**: Design documents from `/specs/021-sync-link-envelope/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/021-sync-link-envelope/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/021-sync-link-envelope/spec.md) and [specs/021-sync-link-envelope/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/021-sync-link-envelope/plan.md)

## Phase 2: Link-Aware Sync

- [x] T002 [US1] Add Python integration coverage for link-aware sync envelopes in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Extend [aegis_py/operations.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/operations.py) export/preview/import flows to carry links

## Phase 3: Documentation

- [x] T004 [US2] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to document link-aware sync envelopes

## Phase 4: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/021-sync-link-envelope/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/021-sync-link-envelope/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/021-sync-link-envelope/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/021-sync-link-envelope/tasks.md)
