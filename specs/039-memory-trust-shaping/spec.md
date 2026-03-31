# Feature Specification: Memory Trust Shaping

**Feature Branch**: `039-memory-trust-shaping`
**Status**: Implemented
**Input**: Roadmap slice `039-memory-trust-shaping` from `aegis_py/ARCHITECTURE_BEAST_MAP.md`

## User Scenarios & Testing

### User Story 1 - Clear Trust Labels (Priority: P1)
As a non-technical user, I want recalled memories to indicate whether they are strong, weak, uncertain, or conflicting so I know what to trust.

**Acceptance Scenarios**:
1. **Given** a lexical fact match with good confidence and no conflict, **When** I inspect search output, **Then** it is labeled `strong`.
2. **Given** a result is relationship-expanded or low-signal, **When** I inspect search output, **Then** it is labeled `uncertain` or `weak`.
3. **Given** a result is tied to an open conflict, **When** I inspect search output, **Then** it is labeled `conflicting`.

### User Story 2 - Trust Visible In Human Surface (Priority: P1)
As a user of the simple recall surface, I want trust expressed in plain language so I can understand caveats without reading internal fields.

**Acceptance Scenarios**:
1. **Given** the simple `memory_recall` action returns a conflicting memory, **When** it renders the response, **Then** it includes a human-readable trust cue.
2. **Given** the simple `memory_recall` action returns a strong memory, **When** it renders the response, **Then** it does not overwhelm me with jargon.

## Requirements

- **FR-001**: Retrieval results MUST expose a trust state with the values `strong`, `weak`, `uncertain`, or `conflicting`.
- **FR-002**: Retrieval results MUST expose a concise trust reason suitable for debugging and user-surface adaptation.
- **FR-003**: Public serialized search payloads and context-pack results MUST include trust state and trust reason.
- **FR-004**: The simplified `memory_recall` surface MUST render trust cues in human-readable form.
- **FR-005**: The feature MUST preserve the current six-module runtime model and MUST NOT introduce a separate trust subsystem.

## Success Criteria

- **SC-001**: Search and context-pack payloads expose trust metadata for every returned result.
- **SC-002**: Integration tests cover at least one `strong`, one `uncertain`, and one `conflicting` retrieval case.
- **SC-003**: The simple recall surface exposes trust cues without surfacing raw implementation jargon.
