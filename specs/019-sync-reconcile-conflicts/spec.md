# Feature Specification: Sync Reconcile Conflicts

**Feature Branch**: `019-sync-reconcile-conflicts`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add detailed reconcile preview/import for sync envelopes using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview Detailed Reconcile State (Priority: P1)

As a maintainer, I want sync preview to tell me which records are new, already present, only local, or revision-mismatched so I can judge import risk before mutation.

**Independent Test**: Build source/target scopes with overlapping and divergent records and verify preview returns categorized diffs.

### User Story 2 - Return Reconcile Stats On Import (Priority: P1)

As a maintainer, I want sync import to report how many records were inserted, replaced, or left untouched so the result is auditable.

**Independent Test**: Import an envelope into a partially populated target DB and verify reconcile stats are returned.

## Requirements *(mandatory)*

- **FR-001**: Sync preview MUST return `incoming_new`, `incoming_existing`, `local_only`, and `revision_mismatch` counts.
- **FR-002**: Revision comparison MUST use existing local `updated_at` versus incoming `updated_at`.
- **FR-003**: Sync import MUST return reconcile stats including inserted and replaced records.
- **FR-004**: The feature MUST preserve local-first, file-based sync behavior.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: Sync preview exposes actionable diff categories before import.
- **SC-002**: Sync import returns auditable reconcile outcomes instead of only a raw count.
