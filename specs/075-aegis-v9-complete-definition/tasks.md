# Task List: Aegis v9 Complete Definition

## Phase 1: Semantic & Architectural Completion
- [ ] Task 1.1: Update `aegis_py/v9/models.py` with `fact_kind`, `singleton_fact`, and enhanced lifecycle fields.
- [ ] Task 1.2: Refactor `aegis_py/v9/scorer.py` to formalize score tiers (base, judge delta, life delta, hard constraints).
- [ ] Task 1.3: Update `aegis_py/v9/adapter.py` for rich signal mapping (evidence, conflict, correction, lifecycle).

## Phase 2: Runtime & Retrieval Completion
- [ ] Task 2.1: Upgrade `aegis_py/v9/query_signals.py` to support intents and normalized [0,1] signals.
- [ ] Task 2.2: Refactor `aegis_py/retrieval/search.py` to ensure v9 reranking is the final gatekeeper.
- [ ] Task 2.3: Implement operational modes (`v8_primary`, `shadow_v9`, `v9_primary`) via configuration/flags.

## Phase 3: UX & Explanation Completion
- [ ] Task 3.1: Upgrade `aegis_py/v9/translator.py` for compact, standard, and deep narratives.
- [ ] Task 3.2: Expose the `v9_audit` payload in `aegis_py/surface.py`.
- [ ] Task 3.3: Update `aegis_py/health_surface.py` to reflect v9 metrics.

## Phase 4: Quality & Validation
- [ ] Task 4.1: Create comprehensive integration tests in `tests/test_v9_full_path.py` (no SQL mocks).
- [ ] Task 4.2: Develop and run `scripts/v9_shadow_eval.py` for v8 vs v9 comparison.
- [ ] Task 4.3: Execute v9-specific stress gauntlet.

## Verification
- [ ] Verify SC-001 (Pytest pass)
- [ ] Verify SC-002 (Shadow eval success)
- [ ] Verify SC-003 (Faithful explanations)
- [ ] Verify SC-004 (Latency within limits)
- [ ] Verify SC-005 (Audit findings addressed)
