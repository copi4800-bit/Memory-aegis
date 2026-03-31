# Feature Specification: Consumer Everyday Surface

**Feature Branch**: `048-consumer-everyday-surface`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Implement Tranche B from `046-consumer-ready-checklist`: simplify the default everyday surface for non-technical users while preserving the Python-owned machine-readable contract underneath.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check Status In Plain Language (Priority: P1)

As a non-technical user, I want the default status output to tell me whether Aegis is ready, degraded, or broken in plain language, so I do not need to read raw JSON or capability flags.

**Why this priority**: The runtime already exposes a strong health contract, but the default status path is still technical and better suited to operators than ordinary users.

**Independent Test**: Run the default status path and verify that the primary output is plain language while the underlying structured payload remains available for programmatic use.

**Acceptance Scenarios**:

1. **Given** a healthy runtime, **When** the user checks status, **Then** Aegis reports a concise human-readable healthy summary.
2. **Given** a degraded runtime, **When** the user checks status, **Then** Aegis explains that local use is still available and distinguishes the degraded condition from a broken one.

---

### User Story 2 - Keep Everyday Verbs Simple (Priority: P1)

As a non-technical user, I want the everyday verbs to remain short and understandable, so the default path emphasizes remember, recall, correct, forget, profile, and status rather than advanced operational controls.

**Why this priority**: The current repo already has the simple verbs, but the surrounding surface still looks operator-first. The default path should clearly favor ordinary usage.

**Independent Test**: Inspect the user-facing CLI and plugin outputs and confirm that the default content for everyday tools is human-readable first rather than raw internal payloads.

**Acceptance Scenarios**:

1. **Given** the user uses the everyday surface, **When** responses are returned, **Then** they prioritize concise human-readable guidance over raw structured output.
2. **Given** machine-readable payloads are still needed, **When** the advanced path is used, **Then** the structured details remain available without being the default user experience.

---

### User Story 3 - Preserve Advanced Paths Without Making Them Default (Priority: P2)

As a maintainer, I want advanced scope, sync, backup, and doctor functionality to remain available without being mistaken for the main non-technical user surface.

**Why this priority**: The repo still needs power-user and integration capabilities, but they should not define the default experience for ordinary users.

**Independent Test**: Review the changed surface and confirm that advanced data remains in `details` or JSON options while the primary displayed content for everyday status paths is plain language.

**Acceptance Scenarios**:

1. **Given** advanced consumers still need structured payloads, **When** they access details or JSON mode, **Then** the machine-readable contract is still intact.
2. **Given** the default user path is used, **When** content is rendered, **Then** advanced internals are not the first thing the user sees.

### Edge Cases

- What happens when the runtime is degraded but local memory still works? The default status must say Aegis is still usable locally.
- What happens when the runtime is broken? The default status must say that memory is not ready for safe use.
- What happens when automation or host tooling still relies on the old structured payload? The structured payload must remain available behind the plain-language first output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST provide a plain-language status summary for the default user path.
- **FR-002**: The default CLI `status` command MUST prioritize human-readable output and still offer JSON output when explicitly requested.
- **FR-003**: The OpenClaw-facing `memory_stats` tool MUST return human-readable primary content while preserving structured details for hosts.
- **FR-004**: The default status summary MUST explicitly distinguish `HEALTHY`, `DEGRADED_SYNC`, and `BROKEN` in language a non-technical user can understand.
- **FR-005**: Advanced operational payloads MUST remain available through JSON mode or tool `details` rather than being removed.
- **FR-006**: The feature MUST add or update tests that lock the new everyday status behavior.

### Key Entities *(include if feature involves data)*

- **StatusSummary**: A concise human-readable explanation of current readiness, health state, and local usability.
- **EverydaySurfaceMode**: The default response mode for non-technical users, where human-readable content is primary and structured detail is secondary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The default CLI status path is readable without requiring JSON parsing.
- **SC-002**: The plugin-facing `memory_stats` content becomes plain-language first while retaining structured details.
- **SC-003**: Tests prove degraded local usability is explained as usable rather than broken.
- **SC-004**: This feature improves `CRC-003` in `046-consumer-ready-checklist` from `PARTIAL` toward a consumer-safe default status path.
