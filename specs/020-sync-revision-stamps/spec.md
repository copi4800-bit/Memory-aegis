# Feature Specification: Sync Revision Stamps

**Feature Branch**: `020-sync-revision-stamps`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add lightweight revision stamps for sync scopes using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Scope Revision Stamps (Priority: P1)

As a maintainer, I want sync envelopes to carry a scope revision stamp so another runtime can compare envelope freshness without relying only on per-record timestamps.

**Independent Test**: Export a sync envelope and verify it includes the current local scope revision.

### User Story 2 - Preview And Import With Revision Awareness (Priority: P1)

As a maintainer, I want sync preview and import to report local and incoming scope revisions so reconcile decisions are clearer.

**Independent Test**: Advance one target scope locally, preview an older envelope, and verify revision mismatch is surfaced.

## Requirements *(mandatory)*

- **FR-001**: Aegis MUST persist a lightweight local revision counter per scope.
- **FR-002**: Scope revision MUST be included in sync envelopes.
- **FR-003**: Sync preview MUST report `incoming_scope_revision` and `local_scope_revision`.
- **FR-004**: Sync preview MUST use scope revision to surface revision mismatch in addition to record-level diffing.
- **FR-005**: Sync import MUST return the post-import scope revision.
- **FR-006**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: Sync envelopes carry portable revision stamps.
- **SC-002**: Preview/import results expose local versus incoming scope revision clearly.
