# Tasks: Classifier Lane Assignment

**Input**: Design documents from `/specs/027-classifier-lane-assignment/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/027-classifier-lane-assignment/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/027-classifier-lane-assignment/spec.md) and [specs/027-classifier-lane-assignment/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/027-classifier-lane-assignment/plan.md)

## Phase 2: Classifier Slice

- [x] T002 [US1] Add deterministic lane inference in [aegis_py/memory/classifier.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/classifier.py)
- [x] T003 [US1] Wire omitted-type lane inference into [aegis_py/memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py)
- [x] T004 [US1] Allow Python-owned store surfaces to pass omitted types through [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py), [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py), and [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py)
- [x] T005 [US2] Add Python integration coverage for inferred lanes and explicit preservation in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

## Phase 3: Polish

- [x] T006 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/027-classifier-lane-assignment/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/027-classifier-lane-assignment/plan.md)
- [x] T007 [FOUNDATION] Reconcile completion state in [specs/027-classifier-lane-assignment/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/027-classifier-lane-assignment/tasks.md)
