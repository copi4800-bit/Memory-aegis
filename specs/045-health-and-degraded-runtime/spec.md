# Feature Specification: Health States And Degraded Runtime Operation

**Feature Branch**: `045-health-and-degraded-runtime`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Follow-up bounded feature after `044-production-hardening`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Surface Stable Runtime Health (Priority: P1)

As a maintainer, I want one canonical runtime health model for Aegis so operators and hosts can tell whether the engine is healthy, degraded, or broken without guessing from incidental errors.

**Why this priority**: `044` established a strong validated baseline, but health-state behavior is still implicit rather than modeled as a first-class contract.

**Independent Test**: Query the runtime health surface and confirm it returns a bounded health state with structured issues and does not rely on prose-only interpretation.

**Acceptance Scenarios**:

1. **Given** the database is available and writable, **When** the health surface is queried, **Then** it returns `HEALTHY`.
2. **Given** the runtime detects non-fatal operational problems, **When** the health surface is queried, **Then** it returns a degraded state with explicit issue codes instead of opaque generic failures.

---

### User Story 2 - Preserve Offline-First Writes During Degraded States (Priority: P1)

As an operator, I want local reads and writes to continue while optional remote or deferred workflows are degraded, so Aegis remains truthful to its local-first contract.

**Why this priority**: The constitution requires that optional distributed or remote capabilities never become hidden blockers for local memory behavior.

**Independent Test**: Simulate degraded remote state and confirm local store/search operations still succeed while the health surface reports the degraded mode.

**Acceptance Scenarios**:

1. **Given** sync-adjacent behavior is unavailable or explicitly degraded, **When** a local memory is stored, **Then** the write succeeds without waiting for recovery.
2. **Given** the runtime is degraded but not broken, **When** the host asks for status, **Then** the response includes both the degraded state and the preserved local capability.

---

### User Story 3 - Distinguish Broken From Degraded (Priority: P1)

As a maintainer, I want hard failures like missing or unusable local storage to be marked as broken rather than merely degraded, so operators can distinguish recoverable optional-service issues from core engine failure.

**Why this priority**: Without this boundary, degraded-mode reporting becomes misleading and could mask loss of core local-first functionality.

**Independent Test**: Force a local database failure scenario and confirm the runtime reports `BROKEN` rather than a soft degraded state.

**Acceptance Scenarios**:

1. **Given** the local database cannot be opened or repaired, **When** the health surface is queried, **Then** the runtime reports `BROKEN`.
2. **Given** a core local dependency fails, **When** the host tries to use a local-only operation, **Then** the operation fails clearly and the health surface explains why.

---

### User Story 4 - Keep Health Contract Aligned Across Surfaces (Priority: P2)

As a maintainer, I want README, plugin metadata, Python runtime surfaces, and the TS adapter shell to describe the same health contract, so host integrations do not drift.

**Why this priority**: `044` fixed major surface drift. Health-state semantics must not reopen that problem.

**Independent Test**: Compare the declared health/status surfaces across runtime and docs and verify that the same bounded states and meanings are represented.

**Acceptance Scenarios**:

1. **Given** the health model changes, **When** the repo is updated, **Then** `README.md`, `aegis_py/surface.py`, `openclaw.plugin.json`, and adapter-facing status surfaces remain aligned.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The runtime MUST define a bounded health-state enum for the local-first engine, including at least `HEALTHY`, `DEGRADED_SYNC`, and `BROKEN`.
- **FR-002**: The health surface MUST return structured issue codes and relevant capability flags rather than only prose.
- **FR-003**: Local-only store/search/status operations MUST continue working while the runtime is in degraded-but-not-broken states.
- **FR-004**: Optional remote or deferred workflows MUST not silently upgrade degraded conditions into hard blockers for local operations.
- **FR-005**: Core local storage failures MUST be reported as `BROKEN`, not as a recoverable degraded mode.
- **FR-006**: The Python-owned public surface, README, plugin metadata, and TS adapter-facing status output MUST remain aligned on the health contract.
- **FR-007**: Validation evidence for this feature MUST include tests that prove degraded-state reporting and local-write preservation.

### Key Entities

- **HealthState**: Canonical runtime state describing whether Aegis is healthy, degraded in a bounded way, or broken.
- **HealthIssue**: Structured issue code and metadata explaining why the runtime is degraded or broken.
- **CapabilityFlag**: Machine-readable indicator for whether local store, local search, backup, and optional sync-adjacent flows are currently available.

## Non-Goals

- This feature does not add cloud dependencies or hosted control planes.
- This feature does not redesign sync architecture.
- This feature does not replace the validated backup/migration work completed in `044`.
- This feature does not reopen TypeScript memory-domain ownership.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The health surface reports bounded states and structured issues in tests, not only free-form text.
- **SC-002**: Local write/read tests continue to pass while degraded states are simulated.
- **SC-003**: Broken local-storage scenarios are distinguished from degraded optional-service scenarios in tests.
- **SC-004**: The public surfaces that expose health/status remain aligned after the feature lands.
