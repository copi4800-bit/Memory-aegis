# Feature Specification: Consumer Onboarding

**Feature Branch**: `047-consumer-onboarding`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Implement Tranche A from `046-consumer-ready-checklist`: replace the current self-test style setup with a real onboarding flow on the Python-owned runtime.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run First-Time Setup Successfully (Priority: P1)

As a non-technical user, I want one setup command that checks whether Aegis can create its local DB, store a test memory, and recall it, so I can know whether the system is actually ready.

**Why this priority**: The repo already has a runtime, but the current setup flow is a developer-oriented self-test. Without a live first-run check, onboarding is still partial.

**Independent Test**: Run the onboarding command on an empty temporary workspace and verify that it reports DB creation, write success, recall success, and a ready/not-ready summary.

**Acceptance Scenarios**:

1. **Given** an empty workspace, **When** the user runs the setup command, **Then** Aegis creates or opens the local DB and reports the result in plain language.
2. **Given** a healthy runtime, **When** onboarding runs, **Then** it performs a real write and recall check through the Python-owned runtime and reports success.

---

### User Story 2 - Explain Failure In Plain Language (Priority: P1)

As a non-technical user, I want setup failures explained in plain language, so I know what is wrong without reading internal engine details.

**Why this priority**: A setup flow that only dumps technical JSON or generic exceptions is still developer-facing, not consumer-facing.

**Independent Test**: Force a setup problem such as an unwritable workspace or broken DB path and verify that onboarding marks the run as not ready and lists understandable next-step guidance.

**Acceptance Scenarios**:

1. **Given** the workspace is not writable or the DB cannot be initialized, **When** onboarding runs, **Then** the summary reports the failure as not ready and explains the likely cause.
2. **Given** health is degraded but local runtime still works, **When** onboarding runs, **Then** the summary distinguishes usable-but-degraded from broken.

---

### User Story 3 - Use The Same Active Production Path (Priority: P2)

As a maintainer, I want setup to use the Python-owned production runtime rather than legacy TS engine code, so onboarding does not drift from the path users actually rely on.

**Why this priority**: The current repo has legacy TS-era onboarding artifacts. The active onboarding path must align with the Python runtime that owns production semantics.

**Independent Test**: Inspect the setup entrypoint and verify that it invokes the Python onboarding command rather than the retired TS engine or a raw MCP self-test.

**Acceptance Scenarios**:

1. **Given** the setup CLI runs, **When** its implementation is inspected, **Then** it routes through `aegis_py` rather than `AegisMemoryManager`.
2. **Given** the onboarding flow succeeds, **When** the same DB is queried later, **Then** the runtime remains usable without depending on a TS-only data path.

### Edge Cases

- What happens when setup can write locally but health is degraded due to optional sync issues? The onboarding result should still mark local runtime usable while reporting degraded state clearly.
- What happens when the onboarding probe memory is created successfully? The flow must clean up or archive its probe so setup does not leave confusing junk behind.
- What happens when the Python executable cannot be found? The setup wrapper should fail clearly instead of silently succeeding.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST provide a Python-owned onboarding flow that runs against the active production runtime.
- **FR-002**: The onboarding flow MUST check local database initialization or availability.
- **FR-003**: The onboarding flow MUST perform a real local write test and a real local recall test.
- **FR-004**: The onboarding flow MUST report health in plain language while preserving the bounded health contract underneath.
- **FR-005**: The onboarding flow MUST report a ready or not-ready summary for non-technical users.
- **FR-006**: The OpenClaw-facing setup wrapper MUST invoke the Python onboarding flow instead of a raw MCP self-test.
- **FR-007**: The feature MUST add tests covering successful onboarding and at least one failure or degraded-mode explanation path.

### Key Entities *(include if feature involves data)*

- **OnboardingReport**: Structured result of setup containing DB path, health state, write-test result, recall-test result, readiness state, and plain-language guidance.
- **OnboardingCheck**: One concrete setup check such as database availability, workspace writability, write success, or recall success.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-run onboarding command succeeds on a fresh local workspace and reports successful DB, write, and recall checks.
- **SC-002**: The setup wrapper uses the Python-owned onboarding path rather than the legacy TS engine or a raw server self-test.
- **SC-003**: At least one onboarding test proves failures or degraded states are explained clearly enough to distinguish usable from broken.
- **SC-004**: This feature improves `CRC-004` in `046-consumer-ready-checklist` from `PARTIAL` toward an active production onboarding path.
