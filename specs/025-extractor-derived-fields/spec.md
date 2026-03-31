# Feature Specification: Extractor Derived Fields

**Feature Branch**: `025-extractor-derived-fields`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the first real Tranche A slice by teaching Extractor Beast to derive stable subject and summary fields during ingest using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Derive Missing Subject And Summary (Priority: P1)

As an Aegis maintainer, I want ingest to derive a stable `subject` and `summary` when callers omit them so stored memories are more retrievable without requiring manual metadata every time.

**Why this priority**: Tranche A starts with Extractor Beast, and derived fields improve retrieval quality at the source.

**Independent Test**: Store a memory without `subject` or `summary` and verify the persisted memory receives deterministic extracted values.

**Acceptance Scenarios**:

1. **Given** a caller omits `subject` and `summary`, **When** the memory is ingested, **Then** Aegis stores derived values instead of leaving both fields empty.
2. **Given** the same content is ingested again in a fresh runtime, **When** derived fields are calculated, **Then** the extracted values are deterministic for that input.

### User Story 2 - Preserve Explicit Caller Metadata (Priority: P1)

As an integrator, I want explicit `subject` and `summary` values to win over extractor defaults so the ingest path improves missing metadata without breaking current callers.

**Why this priority**: The extractor should raise the floor, not rewrite deliberate host intent.

**Independent Test**: Store a memory with explicit `subject` and `summary` and verify the extractor does not override them.

**Acceptance Scenarios**:

1. **Given** a caller provides explicit `subject` and `summary`, **When** the memory is ingested, **Then** Aegis preserves those values exactly.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this extractor feature so the first implementation slice of Tranche A remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so the code change needs repo-tracked feature artifacts.

**Independent Test**: Run the prerequisite check and confirm it resolves to `025-extractor-derived-fields` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the extractor feature is active, **When** I run the prerequisite check, **Then** it resolves to `025-extractor-derived-fields`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST derive a stable fallback `subject` during ingest when the caller omits it.
- **FR-002**: Aegis MUST derive a stable fallback `summary` during ingest when the caller omits it.
- **FR-003**: Explicit caller-supplied `subject` and `summary` MUST NOT be overridden by fallback extraction.
- **FR-004**: The extractor implementation MUST stay inside the existing `memory` module and MUST NOT introduce a new public subsystem.
- **FR-005**: Python integration tests MUST cover both derived-field behavior and explicit-field preservation.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `025-extractor-derived-fields` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Derived Subject**: A fallback subject key synthesized from content when no explicit subject is provided.
- **Derived Summary**: A short fallback summary synthesized from content when no explicit summary is provided.
- **Extractor Slice**: The first bounded implementation of Extractor Beast in Tranche A.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Memories ingested without explicit `subject` and `summary` persist non-empty derived values.
- **SC-002**: Explicit caller-provided `subject` and `summary` remain unchanged after ingest.
- **SC-003**: The prerequisite check resolves to `025-extractor-derived-fields` with its `tasks.md` artifact present.
