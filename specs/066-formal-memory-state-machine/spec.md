# Feature Specification: Formal Memory State Machine

**Feature Branch**: `066-formal-memory-state-machine`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Open the tranche immediately after `065-promotion-gate-primitives` by mapping bounded admission decisions into an explicit internal memory state model, without yet rewriting retrieval behavior.

## User Scenarios & Testing

### User Story 1 - Admission Outcomes Map To Explicit States (Priority: P1)

As a maintainer, I want promotion outcomes to land in explicit internal states such as `draft`, `validated`, or `invalidated`, so admission is modeled directly rather than inferred from mixed metadata and lifecycle fields.

**Independent Test**: Promote and reject candidates through the canonical path and verify the resulting stored records map to explicit internal states.

### User Story 2 - Legacy Lifecycle Statuses Stay Compatible (Priority: P1)

As an integrator, I want existing lifecycle-oriented behavior to remain compatible while richer internal states are introduced, so the state tranche hardens internals without breaking current runtime contracts.

**Independent Test**: Re-run existing lifecycle, hygiene, and retrieval tests and verify current public payloads remain stable.

### User Story 3 - Later Retrieval Work Can Read States Cleanly (Priority: P1)

As a maintainer, I want the new state model to be queryable through stable internals, so a later retrieval tranche can consume it without another storage redesign.

**Independent Test**: Verify runtime/storage helpers can inspect stateful records without exposing new public payload shape yet.

## Requirements

- **FR-001**: The runtime MUST define an explicit internal admission-aware state taxonomy.
- **FR-002**: Canonical ingest and promotion decisions MUST map into the new state model.
- **FR-003**: Existing lifecycle-oriented statuses MUST remain backward-compatible during this tranche.
- **FR-004**: Public retrieval and tool payload shapes MUST remain stable.
- **FR-005**: This tranche MUST NOT rewrite ranking, routing, or retrieval-stage behavior.
- **FR-006**: This tranche SHOULD leave clear seams for later retrieval and policy work to consume state directly.

## Success Criteria

- **SC-001**: Admission decisions from `065` are represented as explicit internal states.
- **SC-002**: Existing runtime behavior remains green while the richer state model lands internally.
- **SC-003**: Later retrieval work can depend on a real state model instead of reconstructing admission intent from metadata.
