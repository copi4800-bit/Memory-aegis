# Feature Specification: Navigator Stage Budgets

**Feature Branch**: `029-navigator-stage-budgets`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the first real Tranche B slice by bounding navigator expansion stages during retrieval using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep Expansion Stages Bounded (Priority: P1)

As an Aegis maintainer, I want explicit per-stage budgets for retrieval expansion so link, entity, and subject expansion cannot crowd out lexical recall.

**Why this priority**: Tranche B starts with Navigator discipline, and the highest-value move is to make expansion bounded by contract instead of only by the overall limit.

**Independent Test**: Create enough link, entity, and subject neighbors to exceed a stage budget and verify the context pack keeps bounded counts per stage.

**Acceptance Scenarios**:

1. **Given** many same-scope relation neighbors exist, **When** I build a context pack, **Then** Aegis includes at most the configured number of results from each expansion stage.
2. **Given** lexical hits exist, **When** expansion runs, **Then** lexical results remain present and are not displaced entirely by one expansion mode.

### User Story 2 - Surface Stage Counts For Explainability (Priority: P1)

As an integrator, I want context packs to report stage counts so bounded navigation is visible instead of hidden inside retrieval internals.

**Why this priority**: If stage budgets are enforced but invisible, operators cannot verify or reason about expansion balance.

**Independent Test**: Build a context pack and verify it includes per-stage counts for lexical and expansion stages.

**Acceptance Scenarios**:

1. **Given** a context pack is built, **When** I inspect the payload, **Then** I can see counts for lexical, link, multi-hop, entity, and subject stages.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this navigator feature so the first Tranche B implementation slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this retrieval change must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `029-navigator-stage-budgets` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the navigator feature is active, **When** I run the prerequisite check, **Then** it resolves to `029-navigator-stage-budgets`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST enforce bounded budgets for each retrieval expansion stage after lexical recall.
- **FR-002**: Stage budgets MUST remain local and deterministic.
- **FR-003**: Lexical results MUST remain first-class and MUST NOT be displaced entirely by expansion stages.
- **FR-004**: `memory_context_pack` MUST surface stage counts for lexical and expansion stages.
- **FR-005**: Python integration tests MUST cover bounded expansion behavior and context-pack stage counts.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `029-navigator-stage-budgets` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Stage Budget**: The maximum number of results a retrieval expansion stage may contribute to a context pack.
- **Stage Count**: The number of results actually contributed by each retrieval stage.
- **Navigator Slice**: The bounded Tranche B implementation that disciplines retrieval expansion stages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested context packs show bounded per-stage expansion counts.
- **SC-002**: Context packs surface stage counts for lexical and expansion stages.
- **SC-003**: The prerequisite check resolves to `029-navigator-stage-budgets` with its `tasks.md` artifact present.
