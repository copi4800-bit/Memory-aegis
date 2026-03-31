# Feature Specification: Entity Structure Lite

**Feature Branch**: `017-entity-structure-lite`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add lightweight entity structure to Aegis using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Lightweight Entity Tags On Ingest (Priority: P1)

As a maintainer, I want Aegis to derive lightweight entity tags on ingest so memories carry a small amount of structured identity beyond raw text.

**Independent Test**: Store memories containing stable entity-like terms and verify metadata contains normalized entity tags.

### User Story 2 - Expand Context By Shared Entities (Priority: P1)

As a host integrator, I want context-pack to use shared entity tags as a bounded expansion step so related memories can be found even when they do not share the same subject.

**Independent Test**: Seed lexical hit plus a different-subject memory sharing an entity tag and verify the second memory appears as `entity_expansion`.

### Requirements *(mandatory)*

- **FR-001**: Aegis MUST extract lightweight normalized entity tags on ingest and store them in memory metadata.
- **FR-002**: Entity extraction MUST stay local-only and heuristic, not model-dependent.
- **FR-003**: `memory_context_pack` MAY use shared entity tags as a bounded expansion step after explicit link expansion.
- **FR-004**: Entity expansion MUST remain scope-safe and explainable.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: New memories contain lightweight entity tags in metadata.
- **SC-002**: Context-pack can surface bounded `entity_expansion` results when a lexical seed shares entity tags with nearby memories.
