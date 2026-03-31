# Feature Specification: Weaver Link Explanations

**Feature Branch**: `014-weaver-link-explanations`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Continue Weaver by surfacing richer link explanations in context-pack and neighbor payloads using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explain Link-Driven Expansions (Priority: P1)

As a host integrator, I want context-pack results to state which explicit link caused an expansion so the model can see why a memory was pulled in.

**Independent Test**: Build a context pack that expands through an explicit link and verify the result includes link type, seed memory ID, and link metadata.

### User Story 2 - Preserve Explainability In Public Payloads (Priority: P1)

As a maintainer, I want search serialization to preserve link explanation fields so Python-owned result shapes stay audit-friendly.

**Independent Test**: Serialize expanded results and verify the new link explanation fields are present for link-driven expansions and absent for pure lexical hits.

### User Story 3 - Document Link Explanation Behavior (Priority: P2)

As a contributor, I want docs and workflow artifacts updated so the richer explanation model is discoverable.

### Requirements *(mandatory)*

- **FR-001**: Link-driven context-pack results MUST include `relation_via_link_type`.
- **FR-002**: Link-driven context-pack results MUST include the seed memory ID that caused the expansion.
- **FR-003**: Link-driven context-pack results MUST include link metadata when available.
- **FR-004**: Lexical and subject-only expansions MUST keep stable payloads and should not fake link fields.
- **FR-005**: Docs and feature artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: Host models can inspect which explicit link caused a link expansion.
- **SC-002**: Python-owned serialized payloads remain stable and more informative.
