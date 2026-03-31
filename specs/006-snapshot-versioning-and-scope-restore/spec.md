# Feature Specification: Snapshot Versioning And Scope Restore

**Feature Branch**: `006-snapshot-versioning-and-scope-restore`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Make Aegis better than neural-memory at backup/restore with versioning, manifests, and safer restore flows"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auditable Snapshot Backups (Priority: P1)

As a maintainer, I want every Aegis backup to carry a structured manifest so that I can audit what was backed up, from which runtime version and database, before I restore anything.

**Why this priority**: Without a manifest, backups are opaque files and restore safety stays weak.

**Independent Test**: Create snapshot and export backups in a clean workspace, inspect their manifests, and verify the metadata includes backup type, timestamps, counts, and DB identity fields.

**Acceptance Scenarios**:

1. **Given** a snapshot backup request, **When** Aegis creates the backup, **Then** it writes a companion manifest with backup mode, timestamp, DB path, memory counts, and runtime version fields.
2. **Given** an export backup request, **When** Aegis creates the backup, **Then** it writes a manifest that describes the exported scope and record counts in a machine-readable format.

---

### User Story 2 - Safe Restore Preview (Priority: P1)

As a maintainer, I want a dry-run restore preview so that I can see the impact of a restore before mutating the active database.

**Why this priority**: Restore is the highest-risk mutation path in the system and must follow the constitution's log-first, suggest-first rule.

**Independent Test**: Run restore preview against both snapshot and export backups and verify the result reports the target path, backup metadata, and estimated impact without modifying the live DB.

**Acceptance Scenarios**:

1. **Given** a valid backup file, **When** I request a restore dry-run, **Then** Aegis returns restore metadata and impact details without changing the active database.
2. **Given** an invalid or incompatible backup, **When** I request a restore dry-run, **Then** Aegis returns a clear validation error before any mutation happens.

---

### User Story 3 - Snapshot History Navigation (Priority: P2)

As a maintainer, I want to list and inspect prior snapshots so that I can reason about recovery options without browsing raw files manually.

**Why this priority**: Versioning is only useful if the user can discover available restore points and compare them at a glance.

**Independent Test**: Create multiple backups, list them through the Python runtime, and verify the returned entries are ordered, typed, and manifest-backed.

**Acceptance Scenarios**:

1. **Given** multiple backups in the workspace, **When** I list snapshots, **Then** Aegis returns a stable ordered history with mode, timestamp, size, and manifest path.
2. **Given** a backup without a valid manifest, **When** snapshots are listed, **Then** Aegis either excludes it or marks it as invalid instead of treating it as a trusted restore point.

---

### Edge Cases

- What happens if a snapshot file exists but its manifest is missing or corrupted?
- How does dry-run restore behave when the active database is empty, newer, or structurally different from the backup?
- What happens if a workspace contains both snapshot backups and export backups with overlapping timestamps?
- How does Aegis prevent partial restores from looking successful when only some records were valid?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Python runtime MUST write a machine-readable manifest for every backup it creates.
- **FR-002**: Backup manifests MUST include mode, created timestamp, target artifact path, file size, active-memory counts, and runtime version metadata.
- **FR-003**: The Python runtime MUST expose a snapshot listing surface that returns known backups in a stable order with manifest-backed metadata.
- **FR-004**: The Python runtime MUST expose a restore dry-run surface that validates a backup and reports restore impact without mutating the active database.
- **FR-005**: Restore preview MUST work for both snapshot and export backups.
- **FR-006**: Backup and restore metadata MUST remain local-first and file-system based; this feature MUST NOT require any cloud service.
- **FR-007**: Invalid backup files or invalid manifests MUST fail closed with explicit validation errors.
- **FR-008**: The host bootstrap and MCP surface MUST route backup listing and dry-run restore through Python-owned paths.

### Key Entities

- **Backup Manifest**: JSON metadata describing a backup artifact, its mode, provenance, file identity, and summary counts.
- **Backup Record**: A listed restore point resolved from a backup artifact plus its manifest.
- **Restore Preview**: A non-mutating validation result showing what a restore would target and whether it is safe to apply.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every newly created backup includes a manifest with the required metadata fields.
- **SC-002**: Users can list available backups from the Python runtime without manually inspecting directories.
- **SC-003**: Dry-run restore returns a structured impact report and does not mutate the active DB.
- **SC-004**: The canonical Python validation workflow includes regression coverage for manifests, listing, and dry-run restore.
