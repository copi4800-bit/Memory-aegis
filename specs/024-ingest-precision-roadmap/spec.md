# Feature Specification: Ingest Precision Roadmap

**Feature Branch**: `024-ingest-precision-roadmap`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Open the first execution feature for Tranche A so Extractor, Normalizer, Classifier, and Scorer can be deepened in a bounded order using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonical Order For Tranche A (Priority: P1)

As an Aegis maintainer, I want a concrete execution order for Tranche A so ingest precision work starts with the highest-leverage steps and avoids opening all four beasts at once.

**Why this priority**: Tranche A has the best leverage on future retrieval quality, but it still needs a disciplined order to stay compact.

**Independent Test**: Review the roadmap and verify that Extractor, Normalizer, Classifier, and Scorer are sequenced with clear rationale.

**Acceptance Scenarios**:

1. **Given** a contributor wants to start ingest precision work, **When** they read the roadmap, **Then** they know which beast should be deepened first and what follows next.
2. **Given** a maintainer wants to keep changes bounded, **When** they use the roadmap, **Then** they can open one thin execution slice at a time instead of a broad ingest rewrite.

### User Story 2 - Define Deliverables And Gates Per Ingest Beast (Priority: P1)

As an Aegis architect, I want explicit deliverables and entry gates for each Tranche A beast so later implementation features have a stable contract.

**Why this priority**: Without per-beast deliverables, ingest work will drift into vague cleanup rather than measurable engine improvement.

**Independent Test**: Review the roadmap and confirm each Tranche A beast has deliverables, entry gates, and a bounded module touchpoint.

**Acceptance Scenarios**:

1. **Given** a contributor wants to implement `Extractor Beast`, **When** they inspect the roadmap, **Then** they find a narrow target such as subject/summary extraction or candidate shaping.
2. **Given** a maintainer wants to defer `Scorer Beast`, **When** they inspect the roadmap, **Then** they can point to its gate and explain why it has not opened yet.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this ingest-precision roadmap so the next real implementation feature starts from a clean coordination base.

**Why this priority**: The user asked to keep advancing through SPD/GSD plus Spec Kit, so the first tranche needs its own tracked feature.

**Independent Test**: Run the prerequisite check and confirm it resolves to `024-ingest-precision-roadmap` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the ingest roadmap feature is active, **When** I run the prerequisite check, **Then** it resolves to `024-ingest-precision-roadmap`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repo MUST define a concrete execution order for `Extractor Beast`, `Normalizer Beast`, `Classifier Beast`, and `Scorer Beast`.
- **FR-002**: The roadmap MUST define bounded deliverables for each Tranche A beast.
- **FR-003**: The roadmap MUST define at least one entry gate for each Tranche A beast.
- **FR-004**: The roadmap MUST keep Tranche A inside the existing `memory` module by default and MUST NOT imply a broad ingest subsystem split.
- **FR-005**: The canonical beast architecture document MUST record the Tranche A sub-order in repo-tracked form.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `024-ingest-precision-roadmap` feature.
- **FR-007**: Validation evidence MUST show that the canonical prerequisite workflow resolves to the `024` feature.

### Key Entities

- **Ingest Step**: A thin execution slice inside Tranche A that deepens one beast or one closely related pair.
- **Bounded Deliverable**: A concrete improvement such as subject extraction, canonical normalization, lane assignment, or write-time salience shaping.
- **Opening Gate**: A measurable reason to start a given ingest step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four Tranche A beasts are sequenced in a clear execution order.
- **SC-002**: Each beast has explicit deliverables and entry gates.
- **SC-003**: The prerequisite check resolves to `024-ingest-precision-roadmap` with its `tasks.md` artifact present.
