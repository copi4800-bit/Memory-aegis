# Tasks: Scorer Write-Time Salience

**Input**: Design documents from `/specs/028-scorer-write-time-salience/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/028-scorer-write-time-salience/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/028-scorer-write-time-salience/spec.md) and [specs/028-scorer-write-time-salience/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/028-scorer-write-time-salience/plan.md)

## Phase 2: Scorer Slice

- [x] T002 [US1] Add deterministic write-time scoring in [aegis_py/memory/scorer.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/scorer.py)
- [x] T003 [US1] Wire inferred and explicit score handling into [aegis_py/memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py) and [aegis_py/memory/factory.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/factory.py)
- [x] T004 [US2] Add Python integration coverage for inferred scoring and explicit score preservation in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/028-scorer-write-time-salience/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/028-scorer-write-time-salience/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/028-scorer-write-time-salience/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/028-scorer-write-time-salience/tasks.md)
