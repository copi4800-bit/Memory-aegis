# Tasks: Weaver Multi-Hop Bounded

**Input**: Design documents from `/specs/015-weaver-multi-hop-bounded/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/015-weaver-multi-hop-bounded/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/015-weaver-multi-hop-bounded/spec.md) and [specs/015-weaver-multi-hop-bounded/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/015-weaver-multi-hop-bounded/plan.md)

## Phase 2: Bounded Multi-Hop Expansion

- [x] T002 [US1] Add Python integration coverage for one-hop-extra Weaver expansion in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Extend [aegis_py/retrieval/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py) and [aegis_py/retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) with bounded multi-hop expansion metadata
- [x] T004 [US2] Update [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py) and [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to document the bounded multi-hop step

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/015-weaver-multi-hop-bounded/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/015-weaver-multi-hop-bounded/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/015-weaver-multi-hop-bounded/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/015-weaver-multi-hop-bounded/tasks.md)
