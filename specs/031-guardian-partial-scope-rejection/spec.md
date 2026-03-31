# Feature Specification: Guardian Partial Scope Rejection

**Feature Branch**: `031-guardian-partial-scope-rejection`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the next Guardian slice by rejecting partial retrieval scopes instead of silently accepting ambiguous boundary input using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject Partial Retrieval Scope Inputs (Priority: P1)

As an Aegis maintainer, I want retrieval surfaces to reject partial scope inputs so hosts cannot accidentally issue ambiguous scope-boundary queries.

**Why this priority**: Guardian should enforce clear scope boundaries, and a retrieval request with only `scope_type` or only `scope_id` is an ambiguous contract.

**Independent Test**: Call search and context-pack surfaces with only one scope field and verify they fail clearly.

**Acceptance Scenarios**:

1. **Given** a host provides `scope_type` without `scope_id`, **When** it calls a retrieval surface, **Then** Aegis raises a clear validation error.
2. **Given** a host provides `scope_id` without `scope_type`, **When** it calls a retrieval surface, **Then** Aegis raises a clear validation error.

### User Story 2 - Preserve Valid Scope Defaults (Priority: P1)

As an integrator, I want retrieval to keep working when both scope fields are omitted or when both are provided, so Guardian hardening does not break valid host behavior.

**Why this priority**: The boundary contract should get stricter without breaking stable valid usage.

**Independent Test**: Call retrieval with both scope fields omitted and with both provided and verify the surfaces still work.

**Acceptance Scenarios**:

1. **Given** a host omits both scope fields, **When** it calls a retrieval surface, **Then** Aegis uses the stable default scope pair.
2. **Given** a host provides both scope fields, **When** it calls a retrieval surface, **Then** Aegis performs the retrieval normally.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this Guardian feature so the boundary-hardening slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this contract change must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `031-guardian-partial-scope-rejection` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the guardian feature is active, **When** I run the prerequisite check, **Then** it resolves to `031-guardian-partial-scope-rejection`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Retrieval surfaces MUST reject requests that provide only one of `scope_type` or `scope_id`.
- **FR-002**: Retrieval surfaces MUST continue to accept requests that provide both scope fields.
- **FR-003**: Retrieval surfaces MUST continue to accept requests that omit both scope fields by using the stable default scope pair.
- **FR-004**: Guardian validation errors MUST be explicit and deterministic.
- **FR-005**: Python integration tests MUST cover partial-scope rejection and valid-scope acceptance.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `031-guardian-partial-scope-rejection` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Partial Scope Input**: A retrieval request that supplies only `scope_type` or only `scope_id`.
- **Scope Pair Contract**: The rule that retrieval either receives a full scope pair or no scope pair.
- **Guardian Validation Slice**: The bounded Guardian implementation that rejects ambiguous retrieval boundaries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested partial-scope retrieval requests fail with clear validation errors.
- **SC-002**: Tested valid scope-pair and no-scope retrieval requests continue to work.
- **SC-003**: The prerequisite check resolves to `031-guardian-partial-scope-rejection` with its `tasks.md` artifact present.
