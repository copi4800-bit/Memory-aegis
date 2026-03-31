# Feature Specification: Semantic Recall Core

**Feature Branch**: `035-semantic-recall-core`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Aegis can recall related meaning even when wording changes materially. Implement Oracle Beast bounded inside retrieval as optional semantic recall over local memory."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Meaning-based Recall (Priority: P1)

As a user, I want Aegis to find memories that mean the same thing as my query, even if they use different words, so that I don't have to remember exact phrasing.

**Why this priority**: This is the core "semantic" value. Lexical search (FTS) is already implemented; this slice adds the "meaning" layer.

**Independent Test**:
1. Store a memory: "Tôi thích ăn phở bò."
2. Query: "I enjoy Vietnamese beef noodle soup."
3. Verify that the memory is returned via semantic recall even with zero lexical overlap.

**Acceptance Scenarios**:

1. **Given** a memory exists with specific wording, **When** I query with a synonym or paraphrased meaning, **Then** Aegis returns the memory via the `Oracle Beast` retrieval stage.
2. **Given** no exact lexical match exists, **When** semantic recall is enabled, **Then** Aegis still finds related memories instead of returning an empty list.

---

### User Story 2 - Optional Semantic Toggle (Priority: P2)

As a user, I want to choose when to use semantic recall so that I can still perform precise lexical searches or save on API/compute costs when meaning-based expansion isn't needed.

**Why this priority**: Users need control over "hallucinated" or "loose" matches. Semantic recall might be more expensive or slower than local FTS.

**Independent Test**:
1. Perform a search with `semantic=false`.
2. Perform the same search with `semantic=true`.
3. Verify that results differ and semantic recall only appears in the latter.

**Acceptance Scenarios**:

1. **Given** the search API is used, **When** `semantic` flag is `false`, **Then** only lexical and graph-based expansion results are returned.
2. **Given** the search API is used, **When** `semantic` flag is `true`, **Then** `Oracle Beast` semantic expansion is included.

---

### User Story 3 - Bounded Retrieval Performance (Priority: P2)

As a maintainer, I want semantic recall to stay within the `retrieval` module boundaries and not degrade the system's local-first speed significantly.

**Why this priority**: Aegis is "Local-First". If semantic recall is slow or requires heavy dependencies, it must be handled gracefully (e.g., via background or optional paths).

**Independent Test**: Measure the latency of a search with and without semantic expansion.

**Acceptance Scenarios**:

1. **Given** a large local memory base, **When** semantic recall is triggered, **Then** it does not block the main process or cause excessive timeouts.
2. **Given** the system is offline, **When** a semantic search is attempted, **Then** it fails gracefully or falls back to lexical search with a clear reason.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the `Oracle Beast` role within the `retrieval` module.
- **FR-002**: The `Oracle Beast` MUST provide optional semantic recall capability.
- **FR-003**: The `Oracle Beast` SHOULD use LLM-based query expansion or embedding-based vector search (depending on the available local environment).
- **FR-004**: Results from semantic recall MUST be tagged with the `semantic_recall` retrieval stage and a clear reason.
- **FR-005**: Semantic recall MUST be toggleable via the search query parameters.
- **FR-006**: The system MUST preserve the six-module architecture and NOT leak `retrieval` logic into other modules.
- **FR-007**: Semantic recall results MUST be blended with lexical and graph expansion results using a consistent scoring mechanism.

### Key Entities

- **Oracle Beast**: The role responsible for translating meaning into retrieval candidates.
- **Semantic Recall Result**: A search result found via meaning-based matching rather than lexical overlap.
- **Semantic Query**: An enhanced version of the user query that captures intent and related concepts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Semantic recall finds relevant memories with < 10% lexical overlap in test cases.
- **SC-002**: Search API supports a `semantic` boolean flag.
- **SC-003**: Latency for semantic search is documented and within acceptable bounds for the chosen implementation (e.g., < 2s for LLM-based expansion).
- **SC-004**: Regression tests verify that existing lexical and graph expansion continue to work correctly.
