# Tasks: Resolution Decay Pragmatism

**Input**: Design documents from `/specs/040-resolution-decay-pragmatism/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Setup

- [x] T001 [FOUNDATION] Reconcile [.planning/STATE.md](/home/hali/.openclaw/extensions/memory-aegis-v7/.planning/STATE.md) with [specs/040-resolution-decay-pragmatism/spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism/spec.md) and [specs/040-resolution-decay-pragmatism/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism/plan.md)

## Phase 2: User Story 1 - Hard Conflict Resolution Prompting

- [x] T002 [US1] Add bounded hard-conflict classification helpers in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py`
- [x] T003 [US1] Define a structured resolution prompt payload and result serializer in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py`
- [x] T004 [US1] Expose user-resolution prompt and writeback behavior through `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py` and `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py`
- [x] T005 [US1] Add audit-preserving lifecycle handling for explicit resolution outcomes in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py` using `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/transitions.py`
- [x] T006 [US1] Add regression coverage for prompt-worthy vs deterministic conflicts in `/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_conflict_core.py` and `/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py`

## Phase 3: User Story 2 - Practical Archive-First Decay

- [x] T007 [US2] Refine retention scoring and bounded reinforcement in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py`
- [x] T008 [US2] Extend lifecycle persistence for cold, archive-candidate, and deprecated-candidate shaping in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py` and related hygiene helpers
- [x] T009 [US2] Add type or tier-aware decay guardrails for durable memory classes in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/` and `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py`
- [x] T010 [US2] Add regression coverage for archive-first decay and bounded recall recovery in `/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_hygiene.py` and `/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_lifecycle.py`

## Phase 4: User Story 3 - SQLite-First Graph Boundary

- [x] T011 [US3] Reconcile graph boundary and link-source-of-truth behavior in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py`, `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py`, and `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py`
- [x] T012 [US3] Add optional non-authoritative graph analysis helpers behind a local-only boundary in `/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/graph_analysis.py`
- [x] T013 [US3] Add graph-boundary regression coverage in `/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py` and `/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_python_only_runtime_contract.py`

## Phase 5: Polish And Validation

- [x] T014 [FOUNDATION] Run the canonical prerequisite workflow and record evidence in [specs/040-resolution-decay-pragmatism/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism/plan.md)
- [x] T015 [FOUNDATION] Run the canonical Python regression workflow and append evidence to [specs/040-resolution-decay-pragmatism/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism/plan.md)
- [x] T016 [FOUNDATION] Reconcile completion state in [specs/040-resolution-decay-pragmatism/tasks.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism/tasks.md)
