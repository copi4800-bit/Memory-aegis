# Feature Specification: Guardian Scope Contracts

**Feature Branch**: `030-guardian-scope-contracts`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the first Guardian slice by making retrieval scope contracts explicit in reasoning and context-pack payloads using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Make Global Fallback Explicit (Priority: P1)

As an Aegis maintainer, I want retrieval reasons to mark global fallback explicitly so exact-scope results and global fallback results are not conflated.

**Why this priority**: Guardian Beast should make scope boundaries visible, not implicit.

**Independent Test**: Search with `include_global=True` and verify global fallback results carry an explicit `global_fallback` reason.

**Acceptance Scenarios**:

1. **Given** a project-scoped query with global fallback enabled, **When** a global memory appears in results, **Then** its reasons include `global_fallback`.

### User Story 2 - Surface Boundary Contract In Context Packs (Priority: P1)

As an integrator, I want context packs to describe their boundary contract so hosts can inspect whether retrieval was exact-scope only or allowed global fallback.

**Why this priority**: Context packs are the main host-ready retrieval payload, so Guardian signals should be visible there.

**Independent Test**: Build a context pack and verify it includes a `boundary` section describing scope lock and global fallback policy.

**Acceptance Scenarios**:

1. **Given** a context pack is built for a project scope, **When** I inspect it, **Then** I can see whether exact scope is locked and whether global fallback is enabled.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this guardian feature so the first Guardian implementation slice remains reviewable and reproducible.

**Why this priority**: The user asked to keep advancing through GSD + Spec Kit, so this boundary-contract change must be feature-tracked.

**Independent Test**: Run the prerequisite check and confirm it resolves to `030-guardian-scope-contracts` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the guardian feature is active, **When** I run the prerequisite check, **Then** it resolves to `030-guardian-scope-contracts`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Retrieval reasoning MUST mark global-scope fallback results explicitly when they appear under a narrower requested scope.
- **FR-002**: `memory_context_pack` MUST include a boundary contract section that describes exact scope locking and global fallback policy.
- **FR-003**: Guardian boundary metadata MUST remain deterministic and local-only.
- **FR-004**: Existing search result ordering and stable payload shapes MUST remain intact aside from the added boundary metadata and reason tags.
- **FR-005**: Python integration tests MUST cover global fallback reason visibility and context-pack boundary contract payloads.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `030-guardian-scope-contracts` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and Python regression checks passing for the feature.

### Key Entities

- **Global Fallback Reason**: An explicit retrieval reason tag indicating that a result came from the global scope instead of the requested exact scope.
- **Boundary Contract**: A context-pack payload block that describes retrieval scope guarantees.
- **Guardian Slice**: The bounded Tranche B implementation that makes scope boundaries more explicit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tested global fallback results include explicit guardian-style reasoning.
- **SC-002**: Tested context packs surface a boundary contract block.
- **SC-003**: The prerequisite check resolves to `030-guardian-scope-contracts` with its `tasks.md` artifact present.
