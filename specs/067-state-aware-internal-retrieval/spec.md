# Feature Specification: State-Aware Internal Retrieval

**Feature Branch**: `067-state-aware-internal-retrieval`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Open the tranche immediately after `066-formal-memory-state-machine` by letting retrieval and policy internals consume `admission_state` for bounded filtering and trust shaping, without attempting a broad retrieval rewrite.

## User Scenarios & Testing

### User Story 1 - Retrieval Internals Respect Admission State (Priority: P1)

As a maintainer, I want retrieval internals to distinguish validated, hypothesized, draft, invalidated, and consolidated memories through stable state-aware rules, so later ranking and policy work stop reconstructing admission intent from metadata.

**Independent Test**: Seed memories with different admission states and verify internal retrieval helpers apply bounded state-aware filtering or shaping without changing the public payload shape.

### User Story 2 - Policy Internals Can Inspect State Directly (Priority: P1)

As a maintainer, I want policy-oriented internals to read admission state directly, so follow-on governance and promotion work can reason over explicit states rather than mixed lifecycle heuristics.

**Independent Test**: Run an internal policy-oriented path and verify it can inspect and report state-aware memory selections or counts.

### User Story 3 - Public Retrieval Contract Stays Stable (Priority: P1)

As an integrator, I want current public retrieval/runtime payloads to remain stable while state-aware internals land, so the runtime hardens progressively without client breakage.

**Independent Test**: Re-run Python and host contract tests and verify existing public search/status/context payloads remain green after state-aware internal retrieval lands.

## Requirements

- **FR-001**: Retrieval internals MUST be able to inspect `admission_state` directly.
- **FR-002**: This tranche MUST add bounded state-aware retrieval or policy shaping without rewriting the full retrieval pipeline.
- **FR-003**: Draft or invalidated memories MUST remain controllable through internal rules without breaking current public contracts.
- **FR-004**: Public retrieval and tool payload shapes MUST remain stable.
- **FR-005**: This tranche MUST NOT become a broad reranker/router redesign.
- **FR-006**: This tranche SHOULD leave clear seams for later deeper retrieval-state integration work.

## Success Criteria

- **SC-001**: Retrieval and policy internals can consume explicit admission states directly.
- **SC-002**: State-aware filtering or shaping lands without public payload drift.
- **SC-003**: Later retrieval work can build on real state-aware internals rather than metadata reconstruction hacks.
