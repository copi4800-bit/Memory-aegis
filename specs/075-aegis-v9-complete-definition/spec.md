# Feature Specification: Aegis v9 Complete Definition

**Feature Branch**: `075-aegis-v9-complete-definition`  
**Created**: 2026-04-01  
**Status**: Active  
**Input**: Comprehensive technical and product completion of Aegis v9 as defined in `4.md`.

## User Scenarios & Testing

### User Story 1 - Unified Judgment Engine (Priority: P1)

As a user, I want Aegis to provide the most accurate and truthful result by considering trust, conflict, and correction signals, so I don't have to manually verify which information is current.

**Why this priority**: This is the core value proposition of v9—moving from "search" to "judgment".

**Independent Test**: Use the `tests/test_v9_runtime_full_path.py` (improved) to verify that a correction winner always outranks a superseded record, even with lower lexical overlap.

**Acceptance Scenarios**:
1. **Given** a corrected fact (e.g., address change), **When** I search for that fact, **Then** the new version is ranked #1 with a "correction winner" explanation.
2. **Given** a high-trust but low-lexical match, **When** it competes with a low-trust but high-lexical match, **Then** the high-trust match is preferred if it meets the truth threshold.

---

### User Story 2 - Faithful & Deep Explanations (Priority: P1)

As an operator, I want to see the exact reasoning (decisive factors and deltas) behind a ranking decision, so I can audit and trust the system's logic.

**Why this priority**: Trust in an AI system requires transparency. v9's "explainable by construction" philosophy must be fully visible.

**Independent Test**: Verify the `v9_audit` payload in `serialize_search_result` contains all deltas (judge, life) and the correct `decisive_factor`.

**Acceptance Scenarios**:
1. **Given** a result ranked by trust, **When** I view the explanation, **Then** it explicitly mentions "high trust" and the `v9_audit` shows a high `judge_delta`.
2. **Given** a result penalized by conflict, **When** I view the deep explanation, **Then** it shows the negative `conflict` factor in the `v9_audit` payload.

---

### User Story 3 - Robust Lifecycle & State Mapping (Priority: P2)

As a system, I want memory records to flow correctly through their lifecycle (Draft -> Validated -> Archived), so the judgment engine treats them according to their maturity and reliability.

**Why this priority**: Correct scoring depends on correct state. A "Draft" should not be treated with the same weight as a "Consolidated" fact.

**Independent Test**: Create records in various states and verify `adapter.py` maps them correctly to `MemoryRecordV9` without guessing.

**Acceptance Scenarios**:
1. **Given** a memory marked as 'active' in storage, **When** it is adapted to v9, **Then** its lifecycle state is `VALIDATED` or better.
2. **Given** a memory marked as 'archived', **When** it is adapted, **Then** it is excluded from normal recall or heavily penalized.

---

### User Story 4 - Shadow Evaluation & Metrics (Priority: P2)

As a maintainer, I want to compare v9 performance against v8 using objective metrics, so I can confidently switch to v9 as the primary engine.

**Why this priority**: Data-driven release decisions are mandatory for production hardening.

**Independent Test**: Run a shadow evaluation script that reports `truth_winner_top1_rate` and `latency_delta`.

**Acceptance Scenarios**:
1. **Given** a benchmark suite, **When** run in shadow mode, **Then** it produces a report comparing v8 and v9 rankings.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST implement the canonical v9 score formula: `S_final = S_base + Δ_judge + Δ_life + H_constraints`.
- **FR-002**: `adapter.py` MUST support rich signal mapping including `evidence_strength`, `conflict_severity`, and `correction_freshness`.
- **FR-003**: `build_v9_query_signals` MUST provide normalized signals [0,1] for `semantic_relevance`, `lexical_match`, and `link_support`.
- **FR-004**: The retrieval pipeline MUST allow v9 to act as the primary gatekeeper, reranking candidates before final filtering.
- **FR-005**: `FaithfulRenderer` MUST support three levels of explanation: compact, standard, and deep.
- **FR-006**: The system MUST support `v8_primary`, `shadow_v9`, and `v9_primary` modes via configuration.
- **FR-007**: Fact slot semantics MUST distinguish between `singleton` (overwrite) and `multivalued` (coexist) facts.
- **FR-008**: Lifecycle mapping MUST be explicit and avoid falling back to `DRAFT` for active, non-draft records.

### Key Entities

- **MemoryRecordV9**: Enhanced with `fact_kind`, `singleton_fact`, and `lifecycle_state`.
- **JudgmentTrace**: Enhanced to carry all deltas and factors for auditability.
- **V9QuerySignals**: Standardized input contract for the scorer.
- **ShadowEvalReport**: Objective comparison of v8 vs v9 performance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of v9-specific pytest cases (Truth, Conflict, Bias, Explainability, Lifecycle) pass in a clean environment.
- **SC-002**: Shadow evaluation demonstrates that v9 `truth_winner_top1_rate` is equal to or better than v8.
- **SC-003**: Human explanations correctly identify the `decisive_factor` in 100% of tested search results.
- **SC-004**: Latency overhead for v9 reranking stays within acceptable limits (e.g., < 20% increase over v8).
- **SC-005**: All "High" findings from the previous audit are addressed and verified.
