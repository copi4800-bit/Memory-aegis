# Feature Specification: Aegis v7 Runtime

**Feature Branch**: `069-aegis-v7-runtime`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User description: "Implement Aegis v7 runtime architecture from 11.md with immutable evidence log governance, validation and policy gate, memory state machine, specialized storage surfaces, governed background intelligence, and retrieval orchestrator in the Python-owned runtime."

## User Scenarios & Testing

### User Story 1 - Trusted Admission Pipeline (Priority: P1)

As an operator, I want every admitted memory to pass through immutable evidence capture and a validation gate so weak extraction cannot silently become durable truth.

**Why this priority**: This is the core safety contract of v7. Without it, the rest of the architecture is cosmetic.

**Independent Test**: Ingest one strong fact and one weak fact, then verify evidence exists for both while only the strong fact is admitted into active retrieval.

**Acceptance Scenarios**:

1. **Given** a new memory candidate with raw evidence, **When** the ingest flow runs, **Then** the raw evidence is written first and remains queryable even if admission fails.
2. **Given** a candidate below confidence threshold, **When** the validation gate evaluates it, **Then** the candidate stays blocked from retrieval and a governance event explains why.
3. **Given** a candidate that conflicts with existing evidence, **When** the validation gate evaluates it, **Then** the memory enters a review-oriented state instead of silently becoming normal validated memory.

---

### User Story 2 - Explicit Memory State Governance (Priority: P1)

As a maintainer, I want memories to move through explicit v7 states with audit history so lifecycle changes can be explained, reviewed, and rolled back.

**Why this priority**: v7 requires a real state machine, not flat storage with implicit interpretation.

**Independent Test**: Persist a validated memory, transition it through archival behavior, and verify the state history is recorded.

**Acceptance Scenarios**:

1. **Given** a newly admitted memory, **When** it is stored, **Then** its explicit v7 state is persisted alongside the existing runtime metadata.
2. **Given** a memory changes lifecycle status, **When** the runtime applies the change, **Then** the state transition is recorded with reason and timestamp.
3. **Given** governance inspection is requested, **When** the runtime returns the audit view, **Then** state transitions and governance events are visible without reading raw database rows manually.

---

### User Story 3 - Orchestrated Retrieval And Shadow Background Planning (Priority: P2)

As an agent host, I want retrieval to assemble a ranked view from specialized storage surfaces while background intelligence only produces shadow proposals unless explicitly promoted.

**Why this priority**: This delivers the operational behavior promised by the v7 diagram without letting autonomous jobs mutate memory blindly.

**Independent Test**: Query a scope with multiple memory types and confirm the retrieval bundle is ranked and filtered by allowed states; then run background planning and verify only working-copy proposals are created.

**Acceptance Scenarios**:

1. **Given** a retrieval query, **When** the orchestrator runs, **Then** it returns a ranked memory view using only allowed memory states.
2. **Given** active memories with duplicate or stale patterns, **When** background planning runs, **Then** it emits proposals recorded as working-copy runs rather than mutating stored memories directly.
3. **Given** governance inspection after background planning, **When** the operator checks the scope, **Then** the planning artifacts are discoverable.

### Edge Cases

- What happens when a memory has evidence but the evidence link is later missing from metadata?
- How does the runtime behave when an archived memory is inspected through governance but should remain excluded from normal active retrieval?
- What happens when background planning finds no useful proposals in a scope?

## Requirements

### Functional Requirements

- **FR-001**: The system MUST persist raw evidence in an append-only evidence log before a new memory is admitted.
- **FR-002**: The system MUST evaluate new memory candidates through a validation and policy gate that can block, validate, or route to hypothesized review state.
- **FR-003**: The system MUST persist an explicit `memory_state` for v7 with at least `draft`, `validated`, `hypothesized`, `consolidated`, `invalidated`, and `archived`.
- **FR-004**: The system MUST record state transitions with reason, actor, timestamp, and optional evidence reference.
- **FR-005**: The system MUST record governance events for admission and validation outcomes.
- **FR-006**: The system MUST expose specialized storage surfaces for fact storage, vector candidate inspection, and graph traversal support.
- **FR-007**: The system MUST expose a retrieval orchestrator that returns only allowed memory states in the ranked runtime view.
- **FR-008**: The system MUST provide governed background intelligence planning that records shadow proposals without mutating durable memory directly.
- **FR-009**: The Python-owned runtime surface MUST report version `7.x` after this upgrade.
- **FR-010**: The feature MUST include automated tests covering admitted memory, blocked memory, state transition audit, and shadow background planning.

### Key Entities

- **Evidence Event**: Immutable raw capture for a memory candidate, including source, scope, and raw content.
- **Governance Event**: Audit record describing why admission or background decisions occurred.
- **Memory State Transition**: Durable record of movement between v7 memory states.
- **Background Intelligence Run**: Shadow-only proposal emitted by a governed worker for later review.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every admitted memory created through normal ingest has linked evidence and at least one recorded state transition.
- **SC-002**: Blocked memories leave evidence and governance records without appearing in active retrieval.
- **SC-003**: Governance inspection can show admission and transition history for a memory in one runtime call.
- **SC-004**: Background planning creates only shadow proposals and zero direct memory mutations in its default mode.
