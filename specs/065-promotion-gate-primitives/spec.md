# Feature Specification: Promotion Gate Primitives

**Feature Branch**: `065-promotion-gate-primitives`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Open the tranche immediately after `064-internal-evidence-consumption` by introducing bounded promotion-gate primitives that separate extraction from promotion into retrievable memory, without yet landing the full v7 state machine or a retrieval rewrite.

## User Scenarios & Testing

### User Story 1 - Candidates Can Be Evaluated Before Promotion (Priority: P1)

As a maintainer, I want extracted memory candidates to pass through a bounded internal promotion check before they become normal retrievable memories, so the runtime stops implicitly treating every extraction as trusted memory.

**Independent Test**: Submit a candidate through the canonical path and verify the runtime can evaluate and classify it before promotion without changing the public retrieval shape.

### User Story 2 - Evidence And Contradiction Signals Inform Promotion (Priority: P1)

As a maintainer, I want promotion primitives to consult evidence presence and basic contradiction/confidence signals, so later policy work starts from explicit promotion inputs rather than ad hoc heuristics.

**Independent Test**: Feed a candidate with evidence present and a candidate with missing or weak support and verify the internal gate returns distinct admission outcomes.

### User Story 3 - Public Runtime Surface Remains Stable (Priority: P1)

As an integrator, I want `memory_remember`, `memory_recall`, `memory_search`, and `memory_context_pack` to keep their current payloads while promotion primitives land internally, so the next architecture step hardens admission without client breakage.

**Independent Test**: Re-run Python and host contract tests and verify existing public retrieval/runtime surfaces remain green after promotion-gate primitives are introduced.

## Requirements

- **FR-001**: The Python runtime MUST define a bounded internal candidate or pre-promotion representation.
- **FR-002**: The runtime MUST expose an internal promotion-gate helper that evaluates whether a candidate is promotable.
- **FR-003**: The promotion-gate helper MUST be able to consume evidence linkage and basic contradiction/confidence inputs.
- **FR-004**: This tranche MUST preserve current public retrieval and tool payload shapes.
- **FR-005**: This tranche MUST NOT introduce the full richer memory state model from the later state-machine tranche.
- **FR-006**: This tranche SHOULD leave clear seams for a later formal state-machine slice to map promotion decisions into richer states.

## Success Criteria

- **SC-001**: Canonical ingest no longer relies only on implicit “extract then trust” behavior internally.
- **SC-002**: Promotion decisions can be explained in terms of evidence presence and bounded admission signals.
- **SC-003**: The later state-machine tranche can build on a real promotion boundary instead of mixing promotion into storage and retrieval code paths.
