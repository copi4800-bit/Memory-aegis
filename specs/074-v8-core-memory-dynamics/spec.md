# Feature Specification: V8 Core Memory Dynamics

**Feature Branch**: `074-v8-core-memory-dynamics`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: Distill the three v8 theory documents (`7.md`, `11.md`, `12.md`) into one executable tranche that adds only the smallest measurable subset of memory dynamics the current Python runtime can actually support.

## User Scenarios & Testing

### User Story 1 - Retrieval Uses Dynamic Trust Inputs (Priority: P1)

As a maintainer, I want retrieval to consume bounded dynamic signals beyond plain similarity, so Aegis can start behaving like a memory field rather than a static lookup table.

**Why this priority**: This is the smallest slice that turns the v8 theory into user-visible retrieval behavior without opening a broad architecture rewrite.

**Independent Test**: Seed comparable memories with different evidence, conflict, usage, and states, then verify ranking changes through a bounded dynamic retrieval score.

**Acceptance Scenarios**:

1. **Given** two comparable memories with similar lexical relevance, **When** one has stronger evidence and lower conflict pressure, **Then** the higher-trust memory ranks first.
2. **Given** two memories with similar trust, **When** one has higher retrieval readiness from recent useful usage, **Then** retrieval prefers the more ready memory.

---

### User Story 2 - Runtime Computes V8-Core State Signals (Priority: P1)

As a maintainer, I want the runtime to compute a minimal v8-core state vector that is explainable and bounded, so later retrieval and governance work can build on explicit dynamics rather than inferred heuristics.

**Why this priority**: Without explicit signals, the v8 theory remains a document only and later retrieval/governance work will keep reconstructing trust state ad hoc.

**Independent Test**: Run a focused runtime path and verify bounded signals exist for evidence, conflict pressure, usage reinforcement, trust, and retrieval readiness.

**Acceptance Scenarios**:

1. **Given** a memory with evidence and supporting neighbors, **When** the runtime computes v8-core signals, **Then** evidence, support, trust, and readiness stay within bounded ranges.
2. **Given** a memory with a strong conflicting peer, **When** the runtime computes v8-core signals, **Then** conflict pressure rises and trust/readiness decrease relative to the non-conflicted case.

---

### User Story 3 - State Promotion Uses Hysteresis-Friendly Gates (Priority: P2)

As a maintainer, I want a minimal transition surface that respects state admissibility and hysteresis, so draft or hypothesized memories do not churn unpredictably once v8-core scoring lands.

**Why this priority**: State-aware retrieval becomes unstable if promotion/demotion still uses only loose heuristics without explicit dynamic gates.

**Independent Test**: Seed memories around promotion and demotion thresholds and verify transition decisions use separate bounded thresholds instead of a single unstable cutoff.

**Acceptance Scenarios**:

1. **Given** a draft memory above the promote thresholds, **When** transition evaluation runs, **Then** it can promote to `validated`.
2. **Given** a validated memory that dips slightly but not below the demote threshold, **When** transition evaluation runs, **Then** it remains `validated`.

### User Story 4 - Runtime Learns From Retrieval Outcomes (Priority: P2)

As a maintainer, I want the runtime to capture bounded usage, regret, decay, and belief updates from retrieval outcomes, so the v8 tranche reflects actual memory dynamics instead of only static surrogates.

**Why this priority**: The theory documents explicitly model usage reinforcement, regret, decay, and belief evolution. Without at least a bounded feedback path, v8 remains mostly a scoring layer rather than a dynamics layer.

**Independent Test**: Apply positive and negative retrieval outcomes to comparable memories, then verify dynamic signals and ranking shift in the expected direction while governance and evidence artifacts remain traceable.

**Acceptance Scenarios**:

1. **Given** a memory with a successful retrieval outcome, **When** bounded v8 feedback is applied, **Then** usage and belief increase without leaving the bounded signal range.
2. **Given** a memory with an unsuccessful or overridden retrieval outcome, **When** bounded v8 feedback is applied, **Then** regret and decay rise and trust/readiness decline relative to the positive case.

### Edge Cases

- What happens when a memory has no peers and no evidence beyond its ingest event?
- How does the runtime behave when all comparable neighbors are conflicted but low trust?
- What happens when usage or regret signals are absent for older memories?
- How does the system avoid turning invalidated or archived memories into high-readiness retrieval candidates?
- How does bounded feedback avoid becoming a hidden autonomous rewrite of trust state?

## Requirements

### Functional Requirements

- **FR-001**: The runtime MUST expose a bounded v8-core signal set for each memory consisting of evidence signal, support pressure, conflict pressure, usage reinforcement, trust, and retrieval readiness.
- **FR-002**: Evidence strength MUST use a bounded signal derived from existing evidence artifacts rather than raw evidence counts alone.
- **FR-003**: Support and conflict pressure MUST be normalized so large neighborhoods do not explode retrieval or trust calculations.
- **FR-004**: Retrieval scoring MUST add bounded trust and retrieval readiness terms on top of existing relevance and state admissibility rather than replacing the full current retrieval pipeline.
- **FR-005**: Retrieval scoring MUST preserve current scope isolation and public payload contracts.
- **FR-006**: The first v8-core tranche MUST use a bounded surrogate for usage reinforcement based on currently observable runtime signals and MUST NOT depend on unavailable full downstream utility learning.
- **FR-007**: The first v8-core tranche MUST leave full regret learning, energy-function optimization, and large-scale simulator work out of scope.
- **FR-008**: The runtime MUST provide an internal helper or operator-facing surface that explains how a memory’s v8-core trust/readiness terms were derived.
- **FR-009**: Transition logic in this tranche MUST use explicit promote/demote thresholds with hysteresis-friendly separation for at least the draft/validated boundary.
- **FR-010**: Invalidated memories MUST remain inadmissible for normal retrieval regardless of dynamic trust or readiness.
- **FR-011**: This tranche MUST NOT introduce a broad schema rewrite or a full memory-field simulator.
- **FR-012**: The runtime MUST provide a bounded outcome-feedback path that updates usage reinforcement, regret pressure, decay, and belief using existing per-memory metadata rather than a broad schema rewrite.
- **FR-013**: Outcome feedback mutations MUST write governance-visible artifacts so later tuning can inspect how dynamic state changed.
- **FR-014**: The runtime MUST expose a bounded bundle-level energy/objective snapshot for retrieval bundles so benchmark and tuning work can measure field quality without introducing a full simulator.
- **FR-015**: The v8 benchmark suite MUST include at least one retrieval-feedback scenario that checks credit assignment alignment and bounded objective regression tolerance for a seeded bundle case.

### Key Entities

- **V8CoreSignals**: Bounded per-memory dynamic terms such as `evidence_signal`, `support_signal`, `conflict_signal`, `usage_signal`, `trust_score`, and `readiness_score`.
- **DynamicRetrievalScore**: Internal ranking payload that combines current relevance, trust, readiness, admissibility, and bounded cost.
- **TransitionGate**: Hysteresis-aware threshold contract that governs promotion/demotion decisions for the first dynamic state boundary.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A focused retrieval test can demonstrate ranking changes caused by v8-core trust/readiness signals without breaking current scope contracts.
- **SC-002**: All new v8-core state signals are bounded and explainable in runtime tests.
- **SC-003**: The first v8-core tranche lands without requiring a broad schema rewrite or simulator-first architecture fork.
- **SC-004**: Existing runtime correctness and apocalypse validation remain green after v8-core retrieval shaping lands.
- **SC-005**: A focused runtime test can demonstrate that positive and negative outcome feedback move usage/regret/decay/belief in the expected direction and affect retrieval ranking without breaking governance traceability.
- **SC-006**: The v8 benchmark suite can report bundle energy/objective metrics and pass at least one retrieval-feedback gate where selected memories receive more credit than overridden ones and bundle objective regression stays within a bounded tolerance.
