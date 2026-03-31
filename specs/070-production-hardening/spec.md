# Feature Specification: Production Hardening

**Feature Branch**: `070-production-hardening`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Turn the already-working Aegis v7 runtime into a more production-trustworthy system by locking acceptance coverage, regression coverage, and data-safety invariants for critical flows."

## User Scenarios & Testing

### User Story 1 - Critical Flow Acceptance Coverage (Priority: P1)

As an operator, I want the critical user-facing flows to have stable acceptance coverage so regressions are caught before release.

**Why this priority**: The runtime already works. The next risk is silent regression in the flows people actually depend on.

**Independent Test**: Run a focused acceptance suite that exercises remember, recall, backup, restore, sync, and background mutation safety on temporary databases.

**Acceptance Scenarios**:

1. **Given** a fresh runtime database, **When** the acceptance suite runs, **Then** remember and recall complete successfully with the expected scope and result shape.
2. **Given** a populated runtime database, **When** backup and restore acceptance checks run, **Then** the restored database preserves the expected records and audit-visible metadata.
3. **Given** sync-eligible scopes and background proposals, **When** sync and governed background acceptance checks run, **Then** the runtime proves the expected success path without manual operator intervention.

---

### User Story 2 - Historical Regression Locking (Priority: P1)

As a maintainer, I want known failure classes to have explicit regression coverage so previously fixed behavior does not quietly break again.

**Why this priority**: Production trust comes less from new features than from refusing to reintroduce old bugs.

**Independent Test**: Run a regression suite that covers the known failure classes without depending on production services.

**Acceptance Scenarios**:

1. **Given** a runtime/config boundary issue that was previously observed, **When** the regression suite runs, **Then** the affected path is exercised and the old failure does not reappear.
2. **Given** a dry-run or preview path, **When** the regression suite runs, **Then** the database remains unchanged.
3. **Given** a rollback path after a governed apply, **When** the regression suite runs, **Then** the runtime restores the pre-apply state instead of leaving partial mutation behind.

---

### User Story 3 - Data-Safety Invariants (Priority: P2)

As a system owner, I want the runtime to prove core data-safety invariants so I can trust it under normal operator error and normal release churn.

**Why this priority**: Passing happy-path tests is not enough if destructive paths can still violate scope or mutation boundaries.

**Independent Test**: Run invariant-focused tests that validate scope isolation, dry-run safety, restore safety, and rollback safety.

**Acceptance Scenarios**:

1. **Given** memories from multiple scopes, **When** retrieval and sync acceptance checks run, **Then** no cross-scope leakage occurs.
2. **Given** preview and dry-run operations, **When** the suite completes, **Then** durable row counts and revision-sensitive state remain unchanged.
3. **Given** a backup restore or governed rollback, **When** the operation completes, **Then** the resulting state matches the expected post-recovery contract.

### Edge Cases

- What happens when acceptance tests run against an empty database and a partially populated database?
- How does the suite prove mutation safety for preview/dry-run paths without relying on operator eyeballing?
- What happens when governed background work produces no proposals for a scope?

## Requirements

### Functional Requirements

- **FR-001**: The feature MUST add acceptance coverage for the critical flows: remember, recall, backup, restore, sync, background apply, and background rollback.
- **FR-002**: The feature MUST add regression coverage for known failure classes already observed during runtime integration or migration work.
- **FR-003**: The feature MUST prove dry-run and preview operations do not mutate durable state.
- **FR-004**: The feature MUST prove rollback restores the expected pre-apply contract for governed background operations.
- **FR-005**: The feature MUST prove restore produces the expected post-restore contract on a separate database.
- **FR-006**: The feature MUST prove no cross-scope leakage for the acceptance flows it covers.
- **FR-007**: The feature MUST keep the test surface runnable from the local Python-owned runtime without requiring live network services.
- **FR-008**: The feature MUST document the acceptance and regression command set used to validate this tranche.

### Key Entities

- **Acceptance Flow**: A production-critical runtime path exercised end-to-end against a temporary database or workspace.
- **Regression Case**: A test fixture that locks a previously observed failure class.
- **Safety Invariant**: A durable rule that must remain true after preview, rollback, restore, or scoped retrieval operations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A focused acceptance suite exists for all critical flows and runs green locally.
- **SC-002**: At least one regression test exists for each known high-signal failure class chosen for this tranche.
- **SC-003**: Dry-run and preview paths are verified to leave durable state unchanged.
- **SC-004**: Restore and rollback paths are verified on separate test databases without manual inspection.

