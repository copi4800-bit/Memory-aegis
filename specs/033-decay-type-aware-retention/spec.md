# Feature Specification: Decay Type-Aware Retention

**Feature Branch**: `033-decay-type-aware-retention`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the first Decay Beast slice by applying type-aware retention half-lives during maintenance using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Decay Different Memory Types At Different Rates (Priority: P1)

As an Aegis maintainer, I want maintenance decay to respect memory type so working memories cool faster than durable semantic or procedural memory.

**Why this priority**: Tranche C should improve lifecycle behavior meaningfully, and type-aware decay is the smallest useful retention policy slice.

**Independent Test**: Age different memory types by the same duration, run maintenance, and verify their activation scores decay at different rates.

**Acceptance Scenarios**:

1. **Given** a working memory and a semantic memory are equally old, **When** maintenance runs, **Then** the working memory decays more aggressively.
2. **Given** an episodic memory is equally old, **When** maintenance runs, **Then** it continues to use the baseline decay behavior.

### User Story 2 - Preserve Explicit Maintenance Overrides (Priority: P1)

As an operator, I want an explicit `half_life_days` override to remain available so maintenance can still be run with one forced half-life when needed.

**Why this priority**: Type-aware retention should become the default policy, not remove operator control.

**Independent Test**: Run maintenance with an explicit `half_life_days` override and verify that memories use the same override instead of per-type defaults.

**Acceptance Scenarios**:

1. **Given** maintenance is invoked with an explicit half-life override, **When** decay runs, **Then** all active memories use that override consistently.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this decay feature so the first Tranche C slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this lifecycle change must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `033-decay-type-aware-retention` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the decay feature is active, **When** I run the prerequisite check, **Then** it resolves to `033-decay-type-aware-retention`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Maintenance decay MUST support type-aware half-lives by default.
- **FR-002**: `working` memories MUST decay faster than `episodic` by default.
- **FR-003**: `semantic` memories MUST decay slower than `episodic` by default.
- **FR-004**: An explicit maintenance `half_life_days` override MUST continue to apply uniformly when supplied.
- **FR-005**: Hygiene tests MUST cover type-aware default decay and explicit override behavior.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `033-decay-type-aware-retention` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Type-Aware Half-Life**: A default decay period associated with a memory type.
- **Retention Override**: An explicit maintenance parameter that replaces type-aware defaults for one run.
- **Decay Slice**: The bounded Tranche C implementation that differentiates retention by lane.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested memory types decay at different default rates.
- **SC-002**: Tested explicit maintenance override still applies uniformly.
- **SC-003**: The prerequisite check resolves to `033-decay-type-aware-retention` with its `tasks.md` artifact present.
