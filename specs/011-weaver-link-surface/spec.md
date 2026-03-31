# Feature Specification: Weaver Link Surface

**Feature Branch**: `011-weaver-link-surface`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Implement real Weaver code in Aegis using GSD + Spec Kit so explicit memory relations exist in the Python runtime and host surfaces"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persist Explicit Memory Relations (Priority: P1)

As an Aegis maintainer, I want to create explicit links between memories so the Weaver beast exists as real code instead of only an architecture note.

**Why this priority**: The repo already has a `memory_links` table. What is missing is a Python-owned workflow to create and inspect those links.

**Independent Test**: Store two memories in the same scope, create a link between them, and verify the link is persisted and retrievable.

**Acceptance Scenarios**:

1. **Given** two memories in the same scope, **When** I create a relation, **Then** Aegis persists the link with type, weight, and metadata.
2. **Given** a memory with linked neighbors, **When** I inspect neighbors, **Then** Aegis returns linked memory payloads with link metadata and scope-safe results.

### User Story 2 - Use Explicit Links In Retrieval And Visualization (Priority: P1)

As a host integrator, I want lexical-first retrieval and visualization to surface explicit links so relationship-aware memory works without inventing a new cloud dependency.

**Why this priority**: Weaver should improve retrieval context and graph visibility, not just add another hidden table.

**Independent Test**: Create linked memories, build a context pack from a lexical seed, and verify linked neighbors can appear as explainable expansion results. Also verify visualization includes explicit link edges.

**Acceptance Scenarios**:

1. **Given** a lexical seed result has explicit linked neighbors, **When** I build `memory_context_pack`, **Then** linked neighbors may be added after lexical hits and are tagged as link-driven expansion.
2. **Given** linked memories exist, **When** I call `memory_visualize`, **Then** the response includes explicit relation edges in addition to contradiction edges.

### User Story 3 - Expose Weaver Through Public Surfaces (Priority: P2)

As an external host or operator, I want MCP, CLI, and TypeScript adapter access to link creation and neighbor inspection so Weaver is available outside direct Python imports.

**Why this priority**: Aegis is being shaped as a host-agnostic memory engine, so new Python-owned memory semantics need a public surface.

**Independent Test**: Invoke link creation and neighbor listing through MCP/CLI/TS routing and verify the payloads are stable JSON objects.

**Acceptance Scenarios**:

1. **Given** the Python runtime is active, **When** I call `memory_link_store` and `memory_link_neighbors`, **Then** the payloads are available through MCP, CLI, and the TS adapter.

### Edge Cases

- Linking memories across different scopes must fail clearly to avoid leakage.
- Duplicate links should update or reuse the unique relation instead of creating ambiguous duplicates.
- Retrieval expansion must stay lexical-first and must not return link-only results when there is no lexical seed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST provide a Python-owned way to create or upsert explicit memory links using the existing `memory_links` storage table.
- **FR-002**: Aegis MUST provide a Python-owned way to inspect linked neighbors for a memory.
- **FR-003**: Link creation MUST reject cross-scope relations.
- **FR-004**: `memory_context_pack` MUST remain lexical-first and MAY use explicit links only after lexical seed recall succeeds.
- **FR-005**: `memory_visualize` MUST include explicit relation edges when they are present in the selected node set.
- **FR-006**: The public contract MUST expose link operations through Python app, MCP, CLI, and TypeScript adapter surfaces.
- **FR-007**: Repo docs and feature artifacts MUST be updated through GSD + Spec Kit.

### Key Entities

- **Memory Link**: A typed explicit relation between two stored memories in the same scope.
- **Linked Neighbor**: A memory returned through explicit relation traversal from a seed memory.
- **Weaver Surface**: The public Python-owned operations that create and inspect explicit links.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A contributor can create and inspect explicit memory links through the Python runtime without editing the database manually.
- **SC-002**: `memory_context_pack` can surface explicit linked neighbors while keeping lexical-first ordering.
- **SC-003**: MCP/CLI/TS paths expose link creation and neighbor inspection without diverging from Python-owned semantics.
