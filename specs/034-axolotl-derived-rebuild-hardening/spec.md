# Feature Specification: Axolotl Derived Rebuild Hardening

**Feature Branch**: `034-axolotl-derived-rebuild-hardening`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement the next Tranche C slice by hardening rebuild so missing derived metadata is regenerated locally before link backfill"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rebuild Restores Missing Derived Metadata (Priority: P1)

As an Aegis maintainer, I want rebuild to restore missing derived `subject` and `summary` fields for legacy active memories so maintenance can recover incomplete rows without re-ingest.

**Why this priority**: Axolotl is about rebuild/regeneration, and missing derived metadata currently leaves legacy data underpowered during maintenance.

**Independent Test**: Seed active memories with missing `subject` and `summary`, run rebuild, and verify those fields are backfilled deterministically.

**Acceptance Scenarios**:

1. **Given** an active memory has no `subject`, **When** rebuild runs, **Then** Aegis derives and persists a normalized fallback subject.
2. **Given** an active memory has no `summary`, **When** rebuild runs, **Then** Aegis derives and persists a fallback summary.

### User Story 2 - Rebuild Enables Link Recovery After Metadata Hardening (Priority: P1)

As a maintainer, I want rebuild to recover missing same-subject structure after derived metadata is restored so legacy rows can participate in current Weaver backfill rules.

**Why this priority**: Restoring metadata only matters if rebuild can then regenerate the derived structure that depends on it.

**Independent Test**: Seed same-scope memories with missing subjects, run rebuild, and verify rebuild both backfills the subjects and restores same-subject links.

**Acceptance Scenarios**:

1. **Given** legacy same-scope memories share the same derived subject but currently store no subject, **When** rebuild runs, **Then** Aegis backfills the subject and restores `same_subject` links.

### User Story 3 - Preserve Explicit Metadata And Workflow State (Priority: P2)

As a maintainer, I want rebuild hardening to avoid overwriting explicit metadata and to keep GSD + Spec Kit state aligned to this feature.

**Why this priority**: Hardening should be conservative, and the tranche should remain reviewable through repo artifacts.

**Independent Test**: Run the prerequisite check and confirm it resolves to `034-axolotl-derived-rebuild-hardening` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** an active memory already has a non-empty explicit subject, **When** rebuild runs, **Then** that explicit subject remains unchanged.
2. **Given** the rebuild hardening feature is active, **When** I run the prerequisite check, **Then** it resolves to `034-axolotl-derived-rebuild-hardening`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `AegisApp.rebuild()` MUST backfill missing derived `subject` values for active memories before link backfill runs.
- **FR-002**: `AegisApp.rebuild()` MUST backfill missing derived `summary` values for active memories before link backfill runs.
- **FR-003**: Rebuild MUST NOT overwrite non-empty explicit `subject` or `summary` values.
- **FR-004**: Rebuild response payload MUST report how many memories had derived fields backfilled.
- **FR-005**: Python integration tests MUST cover derived-field rebuild recovery and same-subject link recovery after hardening.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `034-axolotl-derived-rebuild-hardening` feature.
- **FR-007**: Validation evidence MUST show the canonical prerequisite workflow and regression checks passing for the feature.

### Key Entities

- **Derived Rebuild Hardening**: A conservative rebuild step that regenerates missing derived metadata without mutating explicit non-empty fields.
- **Legacy Active Memory**: An existing active row whose derived metadata is incomplete because it predates current ingest guarantees or was manually altered.
- **Rebuild Recovery Count**: The number of active memories whose derived fields were backfilled during one rebuild run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running rebuild on legacy rows fills missing derived `subject` and `summary` fields.
- **SC-002**: Running rebuild after derived-field hardening restores same-subject links for eligible legacy rows.
- **SC-003**: The prerequisite check resolves to `034-axolotl-derived-rebuild-hardening` with its `tasks.md` artifact present.
