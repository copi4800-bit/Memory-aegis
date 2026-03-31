# Feature Specification: Normalizer Subject Canonicalization

**Feature Branch**: `026-normalizer-subject-canonicalization`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the next Tranche A slice by canonicalizing subject keys during ingest using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonicalize Subject Keys During Ingest (Priority: P1)

As an Aegis maintainer, I want ingest to canonicalize subject keys so retrieval, linking, and hygiene see one stable subject form instead of punctuation and casing variants.

**Why this priority**: Tranche A now has fallback extraction, and the next highest-leverage move is to collapse subject drift at write time.

**Independent Test**: Store memories with messy subject formatting and verify persisted subjects are normalized into a stable dotted lowercase form.

**Acceptance Scenarios**:

1. **Given** a caller provides a mixed-case or punctuation-heavy subject, **When** the memory is ingested, **Then** Aegis stores a canonical subject key.
2. **Given** a subject is derived by the extractor, **When** ingest normalizes it, **Then** the persisted value uses the same canonical form as explicit subjects.

### User Story 2 - Preserve Explicit Null Subject Semantics (Priority: P1)

As a maintainer, I want explicit `None` subject values to remain unlabeled so taxonomy cleanup and related hygiene flows keep working.

**Why this priority**: The normalizer should reduce subject drift, not erase the existing unlabeled-memory contract.

**Independent Test**: Store a memory with explicit `subject=None` and verify the stored memory remains unlabeled.

**Acceptance Scenarios**:

1. **Given** a caller explicitly passes `subject=None`, **When** the memory is ingested, **Then** Aegis keeps the subject unset instead of deriving or normalizing a replacement.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this normalizer feature so the second real Tranche A slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this code change must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `026-normalizer-subject-canonicalization` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the normalizer feature is active, **When** I run the prerequisite check, **Then** it resolves to `026-normalizer-subject-canonicalization`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST canonicalize non-empty subject strings during ingest into a stable lowercase dotted format.
- **FR-002**: Subject canonicalization MUST collapse punctuation and whitespace variants into the same canonical subject key when possible.
- **FR-003**: Explicit `subject=None` MUST remain `None` and MUST NOT be replaced by a canonicalized fallback.
- **FR-004**: Derived subjects from the extractor MUST pass through the same normalizer path as explicit subject strings.
- **FR-005**: Python integration tests MUST cover explicit subject canonicalization, derived subject canonicalization, and explicit null preservation.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `026-normalizer-subject-canonicalization` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Canonical Subject**: A normalized dotted lowercase subject key suitable for retrieval, links, and hygiene.
- **Subject Drift**: Divergence caused by punctuation, case, or spacing variants that should collapse into one canonical subject.
- **Normalizer Slice**: The bounded Tranche A implementation that canonicalizes subject keys at write time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Persisted subject strings use a canonical dotted lowercase form for tested variant inputs.
- **SC-002**: Explicit `subject=None` remains unlabeled after ingest.
- **SC-003**: The prerequisite check resolves to `026-normalizer-subject-canonicalization` with its `tasks.md` artifact present.
