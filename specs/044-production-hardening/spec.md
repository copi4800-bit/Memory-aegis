# Feature Specification: Production Hardening And SRE-Grade Guarantees

**Feature Branch**: `044-production-hardening`
**Created**: 2026-03-24
**Status**: Draft
**Input**: Tranche C of 041-completion-program, refined against current validated runtime gaps

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore A Fully Green Runtime Baseline (Priority: P1)

As a maintainer, I want the current Python-owned runtime to pass its validated regression suite before more capability is added, so that "complete" means operationally trustworthy rather than aspirational.

**Why this priority**: The current repo already runs, but known red tests prove that key promises around semantic recall, trust shaping, link behavior, scoped restore, and legacy repair are not yet production-safe.

**Independent Test**: Run the canonical local validation commands and confirm the runtime passes the current Python suite and the Python-adapter TypeScript integration suite without expected-failure exceptions.

**Acceptance Scenarios**:

1. **Given** the Python runtime is the public owner, **When** the canonical validation suite is run, **Then** the current red tests for semantic dedupe, semantic recall, trust shaping, Weaver link flows, scoped restore, and legacy schema repair are green.
2. **Given** the TypeScript shell remains transitional only, **When** the adapter integration suite is run, **Then** it still passes without reintroducing memory-domain logic into the shell.

---

### User Story 2 - Automated Backup and Restore Drills (Priority: P1)

As a maintainer, I want built-in tools for safely taking consistent snapshots of the database and executing restore drills, so that I have absolute confidence that long-lived data will survive catastrophic failures.

**Why this priority**: A memory engine is only as good as its durability. Without verified backups, "production ready" is a false claim.

**Independent Test**: Run a CLI command or API method that takes a consistent snapshot while the database is being written to, and then use a verify command to restore the snapshot to an isolated environment and confirm schema and data integrity.

**Acceptance Scenarios**:

1. **Given** an active Aegis instance, **When** the backup command is executed, **Then** a consistent SQLite snapshot is saved without locking the main database.
2. **Given** a backup file, **When** a restore drill is executed, **Then** the tool verifies file integrity, schema version, and successful connection.

---

### User Story 3 - Automated Migration Tooling (Priority: P1)

As an operator, I want a declarative, versioned database migration system, so that schema updates across multiple distributed nodes do not cause structural drift or data loss.

**Why this priority**: Up to now, migrations were ad-hoc scripts. Production hardening requires a rigorous schema versioning system.

**Independent Test**: Setup an older version of the schema, run the new migration manager, and verify `user_version` PRAGMA is updated and tables are correctly modified.

**Acceptance Scenarios**:

1. **Given** a database on schema `v1`, **When** the migration tool is run, **Then** it applies exactly the scripts needed to reach `v2` and updates the internal version tracking.

---

### User Story 4 - Health Degradation Modes (Priority: P2)

As a system, I want to degrade gracefully rather than crash entirely when non-critical components (like the sync network or ML embedding services) fail, so that local offline memory operations continue uninterrupted.

**Why this priority**: "Local-first" means offline operations must never be blocked by cloud/sync failures.

**Independent Test**: Disconnect the network (simulated). Attempt to write a memory. Verify the memory is saved locally and marked as `pending_sync`, while the system surfaces a "Degraded: Sync Offline" health status.

**Acceptance Scenarios**:

1. **Given** the remote sync endpoint is unreachable, **When** a local save occurs, **Then** the local operation succeeds immediately and the system health metric indicates a sync disruption.

---

### User Story 5 - Benchmark & Regression Gates (Priority: P2)

As a developer, I want an automated performance and semantic regression test suite that measures query latency, retrieval accuracy, and conflict leakage, so I am blocked from releasing code that degrades the engine.

**Why this priority**: SRE-grade guarantees require continuous measurement of SLIs (Service Level Indicators).

**Independent Test**: Run a benchmark CLI command that tests retrieval time. Introduce a bad index change, run it again, and verify the command fails with an SLI violation.

**Acceptance Scenarios**:

1. **Given** a standard benchmark dataset, **When** the regression suite is executed, **Then** it asserts that p95 read latency is under the defined threshold (e.g., <50ms).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST keep Python as the public owner of memory-domain behavior, with TypeScript limited to host/bootstrap and adapter responsibilities.
- **FR-002**: System MUST preserve parity across the declared public surfaces in `README.md`, `openclaw.plugin.json`, `aegis_py/surface.py`, `aegis_py/mcp/server.py`, and the TypeScript plugin shell.
- **FR-003**: System MUST restore a fully green baseline for the currently validated Python runtime behaviors, including semantic dedupe, semantic recall, trust/conflict shaping, Weaver auto-linking and bounded multi-hop behavior, scoped backup preview/restore, and legacy schema repair.
- **FR-004**: System MUST implement a safe backup mechanism leveraging SQLite's Backup API to prevent locked DBs.
- **FR-005**: System MUST include a verification tool for restoring and checking backup integrity.
- **FR-006**: System MUST track database schema versions using SQLite's `user_version` PRAGMA and execute incremental migrations.
- **FR-007**: System MUST repair supported legacy databases in place rather than forcing destructive reset when required columns or helper tables are missing.
- **FR-008**: System MUST maintain operational health states (e.g., `HEALTHY`, `DEGRADED_SYNC`, `DEGRADED_EMBEDDING`) and never block local reads/writes due to degraded remote states.
- **FR-009**: System MUST include a performance and regression suite asserting retrieval quality, trust visibility, and operational SLOs before release.
- **FR-010**: Completion evidence for this feature MUST include the canonical command set and observed pass counts for both Python and TypeScript adapter validation.

### Key Entities

- **HealthState**: The current operational status of the local instance and its remote dependencies.
- **BackupSnapshot**: A verified, point-in-time copy of the SQLite database.
- **SchemaVersion**: An integer tracking the structural state of the database.
- **Runtime Validation Baseline**: The current known-good command set and pass criteria for Python runtime tests and TypeScript adapter integration tests.
- **Surface Contract Matrix**: The explicit list of user-facing operations and owners that must remain aligned across docs, plugin metadata, and runtime adapters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The canonical Python validation command passes with 0 failing tests on the tracked runtime suite.
- **SC-002**: The canonical TypeScript adapter validation command passes with 0 failing tests.
- **SC-003**: Backups complete successfully while concurrent writes are happening, with 0 data corruption on restore.
- **SC-004**: 100% of offline writes succeed within <50ms even when sync endpoints are completely unreachable.
- **SC-005**: Migration from an empty database and a supported legacy database to the current schema executes cleanly using the versioned migration runner.
- **SC-006**: A defined set of latency, semantic, and trust-visibility SLIs are implemented and integrated into the test runner.
