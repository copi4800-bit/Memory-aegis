# Feature Specification: Weaver Auto Linking

**Feature Branch**: `012-weaver-auto-linking`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Continue Weaver by making Aegis automatically create safe local relations during ingest using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto Link Same-Subject Memories On Ingest (Priority: P1)

As an Aegis maintainer, I want same-scope memories with the same subject to auto-link on ingest so the Weaver layer gains useful structure without manual relation entry every time.

**Why this priority**: The explicit Weaver surface already exists. The next practical step is safe automatic relation creation with a narrow rule.

**Independent Test**: Ingest two memories in the same scope with the same subject and verify an explicit `same_subject` link appears automatically.

**Acceptance Scenarios**:

1. **Given** an existing memory with subject `alpha.topic`, **When** I ingest another memory in the same scope with subject `alpha.topic`, **Then** Aegis creates a `same_subject` relation automatically.
2. **Given** memories in different scopes or without a subject, **When** I ingest them, **Then** Aegis does not auto-link them.

### User Story 2 - Rebuild Missing Same-Subject Links (Priority: P1)

As a maintainer, I want the Python rebuild flow to backfill missing same-subject links so older datasets can gain Weaver structure without re-ingesting all memories.

**Why this priority**: Existing databases predate the new write-path behavior.

**Independent Test**: Seed same-subject memories without links, run rebuild, and verify `same_subject` links are created.

**Acceptance Scenarios**:

1. **Given** active same-subject memories in one scope and no explicit links, **When** I run rebuild, **Then** Aegis backfills bounded `same_subject` links.

### User Story 3 - Document Auto-Link Behavior (Priority: P2)

As a contributor, I want the docs and feature artifacts to explain the auto-link rule so the behavior is predictable and clearly scoped.

**Why this priority**: Automatic relation creation must stay explainable and narrowly bounded.

**Independent Test**: Review docs and confirm the rule is documented as same-subject, same-scope, bounded, and local-first.

### Edge Cases

- Duplicate auto-links must not create multiple identical link rows.
- Subject-less memories must not auto-link.
- Auto-linking must stay bounded and must not flood large scopes with unbounded pair generation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST auto-create explicit `same_subject` links when a new active memory is stored with a non-empty subject and same-scope active peers already exist.
- **FR-002**: Auto-linking MUST stay within the same `scope_type` and `scope_id`.
- **FR-003**: Auto-linking MUST be bounded to a small number of peers per ingest.
- **FR-004**: The Python rebuild flow MUST backfill missing `same_subject` links for existing same-scope active memories.
- **FR-005**: Duplicate links MUST be absorbed by the existing upsert behavior rather than creating ambiguous rows.
- **FR-006**: Repo docs and feature artifacts MUST describe the auto-link rule.

### Key Entities

- **Auto Link Rule**: The narrow rule that creates `same_subject` links for same-scope active memories with the same non-empty subject.
- **Backfill Rebuild**: The rebuild path that adds missing same-subject links for existing memories.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ingesting same-subject memories in one scope produces usable explicit links without manual relation creation.
- **SC-002**: Running rebuild backfills missing same-subject links for existing local data.
- **SC-003**: The rule remains narrow, bounded, and documented.
