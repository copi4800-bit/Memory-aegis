# Feature Specification: Resolution Decay Pragmatism

**Feature Branch**: `040-resolution-decay-pragmatism`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add user-guided hard conflict resolution, practical archive-first decay refinement, and SQLite-first graph pragmatism"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask The User On Hard Conflicts (Priority: P1)

As a user, when Aegis finds two high-confidence memories that truly disagree and cannot be resolved safely, I want it to pause and ask me for a bounded decision instead of silently guessing.

**Why this priority**: This is the highest-trust slice in `2.md`. It directly improves correctness and aligns with the constitution's suggest-first, log-first mutation rule.

**Independent Test**: Seed two same-subject, same-scope memories with a hard contradiction and no deterministic supersession rule, run conflict handling, and verify Aegis returns a bounded resolution prompt payload instead of auto-resolving.

**Acceptance Scenarios**:

1. **Given** two active memories in the same scope form a hard contradiction and both have high confidence, **When** conflict handling runs, **Then** Aegis MUST emit a user-resolution prompt payload instead of auto-resolving the pair.
2. **Given** a conflict has a deterministic resolution such as explicit correction or clear supersession, **When** conflict handling runs, **Then** Aegis MUST NOT ask the user unnecessarily.
3. **Given** the user selects a bounded resolution action, **When** Aegis records the decision, **Then** the chosen outcome and rationale MUST remain auditable.

---

### User Story 2 - Decay As Controlled Cooling, Not Silent Deletion (Priority: P1)

As a maintainer, I want memory decay to lower recall priority and transition memories toward cold, archived, or deprecated states without broad destructive deletion.

**Why this priority**: `2.md` explicitly treats practical decay as the next hygiene slice after trust. This improves long-term quality while preserving provenance and reducing over-filtering risk.

**Independent Test**: Seed memories with different ages, salience, reinforcement counts, and types, run maintenance, and verify the resulting lifecycle states and scores match the practical archive-first policy.

**Acceptance Scenarios**:

1. **Given** an old low-salience working memory, **When** decay runs, **Then** it MUST cool more aggressively than a stable semantic or procedural memory of the same age.
2. **Given** a durable identity or procedural memory, **When** decay runs, **Then** it MUST respect a stronger floor and avoid aggressive demotion.
3. **Given** a memory is recalled again, **When** reinforcement is applied, **Then** it MUST receive a bounded recovery boost rather than a runaway score reset.

---

### User Story 3 - Keep Graph Evolution SQLite-First (Priority: P2)

As a maintainer, I want graph capability to stay SQLite-first so Aegis can support bounded links and analysis without prematurely adopting a separate graph database.

**Why this priority**: `2.md` treats graph pragmatism as valuable but explicitly lower priority than conflict resolution and decay. It should remain an anti-overengineering guardrail unless relation pressure proves otherwise.

**Independent Test**: Verify that bounded link traversal and analysis remain available using the existing SQLite-backed graph structures without requiring Neo4j, FalkorDB, or another graph-native runtime.

**Acceptance Scenarios**:

1. **Given** the existing link and subject graph structures, **When** graph-oriented retrieval or analysis is needed, **Then** the default implementation MUST remain SQLite-backed.
2. **Given** maintainers need richer graph analysis during development, **When** they opt into in-memory analysis helpers, **Then** those helpers MUST remain optional and MUST NOT become the primary storage layer.

### Edge Cases

- What happens when a hard conflict spans different scopes but looks contradictory lexically?
- How does the system behave when a user-resolution prompt is stale because one side was superseded before the user answered?
- What happens when a memory is old but frequently recalled, and decay plus reinforcement compete?
- How does the system classify low-confidence contradictions that should remain visible but should not trigger user prompting?
- What happens when optional graph analysis helpers are unavailable in a local environment?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST classify unresolved same-scope contradictions into at least two buckets: deterministic resolution candidates and user-resolution candidates.
- **FR-002**: The system MUST trigger user-resolution only for bounded hard-conflict cases where both sides remain active, high-confidence, same-scope, and not deterministically resolvable.
- **FR-003**: A user-resolution payload MUST include the older memory, the newer memory, the conflict type, and bounded recommended actions.
- **FR-004**: The bounded user-resolution actions MUST include keeping the newer memory, keeping the older memory, preserving both memories under explicit scope separation, and marking an explicit exception when both can remain valid.
- **FR-005**: User-resolution outcomes MUST be recorded with provenance-preserving audit data and MUST NOT silently discard the losing memory without a traceable lifecycle event.
- **FR-006**: Decay MUST operate as archive-first lifecycle shaping: reduce recall priority first, then transition toward cold, archive-candidate, or deprecated-candidate states before any destructive deletion policy is considered.
- **FR-007**: Decay scoring MUST account for age, salience, reinforcement, and memory type or tier so durable semantic, identity-like, and procedural memories cool more slowly than volatile working memories.
- **FR-008**: Recall-driven reinforcement MUST remain bounded and MUST NOT fully erase age signals after one or two accesses.
- **FR-009**: The default graph/runtime storage model for this feature MUST remain SQLite-backed; this feature MUST NOT introduce Neo4j, FalkorDB, or another graph-native source of truth.
- **FR-010**: Any optional graph analysis helper added by this feature MUST remain local, bounded, and non-authoritative over stored link data.
- **FR-011**: The feature MUST preserve explainability in retrieval, conflict handling, and lifecycle transitions.
- **FR-012**: The feature MUST add or update tests for hard-conflict prompting behavior, practical decay behavior, and SQLite-first graph boundary behavior.
- **FR-013**: `.planning/STATE.md` MUST be reconciled to the active `040-resolution-decay-pragmatism` feature so GSD remains derivative of the spec.

### Key Entities *(include if feature involves data)*

- **Hard Conflict Candidate**: A same-scope contradictory pair that cannot be resolved safely by deterministic policy and therefore requires bounded user input.
- **Resolution Prompt Payload**: A structured, auditable packet containing the conflicting memories, conflict classification, and bounded next actions.
- **Decay Tier Policy**: A retention policy that shapes cooling speed and lifecycle transitions by memory type, salience, and reinforcement.
- **Graph Boundary Contract**: The rule that SQLite-backed links remain the source of truth while optional graph analysis stays non-authoritative.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Hard contradictions that meet the user-resolution criteria produce a bounded prompt payload in automated tests with no silent auto-resolution.
- **SC-002**: Deterministic correction or supersession cases continue resolving without user prompts in automated tests.
- **SC-003**: Practical decay tests show at least one volatile memory cooling faster than one durable memory of equal age while preserving archive-first behavior.
- **SC-004**: The active feature passes the canonical prerequisite check with `spec.md`, `plan.md`, and `tasks.md` present.
- **SC-005**: Validation evidence for this feature demonstrates Python regression coverage for the new conflict, decay, and graph-boundary behavior.
