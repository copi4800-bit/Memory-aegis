# Tasks: Entity Structure Lite

**Input**: Design documents from `/specs/017-entity-structure-lite/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile `.planning/STATE.md` with [specs/017-entity-structure-lite/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/017-entity-structure-lite/spec.md) and [specs/017-entity-structure-lite/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/017-entity-structure-lite/plan.md)

## Phase 2: Entity Extraction

- [x] T002 [US1] Add Python integration coverage for entity metadata extraction in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T003 [US1] Add a lightweight entity extractor under [aegis_py/memory](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory) and integrate it into ingest

## Phase 3: Entity Expansion

- [x] T004 [US2] Add Python integration coverage for `entity_expansion` in [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py)
- [x] T005 [US2] Add bounded entity-overlap expansion in [aegis_py/retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)

## Phase 4: Documentation

- [x] T006 [US2] Update [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) to describe entity-structure-lite behavior

## Phase 5: Polish

- [x] T007 [FOUNDATION] Run the canonical validation workflow and record evidence in [specs/017-entity-structure-lite/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/017-entity-structure-lite/plan.md)
- [x] T008 [FOUNDATION] Reconcile completion state in [specs/017-entity-structure-lite/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/017-entity-structure-lite/tasks.md)
