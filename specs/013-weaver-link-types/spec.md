# Feature Specification: Weaver Link Types

**Feature Branch**: `013-weaver-link-types`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Continue Weaver with another narrow auto-link rule using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto Link Procedural And Semantic Memories (Priority: P1)

As an Aegis maintainer, I want procedural and semantic memories with the same subject in the same scope to auto-link so procedures gain nearby factual context.

**Why this priority**: It strengthens Weaver without opening broad semantic guessing.

**Independent Test**: Ingest procedural and semantic memories with the same subject in the same scope and verify an explicit typed link is created.

### User Story 2 - Backfill Procedural-Semantic Links On Rebuild (Priority: P1)

As a maintainer, I want rebuild to backfill missing procedural-semantic links so older data benefits from the new structure.

**Why this priority**: Existing data predates the new rule.

**Independent Test**: Seed same-subject procedural/semantic memories, remove typed links, run rebuild, and verify links are restored.

### User Story 3 - Document Typed Auto-Linking (Priority: P2)

As a contributor, I want the docs to explain typed auto-link rules so the behavior remains predictable and bounded.

**Why this priority**: Automatic linking must stay explainable.

### Edge Cases

- Only same-scope memories may auto-link.
- Subject-less memories must not auto-link.
- Only procedural/semantic pairing should produce the new typed relation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST auto-create explicit typed links between same-scope procedural and semantic memories with the same non-empty subject.
- **FR-002**: The typed rule MUST remain bounded and local-only.
- **FR-003**: Rebuild MUST backfill missing typed links for existing active same-subject procedural/semantic pairs.
- **FR-004**: Existing `same_subject` behavior MUST remain intact.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Procedural and semantic memories with the same subject auto-link with an explicit typed relation.
- **SC-002**: Rebuild restores missing typed relations for older data.
