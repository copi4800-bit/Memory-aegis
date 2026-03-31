# Feature Specification: Aegis Python vNext Memory Engine

**Feature Branch**: `001-aegis-vnext-memory-engine`  
**Created**: 2026-03-23  
**Status**: Draft  
**Input**: User description: "Dua tren roadmap trong 12.md va codebase aegis_py hien tai, xay dung spec goc cho Aegis Python vNext theo huong refactor, harden, va productize memory engine."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scope-Safe Explainable Retrieval (Priority: P1)

As an OpenClaw or MCP-based agent, I want Aegis to return the most relevant memories for the current scope with a clear explanation so that I can trust the retrieved context and avoid pulling in unrelated or conflicting memories.

**Why this priority**: Retrieval quality is the core value of the product. If Aegis cannot retrieve the right memory for the right scope and explain why, the rest of the system has little product value.

**Independent Test**: This can be fully tested by seeding scoped memories with known provenance and conflict states, running retrieval queries, and verifying returned ranking, explanation fields, and leakage behavior without relying on hygiene or profile features.

**Acceptance Scenarios**:

1. **Given** active memories from project, session, and global scopes, **When** a scoped query is executed for a project context, **Then** Aegis returns project-relevant results first and does not leak unrelated memories from other scopes by default.
2. **Given** a retrieved memory with source metadata and score contributions, **When** the result is returned to a caller, **Then** the response includes explanation fields describing source, scope, and ranking reasons.
3. **Given** an active memory that has an open conflict, **When** it appears in retrieval results, **Then** the result marks the conflict state and does not hide that ambiguity from the caller.

---

### User Story 2 - Safe Memory Lifecycle And Hygiene (Priority: P2)

As a maintainer of a long-lived local memory store, I want working memory, archival, decay, and conflict workflows to be bounded and auditable so that memory quality improves over time without destructive automation.

**Why this priority**: Once retrieval exists, the next source of failure is memory drift and store pollution. Safe lifecycle behavior is necessary for long-term use and maintainability.

**Independent Test**: This can be tested by creating working, episodic, semantic, and procedural memories with different activation levels and conflict relationships, then running lifecycle and hygiene operations and validating status transitions, timestamps, and provenance preservation.

**Acceptance Scenarios**:

1. **Given** active `working` memories bound to a closed session, **When** session conclusion runs, **Then** low-value working memories expire and high-value working memories are archived or demoted according to policy.
2. **Given** two memories that contradict each other on the same subject, **When** hygiene or conflict analysis runs, **Then** Aegis records a conflict or suggestion without silently deleting or overwriting either memory.
3. **Given** a memory selected for archival or supersession, **When** the mutation is applied, **Then** the original provenance and lifecycle history remain traceable.

---

### User Story 3 - Product-Grade Local Engine Surface (Priority: P3)

As a developer integrating Aegis into OpenClaw or an MCP workflow, I want a compact, reliable local engine surface with stable storage, tests, and operational tooling so that I can install, run, debug, and evolve it confidently.

**Why this priority**: Aegis must become a maintainable product, not just an experimental codebase. Clear runtime surfaces and disciplined testing make the engine usable in real workflows.

**Independent Test**: This can be tested by initializing a local SQLite-backed instance, exercising the Python entrypoints and MCP-facing operations, and validating that key workflows work end-to-end with repeatable tests and benchmark fixtures.

**Acceptance Scenarios**:

1. **Given** a fresh local database, **When** Aegis initializes, stores memories, and executes retrieval, **Then** the workflow succeeds without cloud dependencies.
2. **Given** the Python CLI or MCP integration surface, **When** a caller requests store, search, or maintenance operations, **Then** the interface responds consistently and maps cleanly to the underlying memory services.
3. **Given** a code change affecting schema, retrieval, or lifecycle behavior, **When** project tests and benchmarks run, **Then** regressions are visible before release.

---

### Edge Cases

- What happens when a query has no lexical matches but the scope is valid and the caller still expects an explainable empty result?
- How does the system handle memories with missing or partial provenance fields imported from older data?
- What happens when a memory belongs to a session that has ended but was also reinforced enough to remain useful?
- How does retrieval behave when relevant memories are marked `conflict_candidate`, `superseded`, `archived`, or `expired`?
- What happens when two scopes both contain relevant memories and `include_global` or equivalent fallback behavior is enabled?
- How does the system prevent FTS-only ranking from over-promoting stale or high-conflict memories?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST operate as a local-first memory engine using SQLite and FTS5 as the default storage and retrieval path.
- **FR-002**: The system MUST support four public memory types in v1: `working`, `episodic`, `semantic`, and `procedural`.
- **FR-003**: The system MUST persist explicit scope fields for each memory, including at least `scope_type` and `scope_id`, with optional session affinity for working memory.
- **FR-004**: The system MUST persist provenance for each memory, including `source_kind`, optional `source_ref`, and timestamps sufficient for audit and explanation.
- **FR-005**: The system MUST return explainable retrieval results that include the selected memory, a score, and human-readable reasons describing why the memory ranked.
- **FR-006**: The system MUST apply scope-aware retrieval filters so that callers can constrain results to the current session, task, project, user, agent, or global scope as defined by the active query contract.
- **FR-007**: The system MUST surface conflict state in retrieval results when a returned memory is linked to an open or unresolved contradiction.
- **FR-008**: The system MUST maintain lifecycle state for memories, including at least `active`, `archived`, `expired`, `conflict_candidate`, and `superseded`.
- **FR-009**: The system MUST support bounded working-memory lifecycle handling, including session conclusion flows that expire or demote working memories according to policy.
- **FR-010**: The system MUST preserve provenance and traceability when applying archival, supersession, or conflict-related mutations.
- **FR-011**: The system MUST detect and record potential conflicts between memories that refer to the same subject or incompatible facts, while avoiding silent destructive resolution by default.
- **FR-012**: The system MUST expose a compact Python integration surface for local app, CLI, and MCP-based usage without embedding heavy domain logic directly into those entrypoints.
- **FR-013**: The system MUST keep storage, retrieval, hygiene, preference/profile, and integration concerns separable at the module level so that business semantics are not trapped in a single god-object.
- **FR-014**: The system MUST provide benchmark coverage for retrieval-impacting changes, including relevance, leakage, latency, and explanation completeness metrics.
- **FR-015**: The system MUST provide repeatable automated tests for schema, storage, retrieval, lifecycle, and integration-critical behavior.
- **FR-016**: The system MUST remain usable without cloud APIs; optional semantic enhancements MUST degrade gracefully when unavailable.
- **FR-017**: The system MUST treat contextual, temporal, social, and preference nuance as metadata or profile state in v1 rather than as additional public memory lanes.
- **FR-018**: The system MUST support future-safe schema evolution for retrieval explanations, memory links, conflict records, and lifecycle metadata.

### Key Entities *(include if feature involves data)*

- **Memory**: A stored memory record with type, scope, content, summary, subject, provenance, lifecycle state, confidence, activation data, and metadata.
- **Search Query**: The caller's retrieval request containing user query text, scope constraints, ranking thresholds, and optional global fallback behavior.
- **Search Result**: An explainable retrieval response containing the selected memory, score, explanation reasons, provenance, and conflict visibility.
- **Memory Link**: A directional relation between two memories such as `supports`, `contradicts`, `extends`, or `summary_of`.
- **Conflict Record**: A tracked contradiction or ambiguity between memories, including reason, score, status, and optional resolution metadata.
- **Lifecycle Event**: A logical state transition such as activation, archival, expiration, reinforcement, or supersession applied to a memory over time.
- **Style Signal / Profile**: Structured preference or style data extracted from interaction patterns and stored separately from the public memory type system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A seeded benchmark corpus can measure Recall@1, Recall@5, MRR@10, and nDCG@10 for the default retrieval pipeline on every retrieval-affecting change.
- **SC-002**: Scope leakage rate for the default retrieval path is reduced to a level accepted by the benchmark suite and does not regress unnoticed between change sets.
- **SC-003**: Conflict leakage is visible rather than silent: 100% of returned memories with known open conflicts expose that state in their retrieval output.
- **SC-004**: The default local store-search-maintain workflow succeeds end-to-end on a fresh SQLite database without requiring any cloud dependency.
- **SC-005**: Session lifecycle handling correctly transitions working memories in automated tests, with expected archival or expiration outcomes for benchmarked scenarios.
- **SC-006**: Retrieval responses for benchmark fixtures include explanation payloads judged complete by the test harness for source, scope, and ranking rationale.
- **SC-007**: Schema, retrieval, lifecycle, and integration-critical changes are covered by automated tests that fail on behavioral regressions before release.
