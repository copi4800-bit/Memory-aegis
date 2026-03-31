# Tasks: Weaver Link Reranking

**Input**: Design documents from `/specs/016-weaver-link-reranking/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/016-weaver-link-reranking/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/016-weaver-link-reranking/spec.md) and [specs/016-weaver-link-reranking/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/016-weaver-link-reranking/plan.md)

## Phase 2: Link Scoring

- [x] T002 [US1] Add Python integration coverage for hop-aware and link-type-aware reranking in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add a dedicated link scoring helper in [aegis_py/retrieval/contract.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/contract.py)
- [x] T004 [US2] Route explicit link expansion scoring through the helper in [aegis_py/retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)

## Phase 3: Documentation

- [x] T005 [US2] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to mention hop-aware and link-type-aware Weaver reranking

## Phase 4: Polish

- [x] T006 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/016-weaver-link-reranking/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/016-weaver-link-reranking/plan.md)
- [x] T007 [FOUNDATION] Reconcile completion state in [specs/016-weaver-link-reranking/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/016-weaver-link-reranking/tasks.md)
