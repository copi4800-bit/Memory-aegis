# Feature Specification: Evidence Log Foundation

**Feature Branch**: `063-evidence-log-foundation`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Open the first implementation tranche from `062-v4-to-v7-migration-roadmap` by introducing the immutable evidence backbone proposed in `/home/hali/.openclaw/11.md` without destabilizing the current retrieval/runtime surface.

## User Scenarios & Testing

### User Story 1 - Raw Evidence Survives Extraction Errors (Priority: P1)

As a maintainer, I want every new ingest path to preserve immutable raw evidence before memory normalization, so extraction mistakes do not erase the original source text.

**Independent Test**: Ingest a new memory through the canonical v4 path and verify that the original raw evidence is persisted in an append-only evidence table before or alongside the resulting memory record.

### User Story 2 - Memories Point Back To Evidence (Priority: P1)

As a maintainer, I want stored memories to retain a stable pointer to the evidence event or span that justified them, so provenance can later evolve from “free-form source_ref” into auditable evidence-backed traceability.

**Independent Test**: Store a memory and verify that the persisted memory record carries evidence linkage metadata without breaking the existing search/retrieval payload shape.

### User Story 3 - Existing Retrieval Surface Does Not Regress (Priority: P1)

As an integrator, I want the existing `memory_remember`, `memory_recall`, `memory_search`, and `memory_context_pack` surfaces to keep their current public shapes while evidence logging is introduced, so the first v7 tranche does not break OpenClaw or MCP clients.

**Independent Test**: Run the current Python and host contract tests and verify that existing retrieval and tool surfaces still pass after the evidence layer lands.

### User Story 4 - Evidence Is Append-Only By Contract (Priority: P2)

As a maintainer, I want the new evidence layer to be explicitly append-only and non-overwriting, so later policy/promotions can rely on evidence immutability instead of conventions.

**Independent Test**: Review the schema and persistence path and verify that evidence rows are written as new events rather than updated in place.

## Requirements

- **FR-001**: The storage layer MUST define an append-only evidence event store for raw evidence.
- **FR-002**: The canonical ingest path MUST persist evidence events before or alongside memory creation.
- **FR-003**: New memory records MUST retain evidence linkage fields or structured evidence metadata that can later support span binding.
- **FR-004**: The current public retrieval and tool payload shapes MUST remain backward-compatible during this tranche.
- **FR-005**: The evidence store MUST remain local-first and SQLite-native.
- **FR-006**: This tranche MUST avoid introducing the full v7 admission/state machine in the same slice.

## Success Criteria

- **SC-001**: A new memory can be traced back to immutable raw evidence stored locally.
- **SC-002**: Existing v4 retrieval and integration surfaces remain green after the evidence layer lands.
- **SC-003**: A follow-on tranche for promotion gating can assume that raw evidence already exists as a first-class store.
