# Feature Specification: Consumer Recovery Trust

**Feature Branch**: `049-consumer-recovery-trust`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Implement Tranche C from `046-consumer-ready-checklist`: make backup, restore, and diagnostics safer and more understandable for ordinary users without dropping the Python-owned structured contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Recovery Actions (Priority: P1)

As a non-technical user, I want backup and restore commands to explain what they did or what they are about to do in plain language, so I do not need to inspect raw JSON to trust recovery actions.

**Why this priority**: Backup and restore exist today, but the current surfaces remain operator-oriented. That keeps `CRC-006` partial.

**Independent Test**: Run the backup and preview commands from the CLI and verify that the default output explains the action, target path, and likely impact in plain language.

**Acceptance Scenarios**:

1. **Given** a healthy local runtime, **When** the user creates a backup, **Then** Aegis reports where the backup was written and what kind of backup it is.
2. **Given** a backup file exists, **When** the user previews a restore, **Then** Aegis explains whether the preview is safe, what scope it targets, and how many records are involved.

---

### User Story 2 - Understand Diagnostics Without Reading Machine Payloads (Priority: P1)

As a non-technical user, I want the default doctor/health output to explain whether Aegis is healthy, degraded, or broken and what I should do next.

**Why this priority**: The health contract is already good for machines and maintainers, but ordinary users still need a trust-oriented explanation path.

**Independent Test**: Run the doctor path on healthy and degraded states and verify that the primary output is a readable diagnostic summary while JSON remains available explicitly.

**Acceptance Scenarios**:

1. **Given** Aegis is healthy, **When** the user runs doctor, **Then** Aegis reports that memory is operating normally.
2. **Given** Aegis is degraded but local runtime still works, **When** the user runs doctor, **Then** Aegis explains that local use is still available and names the issue in understandable language.

---

### User Story 3 - Preserve Automation Paths (Priority: P2)

As a maintainer, I want the structured recovery and diagnostics payloads preserved for automation and plugin integrations, so consumer improvements do not break operational tooling.

**Why this priority**: The repo still needs stable JSON/details payloads for host integrations and tests.

**Independent Test**: Verify that the CLI supports explicit JSON output and that plugin tool `details` keep the existing structured payloads even when primary displayed content becomes summary-first.

**Acceptance Scenarios**:

1. **Given** the CLI defaults to plain-language output, **When** the caller passes `--json`, **Then** the full structured payload is still returned.
2. **Given** the plugin surfaces doctor output, **When** the tool executes, **Then** the primary text is human-readable and `details` still contain the Python payload.

### Edge Cases

- What happens when a restore preview targets only one scope? The summary should say it is scope-limited rather than implying a full DB restore.
- What happens when Aegis is degraded but not broken? Recovery and doctor summaries should say local use is still available.
- What happens when the backup file does not exist? The command should still fail clearly rather than pretending the action succeeded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST provide plain-language default summaries for doctor, backup creation, backup listing, restore preview, and restore completion on the CLI path.
- **FR-002**: The CLI MUST preserve full structured payloads for those commands when explicitly requested with JSON mode.
- **FR-003**: The default summaries MUST distinguish healthy, degraded, and broken local runtime states in understandable language.
- **FR-004**: Restore preview summaries MUST indicate whether the preview is full-database or scope-limited and report the main record-count impact.
- **FR-005**: The OpenClaw-facing `memory_doctor` tool MUST present human-readable primary content while keeping structured `details`.
- **FR-006**: The feature MUST add or update tests for the new recovery and diagnostics summaries.

### Key Entities *(include if feature involves data)*

- **DoctorSummary**: Plain-language explanation of current runtime health, local usability, and next-step guidance.
- **RecoverySummary**: Plain-language explanation of backup creation, backup listing, restore preview, or restore completion with the minimum details a non-technical user needs to trust the action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Default CLI recovery and doctor commands are readable without JSON parsing.
- **SC-002**: Restore preview tells the user whether the action is full or scope-limited and what the main impact will be.
- **SC-003**: Plugin-facing `memory_doctor` content becomes summary-first while preserving structured `details`.
- **SC-004**: This feature improves `CRC-006` in `046-consumer-ready-checklist` from `PARTIAL` toward a consumer-safe recovery/trust surface.
