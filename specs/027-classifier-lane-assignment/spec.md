# Feature Specification: Classifier Lane Assignment

**Feature Branch**: `027-classifier-lane-assignment`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the next Tranche A slice by inferring a memory lane when the caller omits type using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Infer A Lane When Type Is Omitted (Priority: P1)

As an Aegis maintainer, I want ingest to infer a stable memory lane when callers omit `type` so the engine can store reasonable defaults without requiring every host to choose a lane manually.

**Why this priority**: Tranche A needs an explicit Classifier slice, and lane assignment is the smallest useful contract it can own.

**Independent Test**: Store memories with `type=None` and verify Aegis assigns deterministic lanes for representative working, procedural, and semantic-style inputs.

**Acceptance Scenarios**:

1. **Given** a caller omits `type` and provides session-scoped temporary note content, **When** the memory is ingested, **Then** Aegis classifies it into `working`.
2. **Given** a caller omits `type` and provides instruction-like content, **When** the memory is ingested, **Then** Aegis classifies it into `procedural`.
3. **Given** a caller omits `type` and provides fact-like content, **When** the memory is ingested, **Then** Aegis classifies it into `semantic`.

### User Story 2 - Preserve Explicit Caller Lane (Priority: P1)

As an integrator, I want explicit `type` values to win over classifier inference so hosts keep control when they already know the correct lane.

**Why this priority**: The classifier should raise the floor for omitted inputs, not override deliberate host behavior.

**Independent Test**: Store a memory with explicit `type` and verify the classifier does not alter it.

**Acceptance Scenarios**:

1. **Given** a caller provides an explicit lane, **When** the memory is ingested, **Then** Aegis persists that exact lane unchanged.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this classifier feature so the third Tranche A slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this implementation slice must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `027-classifier-lane-assignment` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the classifier feature is active, **When** I run the prerequisite check, **Then** it resolves to `027-classifier-lane-assignment`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST infer a lane when `type` is omitted or `None`.
- **FR-002**: Lane inference MUST remain deterministic and local-only.
- **FR-003**: Explicit caller-provided `type` values MUST NOT be overridden by classifier inference.
- **FR-004**: Classifier inference MUST remain conservative and MUST bias to `episodic` when heuristics are weak.
- **FR-005**: Python integration tests MUST cover inferred `working`, `procedural`, and `semantic` cases plus explicit lane preservation.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `027-classifier-lane-assignment` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Inferred Lane**: The memory type chosen by the classifier when the caller omits `type`.
- **Explicit Lane**: A caller-supplied `type` value that must remain authoritative.
- **Classifier Slice**: The bounded Tranche A implementation that assigns memory lanes conservatively.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested omitted-type inputs persist deterministic inferred lanes.
- **SC-002**: Explicit caller-provided lanes remain unchanged after ingest.
- **SC-003**: The prerequisite check resolves to `027-classifier-lane-assignment` with its `tasks.md` artifact present.
