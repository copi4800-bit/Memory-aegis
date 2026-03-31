# Feature Specification: App Surface Refactor

**Feature Branch**: `008-app-surface-refactor`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Refactor Aegis app surface boundaries by extracting host-facing contracts and operational services out of app.py without breaking existing public behavior"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract Public Surface Helpers (Priority: P1)

As a maintainer, I want host-facing contract assembly to live outside `app.py` so that the canonical app orchestrator stops accumulating serialization and adapter-facing helper logic.

**Why this priority**: `app.py` is approaching god-object territory, and host-facing contract helpers are the easiest behavior-preserving extraction path.

**Independent Test**: Run the current Python and bootstrap integration suites and confirm `memory_surface`, `memory_context_pack`, and serialized search payloads stay unchanged after extraction.

**Acceptance Scenarios**:

1. **Given** a host calls public Aegis surfaces, **When** the refactor lands, **Then** returned payload shapes remain backward-compatible.
2. **Given** maintainers inspect the codebase, **When** they open the new helper modules, **Then** they can see public contract assembly separated from core orchestration.

---

### User Story 2 - Extract Operational Services (Priority: P1)

As a maintainer, I want backup and scope-policy operational logic to move into focused service helpers so that `app.py` delegates operational workflows instead of owning their full implementation.

**Why this priority**: Backup/restore and scope-policy paths are growing independently and should not remain embedded in one monolithic app file.

**Independent Test**: Run backup/restore and scope-policy integration tests and confirm behavior remains unchanged while `app.py` delegates to new service modules.

**Acceptance Scenarios**:

1. **Given** a backup upload, preview, or restore request, **When** the refactor lands, **Then** results remain identical to the pre-refactor behavior.
2. **Given** a scope-policy inspection request, **When** the refactor lands, **Then** local-only defaults and explicit sync-policy behavior remain unchanged.

---

### User Story 3 - Codify Refactor Boundary (Priority: P2)

As a maintainer, I want the new ownership boundary documented in feature artifacts and repo docs so that future work follows the extracted structure instead of rebuilding `app.py` bloat.

**Why this priority**: Refactors decay quickly if ownership boundaries are not written down.

**Independent Test**: Review README and feature artifacts and verify they identify which modules now own public contract assembly and operational workflows.

**Acceptance Scenarios**:

1. **Given** a future contributor reads the docs, **When** they look up public surface ownership, **Then** they can see which modules are canonical for contract assembly and operational services.

---

### Edge Cases

- What happens if extracted service helpers start importing each other and recreate the same coupling in a different place?
- How does the refactor avoid changing JSON payload ordering or missing fields in backward-compatible surfaces?
- What happens if backup helpers still need private storage access that is not yet abstracted cleanly?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The refactor MUST preserve existing public behavior for `memory_surface`, `memory_context_pack`, backup flows, and scope-policy inspection.
- **FR-002**: `app.py` MUST delegate public contract assembly to extracted helper modules rather than continuing to own all serialization details directly.
- **FR-003**: `app.py` MUST delegate backup and scope-policy operational workflows to extracted helper modules where behavior can be preserved cleanly.
- **FR-004**: New helper modules MUST remain Python-owned and MUST NOT move memory-domain semantics into TypeScript adapters.
- **FR-005**: The feature MUST add or update regression coverage that proves refactor safety for extracted surfaces.
- **FR-006**: The feature artifacts and repo docs MUST record the new boundary so future work follows the extracted ownership model.

### Key Entities

- **Surface Helper**: A Python-owned helper responsible for assembling stable host-facing payloads without changing memory semantics.
- **Operational Service**: A Python-owned helper responsible for operational workflows such as backup, restore, and scope-policy handling.
- **App Orchestrator**: The `AegisApp` class, which should coordinate subsystems rather than accumulate every detail directly.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `aegis_py/app.py` is materially smaller after extraction while preserving the same public behavior.
- **SC-002**: Python and bootstrap integration suites continue to pass without payload regressions.
- **SC-003**: The resulting module boundary clearly separates orchestration from public contract assembly and operational workflows.
