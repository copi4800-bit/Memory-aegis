# Feature Specification: Correction-First Memory Flow

**Feature Branch**: `037-correction-first-memory-flow`  
**Created**: 2026-03-24  
**Status**: Implemented  
**Input**: User description: "Newer correct information can supersede or amend older memory without leaving both active ambiguously. Use Meerkat, Consolidator Beast, and Constitution Beast policies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explicit Fact Correction (Priority: P1)

As a user, when I explicitly correct a fact (e.g., "My phone number is no longer X, it is Y"), I want Aegis to archive the old fact and make the new one the primary active memory for that subject.

**Why this priority**: Facts change over time. Keeping stale facts active leads to confusion and incorrect RAG context.

**Independent Test**:
1. Ingest: "My office is in Room 101." (Subject: `user.office`)
2. Ingest: "Actually, my office moved to Room 202."
3. Verify: `Room 101` memory is `superseded`, `Room 202` is `active`.

**Acceptance Scenarios**:

1. **Given** an active memory exists for a specific subject, **When** a new memory with a "correction signal" (e.g., "no longer", "instead of", "corrected to") arrives, **Then** the old memory is transitioned to `superseded` status.
2. **Given** a correction occurs, **When** I search for that subject, **Then** only the newest (corrected) memory is returned by default.

---

### User Story 2 - Automated Contradiction Resolution (Priority: P2)

As a system, when I detect a direct logical contradiction between a new memory and an old one, I want to prefer the newer one as the "truth" if the confidence is high.

**Why this priority**: Users don't always use explicit correction words. The system should infer intent from contradictions.

**Independent Test**:
1. Ingest: "Project X is cancelled."
2. Ingest (later): "Project X is active again."
3. Verify: `Meerkat` detects the contradiction and marks the older one as `superseded` due to temporal precedence.

**Acceptance Scenarios**:

1. **Given** two memories in the same subject share high lexical overlap but have opposing polarity (negation), **When** maintenance runs, **Then** the `Consolidator Beast` resolves the conflict by preferring the newer record.

---

### User Story 3 - Correction History (Priority: P2)

As a user, I want to be able to see the history of corrections so that I can track how a fact has evolved over time.

**Why this priority**: Auditability and lineage.

**Independent Test**:
1. Inspect the metadata of a corrected memory.
2. Verify it contains a `corrected_from` link to the previous version.

**Acceptance Scenarios**:

1. **Given** a memory was created as a correction, **When** I view its metadata, **Then** I see the ID of the memory it replaced and the reason for the correction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `IngestEngine` MUST detect explicit correction patterns (Regex-based for common triggers).
- **FR-002**: `Meerkat` (ConflictManager) MUST flag contradictions as "Correction Candidates" if they share the same subject and scope.
- **FR-003**: `Consolidator Beast` MUST implement a "Recency Preference" policy for resolving contradictions in the same subject.
- **FR-004**: Transitioning a memory to `superseded` MUST include an event reason: `corrected_by_newer_info`.
- **FR-005**: Search results MUST filter out `superseded` memories unless explicitly requested.

### Key Entities

- **Correction Signal**: A linguistic trigger indicating a change in state or fact.
- **Temporal Precedence**: A policy where newer data is trusted over older data for the same subject.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 80% of explicit corrections result in automatic status transition of the old memory.
- **SC-002**: `SearchPipeline` returns only the corrected version for common "state change" queries.
- **SC-003**: Metadata trace `corrected_from` is present in 100% of detected correction events.
