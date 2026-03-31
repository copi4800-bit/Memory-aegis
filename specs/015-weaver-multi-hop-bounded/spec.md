# Feature Specification: Weaver Multi-Hop Bounded

**Feature Branch**: `015-weaver-multi-hop-bounded`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add bounded multi-hop Weaver expansion using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add One Bounded Extra Link Hop (Priority: P1)

As a host integrator, I want Aegis to follow one extra explicit link hop after lexical seed recall so context packs can include a slightly wider but still explainable neighborhood.

**Independent Test**: Seed `A -> B -> C` explicit links, query `A`, and verify `C` may appear only as a bounded multi-hop expansion with explicit explanation fields.

### User Story 2 - Preserve Lexical-First Discipline (Priority: P1)

As a maintainer, I want multi-hop expansion to stay behind lexical seed recall and a strict hop budget so Aegis does not turn into uncontrolled graph traversal.

**Independent Test**: Confirm multi-hop results never appear without lexical seed hits and that returned payloads state hop count.

### Requirements *(mandatory)*

- **FR-001**: `memory_context_pack` MUST remain lexical-first.
- **FR-002**: Explicit link traversal MAY follow at most one extra hop beyond first-hop link expansion.
- **FR-003**: Multi-hop results MUST expose hop count and link explanation fields.
- **FR-004**: Multi-hop traversal MUST remain scope-safe and budget-bounded.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: Context-pack can include bounded multi-hop link results with explicit explanation payloads.
- **SC-002**: Lexical-first behavior remains intact and test-covered.
