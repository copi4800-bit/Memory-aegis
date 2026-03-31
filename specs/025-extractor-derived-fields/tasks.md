# Tasks: Extractor Derived Fields

**Input**: Design documents from `/specs/025-extractor-derived-fields/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/025-extractor-derived-fields/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/025-extractor-derived-fields/spec.md) and [specs/025-extractor-derived-fields/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/025-extractor-derived-fields/plan.md)

## Phase 2: Extractor Slice

- [x] T002 [US1] Add deterministic fallback subject and summary extraction in [aegis_py/memory/extractor.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/extractor.py)
- [x] T003 [US1] Wire fallback derived fields into [aegis_py/memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py)
- [x] T004 [US2] Add Python integration coverage for derived fields and explicit override preservation in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)

## Phase 3: Polish

- [x] T005 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/025-extractor-derived-fields/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/025-extractor-derived-fields/plan.md)
- [x] T006 [FOUNDATION] Reconcile completion state in [specs/025-extractor-derived-fields/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/025-extractor-derived-fields/tasks.md)
