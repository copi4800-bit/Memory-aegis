# Feature Specification: Navigator Lexical Subject Gating

**Feature Branch**: `032-navigator-lexical-subject-gating`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the next Navigator slice by allowing subject expansion to seed only from lexical hits using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prevent Subject Expansion Cascades (Priority: P1)

As an Aegis maintainer, I want subject expansion to seed only from lexical hits so link and entity expansions cannot recursively create broader subject cascades.

**Why this priority**: Navigator should stay bounded and lexical-led, not let secondary expansions recursively widen recall.

**Independent Test**: Create a case where an entity-expanded result has a different subject and verify that its subject does not seed further subject expansion.

**Acceptance Scenarios**:

1. **Given** a lexical hit produces an entity-expanded neighbor with a different subject, **When** a context pack is built, **Then** Aegis does not add subject-expansion results based only on that expanded neighbor's subject.

### User Story 2 - Preserve Lexical-Led Subject Expansion (Priority: P1)

As an integrator, I want subject expansion from lexical hits to keep working so the tighter gate does not remove the intended lexical-first relationship recall.

**Why this priority**: The slice should narrow expansion seeding, not disable useful lexical-led subject recall.

**Independent Test**: Build a context pack from a lexical hit that has same-subject peers and verify subject expansion still appears.

**Acceptance Scenarios**:

1. **Given** a lexical hit has same-subject neighbors, **When** a context pack is built, **Then** subject expansion still occurs from that lexical subject.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this navigator feature so the lexical-subject gating slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this retrieval contract change must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `032-navigator-lexical-subject-gating` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the navigator feature is active, **When** I run the prerequisite check, **Then** it resolves to `032-navigator-lexical-subject-gating`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Subject expansion MUST seed only from lexical results.
- **FR-002**: Link and entity expansion results MUST NOT introduce new subject-expansion seed subjects.
- **FR-003**: Lexical-led subject expansion MUST continue to work for same-subject neighbors.
- **FR-004**: The change MUST remain local and deterministic.
- **FR-005**: Python integration tests MUST cover lexical subject expansion plus prevention of expansion-seeded subject cascades.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `032-navigator-lexical-subject-gating` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Lexical Seed Subject**: A subject belonging to a direct lexical hit.
- **Expansion Cascade**: A broader expansion caused by using a non-lexical expansion result as a new subject-expansion seed.
- **Navigator Gating Slice**: The bounded Tranche B change that restricts subject expansion seeds to lexical hits.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested non-lexical expansion subjects do not trigger subject-expansion cascades.
- **SC-002**: Tested lexical same-subject expansion still works.
- **SC-003**: The prerequisite check resolves to `032-navigator-lexical-subject-gating` with its `tasks.md` artifact present.
