# Feature Specification: Internal Evidence Consumption

**Feature Branch**: `064-internal-evidence-consumption`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Open the tranche immediately after `063-evidence-log-foundation` by making the new evidence layer consumable inside the Python runtime without yet introducing a full admission gate, promotion state machine, or retrieval rewrite.

## User Scenarios & Testing

### User Story 1 - Runtime Can Inspect Evidence For A Memory (Priority: P1)

As a maintainer, I want internal runtime code to fetch evidence rows for a memory through stable helpers, so future promotion and validation work can depend on evidence without reaching into raw SQL ad hoc.

**Independent Test**: Persist a memory with evidence linkage and verify the runtime can retrieve the linked evidence event through a first-class internal API.

### User Story 2 - Rebuild/Operations Can Report Evidence Coverage (Priority: P1)

As a maintainer, I want operational flows to inspect whether memories are evidence-backed, so later promotion work can distinguish “raw evidence present” from “legacy memory missing evidence” without changing public retrieval payloads yet.

**Independent Test**: Run a runtime inspection or rebuild-oriented path and verify it can report evidence coverage for stored memories without breaking current public output contracts.

### User Story 3 - Evidence Remains Internal And Backward-Compatible (Priority: P1)

As an integrator, I want the current `memory_remember`, `memory_recall`, `memory_search`, and `memory_context_pack` payloads to stay stable while internal evidence consumption is added, so the next tranche can harden internals without destabilizing clients.

**Independent Test**: Re-run Python and host contract tests and verify the existing public retrieval/runtime shapes still pass after evidence-consumption helpers land.

## Requirements

- **FR-001**: The Python runtime MUST expose internal helpers for resolving evidence rows linked to a memory.
- **FR-002**: The runtime MUST support internal inspection of evidence coverage without requiring direct SQL from higher layers.
- **FR-003**: This tranche MUST preserve the current public retrieval and tool payload shapes.
- **FR-004**: This tranche MUST remain local-first and SQLite-native.
- **FR-005**: This tranche MUST NOT introduce a full admission gate, promotion validator, or richer state machine.
- **FR-006**: This tranche SHOULD leave clear seams for a later promotion-gate slice to consume evidence-backed memory records.

## Success Criteria

- **SC-001**: Internal runtime code can look up evidence events for stored memories through stable helpers rather than ad hoc queries.
- **SC-002**: Evidence coverage can be inspected or reported for memory records without changing public retrieval contracts.
- **SC-003**: The next promotion-focused tranche can assume both evidence storage and evidence lookup primitives already exist.
