# Feature Specification: Meaning Equivalence Merge

**Feature Branch**: `036-meaning-equivalence-merge`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Aegis stops storing multiple isolated memories that mean the same thing. Use Normalizer Beast + Weaver Beast + Librarian Beast for equivalence grouping and duplicate reduction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Semantic Deduplication on Ingest (Priority: P1)

As a user, when I tell Aegis something I've already said in a different way, I want it to recognize the duplication and update the existing memory instead of creating a new one.

**Why this priority**: Prevents immediate clutter and ensures the "most recent" version of a thought is preserved without fragmentation.

**Independent Test**:
1. Ingest: "I love eating pho."
2. Ingest: "Pho is my favorite food."
3. Verify that only one memory remains active or they are explicitly linked as equivalent, with the older one superseded or merged.

**Acceptance Scenarios**:

1. **Given** a memory already exists with a similar meaning, **When** a new similar memory is ingested, **Then** the engine detects the equivalence and avoids creating a redundant active record.
2. **Given** two memories are semantically equivalent, **When** they are merged, **Then** their activation scores and access counts are combined or updated to reflect the reinforcement.

---

### User Story 2 - Background Equivalence Consolidation (Priority: P2)

As a maintainer, I want Aegis to periodically scan the memory base and group existing equivalent memories that might have been missed during ingestion.

**Why this priority**: Handles "legacy" duplicates or those that were not caught due to high ingestion load or evolving semantic models.

**Independent Test**:
1. Store two paraphrased memories without the semantic deduplicator active.
2. Run the `hygiene` maintenance pass with the `Librarian Beast` active.
3. Verify that the two memories are now grouped or merged.

**Acceptance Scenarios**:

1. **Given** multiple equivalent memories exist in the database, **When** maintenance runs, **Then** the `Librarian Beast` identifies them and triggers a merge or grouping event.

---

### User Story 3 - Explainable Merges (Priority: P2)

As a user, I want to see why two memories were considered the same, so that I can trust the system isn't losing unique information by mistake.

**Why this priority**: Trust and explainability are core tenets of Aegis.

**Independent Test**:
1. Inspect a merged memory.
2. Verify its metadata contains a trace of the "source" memories and the reason for the merge.

**Acceptance Scenarios**:

1. **Given** a merged memory, **When** I inspect its metadata, **Then** I find references to the original superseded memory IDs and the equivalence reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the `Normalizer Beast` logic to include semantic hashing or intent-based canonicalization.
- **FR-002**: The `Weaver Beast` MUST be able to identify "equivalence" links between memories.
- **FR-003**: The `Librarian Beast` MUST manage the lifecycle of merging equivalent memories (superseding old ones, updating the master).
- **FR-004**: The ingest pipeline MUST check for semantic equivalence before final storage.
- **FR-005**: Merging MUST preserve provenance from all source memories.
- **FR-006**: The system MUST NOT merge memories if their subjects differ significantly, even if the content is similar.

### Key Entities

- **Equivalence Group**: A set of memory IDs that represent the same semantic fact.
- **Master Memory**: The currently active "best" representation of an equivalence group.
- **Superseded Memory**: An older or redundant representation that is no longer returned in primary searches but kept for history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of paraphrased duplicates are caught during ingestion in controlled test cases.
- **SC-002**: Maintenance pass reduces total active memory count by merging detected clusters.
- **SC-003**: Merged records include a `merged_from` list in their `metadata_json`.
