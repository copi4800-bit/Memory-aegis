# Feature Specification: Scorer Write-Time Salience

**Feature Branch**: `028-scorer-write-time-salience`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the final Tranche A slice by assigning bounded write-time confidence and activation scores during ingest using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assign Bounded Write-Time Scores When Omitted (Priority: P1)

As an Aegis maintainer, I want ingest to assign bounded `confidence` and `activation_score` values when callers omit them so newly stored memories carry a little salience signal without needing post-hoc reinforcement first.

**Why this priority**: Tranche A ends with Scorer Beast, and write-time signal is already part of retrieval ordering.

**Independent Test**: Store memories without explicit score fields and verify ingest assigns deterministic, bounded values that vary by lane and simple content cues.

**Acceptance Scenarios**:

1. **Given** a caller omits score fields for instruction-like content, **When** the memory is ingested, **Then** Aegis stores non-default bounded score values.
2. **Given** a caller omits score fields for weaker note content, **When** the memory is ingested, **Then** Aegis stores a lower or baseline score than stronger instruction-like content.

### User Story 2 - Preserve Explicit Caller Scores (Priority: P1)

As an integrator, I want explicit `confidence` and `activation_score` values to remain authoritative so hosts can still inject deliberate scores when they know better.

**Why this priority**: The scorer should fill gaps, not override explicit host intent.

**Independent Test**: Store a memory with explicit score values and verify ingest preserves them unchanged.

**Acceptance Scenarios**:

1. **Given** a caller provides explicit `confidence` and `activation_score`, **When** the memory is ingested, **Then** Aegis persists those exact values.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this scorer feature so the final Tranche A implementation slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this scoring change must remain feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `028-scorer-write-time-salience` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the scorer feature is active, **When** I run the prerequisite check, **Then** it resolves to `028-scorer-write-time-salience`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST assign bounded write-time `confidence` and `activation_score` values when callers omit them.
- **FR-002**: Write-time scoring MUST remain deterministic and local-only.
- **FR-003**: Explicit caller-provided `confidence` and `activation_score` values MUST NOT be overridden.
- **FR-004**: Write-time scoring MUST remain conservative and explainable, not a hidden ranking model.
- **FR-005**: Python integration tests MUST cover inferred scoring and explicit score preservation.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `028-scorer-write-time-salience` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Write-Time Score**: The initial `confidence` and `activation_score` values attached during ingest.
- **Explicit Score Override**: Caller-provided scores that remain authoritative.
- **Scorer Slice**: The bounded Tranche A implementation that assigns initial salience conservatively.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested omitted-score inputs persist deterministic bounded score values.
- **SC-002**: Explicit caller-provided score values remain unchanged after ingest.
- **SC-003**: The prerequisite check resolves to `028-scorer-write-time-salience` with its `tasks.md` artifact present.
