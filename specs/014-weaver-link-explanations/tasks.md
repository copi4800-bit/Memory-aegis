# Tasks: Weaver Link Explanations

**Input**: Design documents from `/specs/014-weaver-link-explanations/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/014-weaver-link-explanations/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/014-weaver-link-explanations/spec.md) and [specs/014-weaver-link-explanations/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/014-weaver-link-explanations/plan.md)

## Phase 2: Link Explanation Payloads

- [x] T002 [US1] Add Python integration coverage for link explanation fields in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Extend [aegis_py/retrieval/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py) and [aegis_py/retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) with richer link explanation fields
- [x] T004 [US2] Extend [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py) serialization to preserve the new explanation fields

## Phase 3: Documentation

- [x] T005 [US3] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to describe richer link explanations

## Phase 4: Polish

- [x] T006 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/014-weaver-link-explanations/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/014-weaver-link-explanations/plan.md)
- [x] T007 [FOUNDATION] Reconcile completion state in [specs/014-weaver-link-explanations/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/014-weaver-link-explanations/tasks.md)
