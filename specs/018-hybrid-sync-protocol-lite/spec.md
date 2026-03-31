# Feature Specification: Hybrid Sync Protocol Lite

**Feature Branch**: `018-hybrid-sync-protocol-lite`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add a file-based sync protocol lite for sync-eligible scopes using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export A Sync Envelope (Priority: P1)

As a maintainer, I want to export a file-based sync envelope for a `sync_eligible` scope so hybrid sharing can start without a cloud backend.

**Independent Test**: Mark a scope as `sync_eligible`, export an envelope, and verify it contains scope metadata and memory records.

### User Story 2 - Preview And Import A Sync Envelope (Priority: P1)

As a maintainer, I want to preview and import a sync envelope so I can reconcile local memory safely before mutating the DB.

**Independent Test**: Export from one DB, preview in another DB, import it, and verify records land in the local scope.

### Requirements *(mandatory)*

- **FR-001**: Aegis MUST export a file-based sync envelope for an explicit `sync_eligible` scope.
- **FR-002**: Aegis MUST preview an incoming sync envelope without mutating the DB.
- **FR-003**: Aegis MUST import an incoming sync envelope into the local DB when explicitly requested.
- **FR-004**: Local DB MUST remain source of truth; sync stays optional and file-based.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: A sync-eligible scope can be exported as a portable envelope file.
- **SC-002**: Another local runtime can preview and import that envelope safely.
