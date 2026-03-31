# Tasks: V8 Core Memory Dynamics

**Input**: Design documents from `/specs/074-v8-core-memory-dynamics/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: V8-Core Signal Foundation

- [x] T001 [CORE] Add bounded v8-core signal helpers for evidence, support, conflict, trust, and readiness in `aegis_py/`.
- [x] T002 [CORE] Define one bounded usage surrogate that the current runtime can compute without full downstream utility learning.
- [x] T003 [CORE] Add an internal or operator-facing explanation seam for v8-core signal derivation.

## Phase 2: Dynamic Retrieval Shaping

- [x] T004 [CORE] Update retrieval internals in `aegis_py/retrieval/` to consume trust and readiness as bounded ranking terms without breaking scope isolation.
- [x] T005 [CORE] Preserve current public payload shapes while exposing dynamic ranking evidence through internal/operator-facing helpers only.

## Phase 3: Minimal Transition Gate

- [x] T006 [CORE] Add a minimal hysteresis-aware draft/validated transition gate using explicit promote and demote thresholds.
- [x] T007 [CORE] Ensure invalidated memories remain inadmissible regardless of dynamic trust/readiness.

## Phase 4: Validation

- [x] T008 [TEST] Add focused retrieval tests in `tests/test_retrieval.py` for evidence/conflict/readiness-driven ranking.
- [x] T009 [TEST] Add runtime tests in `tests/test_memory_core.py` or adjacent suites for bounded v8-core signals and hysteresis behavior.
- [x] T010 [TEST] Re-run `tests/test_apocalypse_runtime.py` to verify runtime correctness remains green after dynamic shaping.

## Phase 5: Planning Integration

- [x] T011 [DOCS] Update `.planning/ROADMAP.md` so the next bounded architecture tranche points at `074-v8-core-memory-dynamics`.
- [x] T012 [DOCS] Update `.planning/STATE.md` so current focus explicitly distinguishes executable v8-core from broader theory-only dynamics work.

## Phase 6: Outcome Feedback Dynamics

- [x] T013 [CORE] Add a bounded v8 outcome-feedback path for usage, regret, decay, and belief updates in `aegis_py/app.py` and `aegis_py/retrieval/v8_dynamics.py`.
- [x] T014 [CORE] Preserve operator-facing explainability for the new feedback-driven dynamic state in `aegis_py/operator_surface.py`.
- [x] T015 [TEST] Add retrieval/runtime coverage for positive and negative v8 outcome feedback in `tests/test_retrieval.py`.
- [x] T016 [TEST] Extend the v8 dynamics benchmark fixtures to include feedback-driven usage/regret cases in `tests/benchmarks/test_v8_dynamics_sli.py` and `scripts/v8_dynamics_benchmark.py`.

## Phase 7: Objective Regression Gate

- [x] T017 [CORE] Add a bounded bundle-level energy/objective snapshot for retrieval bundles in `aegis_py/retrieval/v8_dynamics.py` and `aegis_py/app.py`.
- [x] T018 [TEST] Add retrieval/runtime coverage for bundle snapshots and benchmarked retrieval-feedback alignment in `tests/test_retrieval.py` and `tests/benchmarks/test_v8_dynamics_sli.py`.
- [x] T019 [TEST] Extend the benchmark harness and script to gate on feedback alignment and bounded objective regression tolerance in `aegis_py/retrieval/v8_benchmark.py` and `scripts/v8_dynamics_benchmark.py`.
