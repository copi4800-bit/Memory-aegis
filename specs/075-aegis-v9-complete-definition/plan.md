# Implementation Plan: Aegis v9 Complete Definition

## Phase 1: Semantic & Architectural Completion (Spec Kit)
1. **Enrich MemoryRecordV9**: Update the data model to include `fact_kind`, `singleton_fact`, and enhanced lifecycle fields.
2. **Formalize Score Tiers**: Refactor the scorer to follow the `S_final = S_base + Δ_judge + Δ_life + H_constraints` formula.
3. **Enhance Adapter Mapping**: Implement exhaustive signal mapping in `adapter.py` for trust, conflict, and lifecycle.

## Phase 2: Runtime & Retrieval Completion (GSD Execute)
1. **Standardize Query Signals**: Implement a robust builder for query signals with support for intents and normalization.
2. **Retrieve Gatekeeper**: Ensure v9 reranking is the final authority in the search pipeline.
3. **Operational Modes**: Add support for switching between v8, shadow v9, and v9 primary modes.

## Phase 3: UX & Explanation Completion (GSD Execute)
1. **Multi-level Explanations**: Upgrade the renderer for compact, standard, and deep narratives.
2. **Public Audit Metadata**: Expose the full `v9_audit` payload in the surface layer.
3. **Memory Health v2**: Integrate v9 metrics into the health reporting surface.

## Phase 4: Quality & Validation (GSD Verify)
1. **End-to-End Pytest Suite**: Create a comprehensive test suite covering all v9 logic paths.
2. **Shadow Evaluation**: Build and run the evaluation script to compare performance with v8.
3. **Stress Testing**: Perform gauntlet runs for truth alignment and conflict pressure.

## Success Criteria
- [ ] 100% of new pytest cases pass.
- [ ] v9 demonstrates superior truth alignment in benchmarks.
- [ ] Audit metadata is correctly exposed and faithful.
