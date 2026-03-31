# Feature Specification: Guided Host Integration

**Feature Branch**: `051-guided-host-integration`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Resolve the remaining consumer-closure blockers by reducing residual TS-era ambiguity and defining a guided ordinary-user host surface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clear Default Host Path (Priority: P1)

As a maintainer or host integrator, I want one explicit manifest-level description of the ordinary-user tool path, so the default host experience does not have to be inferred from a large mixed tool catalog.

**Why this priority**: The closure review still blocks on guided host integration. The repo needs one clear source of truth for which tools belong to ordinary users versus advanced operators.

**Independent Test**: Read the plugin manifest and verify that it declares a bounded consumer/default surface distinct from advanced tools.

**Acceptance Scenarios**:

1. **Given** the plugin manifest, **When** a maintainer inspects it, **Then** they can see which tools are the default everyday path for ordinary users.
2. **Given** advanced tools still exist, **When** the consumer surface is reviewed, **Then** those tools are clearly separated rather than mixed into the default path.

---

### User Story 2 - Remove TS-Era Onboarding Ambiguity (Priority: P1)

As a maintainer, I want leftover TS-era onboarding code to fail loudly with a migration message instead of looking like an active path, so the production boundary stays clear.

**Why this priority**: `CRC-005` remains partial because the repo still ships legacy-oriented UX files alongside the Python-owned runtime.

**Independent Test**: Inspect the TS onboarding module and verify that it is an explicit legacy stub rather than an alternate active onboarding implementation.

**Acceptance Scenarios**:

1. **Given** a maintainer opens the legacy onboarding module, **When** they inspect it, **Then** it clearly states that onboarding moved to the Python-owned runtime.
2. **Given** a caller tries to invoke the legacy onboarding export, **When** it runs, **Then** it fails with a migration message rather than silently presenting an outdated path.

---

### User Story 3 - Document Consumer Versus Advanced Paths (Priority: P2)

As a maintainer, I want the README and manifest to align on the default user path, so closure decisions are based on explicit product boundaries rather than repo folklore.

**Why this priority**: The consumer-complete label should be blocked or allowed by artifacts, not by memory of prior chat turns.

**Independent Test**: Verify that the README and manifest describe the same bounded consumer path.

**Acceptance Scenarios**:

1. **Given** the README and manifest, **When** they are compared, **Then** they point to the same ordinary-user verbs and same advanced-tool separation.

### Edge Cases

- What happens if advanced tools remain present? They should stay available but must not be mistaken for the default user path.
- What happens if old imports still point at TS-era onboarding? They should fail clearly with a migration message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin manifest MUST declare a bounded consumer/default tool surface separate from advanced tools.
- **FR-002**: The README MUST describe the same default consumer path as the manifest.
- **FR-003**: The TS-era onboarding module MUST be converted into an explicit legacy stub with a migration message to the Python-owned path.
- **FR-004**: The feature MUST add or update tests that lock the manifest consumer surface and the TS legacy-stub behavior.

### Key Entities *(include if feature involves data)*

- **ConsumerSurface**: The manifest-level definition of the ordinary-user path, including default tools and the distinction from advanced tools.
- **LegacyStub**: A retained file that exists only to fail clearly and redirect callers to the active Python-owned runtime path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The plugin manifest exposes an explicit consumer/default tool set.
- **SC-002**: The TS onboarding module no longer appears to be an active production path.
- **SC-003**: The closure blockers `CRC-005` and `CRC-007` are reduced by explicit artifact and code evidence.
