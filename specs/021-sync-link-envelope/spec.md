# Feature Specification: Sync Link Envelope

**Feature Branch**: `021-sync-link-envelope`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Extend sync envelopes to include Weaver links using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Links With The Scope Envelope (Priority: P1)

As a maintainer, I want sync envelopes to include explicit `memory_links` for the exported scope so Aegis can transfer relationship structure, not just raw memories.

**Independent Test**: Export a scope with explicit links and verify the envelope contains both memories and links.

### User Story 2 - Preview And Import Link Diffs (Priority: P1)

As a maintainer, I want sync preview/import to report link diffs and import links after memories so the Weaver graph survives transport.

**Independent Test**: Export linked scope data from one DB, preview in another DB, import it, and verify both records and links arrive.

## Requirements *(mandatory)*

- **FR-001**: Sync envelopes MUST include explicit `memory_links` whose endpoints belong to the exported scope.
- **FR-002**: Sync preview MUST report incoming and existing link counts.
- **FR-003**: Sync import MUST upsert links after importing memories.
- **FR-004**: Link sync MUST preserve local-first, file-based behavior.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: Scope envelopes carry both memory rows and link rows.
- **SC-002**: Importing an envelope restores syncable Weaver structure, not just text memories.
