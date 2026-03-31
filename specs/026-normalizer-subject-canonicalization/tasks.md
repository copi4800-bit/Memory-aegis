# Tasks: Normalizer Subject Canonicalization

**Input**: Design documents from `/specs/026-normalizer-subject-canonicalization/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/026-normalizer-subject-canonicalization/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/026-normalizer-subject-canonicalization/spec.md) and [specs/026-normalizer-subject-canonicalization/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/026-normalizer-subject-canonicalization/plan.md)

## Phase 2: Normalizer Slice

- [x] T002 [US1] Add deterministic subject canonicalization in [aegis_py/memory/normalizer.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/normalizer.py)
- [x] T003 [US1] Wire subject canonicalization into [aegis_py/memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py)
- [x] T004 [US2] Add Python integration coverage for explicit and derived subject normalization plus explicit null preservation in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/026-normalizer-subject-canonicalization/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/026-normalizer-subject-canonicalization/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/026-normalizer-subject-canonicalization/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/026-normalizer-subject-canonicalization/tasks.md)
