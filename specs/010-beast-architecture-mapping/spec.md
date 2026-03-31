# Feature Specification: Beast Architecture Mapping

**Feature Branch**: `010-beast-architecture-mapping`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Map the 23 Aegis beasts into the current Python architecture using GSD + Spec Kit so the lore becomes an internal engineering guide instead of loose notes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonical Internal Beast Map (Priority: P1)

As an Aegis maintainer, I want a canonical beast-to-module map in the repo so future refactors share the same internal architecture language.

**Why this priority**: The user explicitly wants the "23 beasts" carried forward, but the repo needs one authoritative mapping instead of ad hoc lore.

**Independent Test**: Review the new architecture document and verify that all 23 beasts are mapped to current or target Python ownership boundaries.

**Acceptance Scenarios**:

1. **Given** the architectural note in `/home/hali/.openclaw/1.md`, **When** I read the canonical beast map in the repo, **Then** I can see where each beast belongs in the Python engine.
2. **Given** a contributor wants to refactor Aegis, **When** they use the beast map, **Then** they can translate lore into concrete module ownership instead of guessing.

---

### User Story 2 - Align Repo Docs With The Six-Module Model (Priority: P1)

As a contributor, I want the README to describe the six-module consolidation so the public docs no longer imply that the beasts should become 23 runtime modules.

**Why this priority**: The repo already uses six practical boundaries; documentation should say that explicitly to prevent future over-fragmentation.

**Independent Test**: Review the README and confirm it describes the six-module architecture and points to the internal beast map for deeper detail.

**Acceptance Scenarios**:

1. **Given** a contributor reads the README, **When** they look for architecture guidance, **Then** they find the six-module model and a pointer to the internal beast map.

---

### User Story 3 - Reconcile GSD + Spec Kit Artifacts (Priority: P2)

As a maintainer, I want feature artifacts and planning state updated for the beast mapping work so the repo remains consistent with the GSD + Spec Kit workflow.

**Why this priority**: The user required this work to be tracked through the repo workflow rather than added as an undocumented side note.

**Independent Test**: Run the Spec Kit prerequisite check and confirm the active feature resolves to `010-beast-architecture-mapping` with its task artifact present.

**Acceptance Scenarios**:

1. **Given** the feature is active, **When** I run the prerequisite check, **Then** it resolves to the `010` feature artifacts instead of the prior feature.

---

### Edge Cases

- Some beasts map to an existing module only partially and should be marked as "partial" rather than forced into a false exact match.
- Some current directories use names such as `preferences/` that serve the role of the target `profiles/` module and should be documented without an immediate rename.
- The beast map must stay internal-facing and must not leak lore-heavy names into user-facing tool surfaces.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST add a canonical internal architecture document that maps all 23 beasts from `/home/hali/.openclaw/1.md` to current or target Python boundaries.
- **FR-002**: The canonical beast map MUST preserve the six-module consolidation already adopted in feature `007-hybrid-memory-core`.
- **FR-003**: The beast map MUST distinguish between current ownership, target ownership, and partial or deferred implementation where needed.
- **FR-004**: The README MUST describe the six-module model and point readers to the internal beast map.
- **FR-005**: `.planning/STATE.md` MUST be reconciled to the active `010-beast-architecture-mapping` feature.
- **FR-006**: The feature MUST keep beast naming as internal architecture language and MUST NOT expose beast names as public runtime/tool contracts.

### Key Entities

- **Beast Map**: The canonical internal document that translates all 23 Aegis beasts into concrete Python module ownership.
- **Six-Module Model**: The architecture target formed by `memory`, `retrieval`, `hygiene`, `profiles`, `storage`, and `integration`.
- **Ownership Status**: A per-beast status such as `current`, `target`, `partial`, or `deferred` explaining how that beast exists in the current Python engine.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 23 beasts are mapped in a repo-tracked internal architecture document.
- **SC-002**: Repo docs clearly state that the beast model is an internal taxonomy and that the runtime remains organized around the six-module model.
- **SC-003**: The active feature check resolves to `010-beast-architecture-mapping` with its `tasks.md` artifact present.
