# Feature Specification: Production Discipline

**Feature Branch**: `072-production-discipline`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Finish the production-excellence wave with a bounded operational discipline slice: release gate, soak-test routine, rollback checklist, and concrete runbooks."

## User Scenarios & Testing

### User Story 1 - Release Gate Discipline (Priority: P1)

As an operator, I want a fixed release gate so each deployment proves the same minimum evidence before touching the live bot.

**Why this priority**: Once correctness and observability exist, inconsistency in release behavior becomes the next main source of avoidable outages.

**Independent Test**: Review and execute one command set from the release checklist without guessing hidden steps.

**Acceptance Scenarios**:

1. **Given** a candidate change, **When** the operator follows the release gate, **Then** build, focused tests, sync checks, and live sanity checks are all explicit.
2. **Given** a failed gate step, **When** the operator stops the release, **Then** the checklist makes the stop condition and rollback path obvious.

---

### User Story 2 - Recovery Runbooks (Priority: P1)

As a maintainer, I want short runbooks for the highest-signal failure modes so I can recover quickly without rediscovering the procedure under pressure.

**Why this priority**: A system that works but cannot be recovered calmly is not production-ready.

**Independent Test**: A maintainer can open the relevant runbook and execute the first-response steps without reading source code.

**Acceptance Scenarios**:

1. **Given** polling stalls, sync failures, DB locks, restore mismatches, or duplicate replies, **When** the matching runbook is opened, **Then** symptoms, triage, verification, and recovery steps are listed.
2. **Given** a risky recovery action, **When** the runbook is followed, **Then** the operator is told what to verify before and after making changes.

---

### User Story 3 - Soak and Rollback Practice (Priority: P2)

As a system owner, I want soak-test and rollback drills defined so reliability is practiced rather than assumed.

**Why this priority**: Production discipline is mostly rehearsal, not documentation volume.

**Independent Test**: A maintainer can run the soak checklist and the rollback checklist end-to-end on a staging-shaped environment.

**Acceptance Scenarios**:

1. **Given** a candidate release, **When** the soak checklist runs for 30 minutes, 6 hours, or 24 hours, **Then** the observed signals and abort conditions are explicit.
2. **Given** a bad release, **When** the rollback checklist is executed, **Then** service restart, snapshot choice, verification, and stop conditions are explicit.

## Requirements

### Functional Requirements

- **FR-001**: The tranche MUST define a single release gate checklist for the current deployment class.
- **FR-002**: The tranche MUST add runbooks for polling stalls, sync failure, DB lock, restore mismatch, and duplicate reply.
- **FR-003**: The tranche MUST define a soak-test checklist covering at least 30-minute, 6-hour, and 24-hour windows.
- **FR-004**: The tranche MUST define a rollback checklist that can be executed in under 5 minutes for normal bad-release recovery.
- **FR-005**: The tranche MUST stay bounded to operational discipline artifacts and avoid reopening runtime feature scope.

## Success Criteria

- **SC-001**: A maintainer can perform the full release gate from a single checklist.
- **SC-002**: A maintainer can find a runbook for each selected high-signal failure mode.
- **SC-003**: Soak-test and rollback drills are explicit enough to execute without code archaeology.
