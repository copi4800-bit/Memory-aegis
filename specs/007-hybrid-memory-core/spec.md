# Feature Specification: Hybrid Memory Core

**Feature Branch**: `007-hybrid-memory-core`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Define a hybrid local-first memory architecture for Aegis with optional sync and host-agnostic API boundaries"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stable Local Core Boundary (Priority: P1)

As a host integrator, I want Aegis to define a stable local-first core and public memory surface so that OpenClaw, MCP clients, and future hosts can use the same memory semantics without importing private internals.

**Why this priority**: Without a clear public boundary, Aegis stays tightly coupled to one host and future hybrid or multi-host work remains fragile.

**Independent Test**: Review the architecture spec and plan, then verify the documented public surface, ownership boundaries, and non-goals are sufficient for a host to integrate without reading private storage helpers.

**Acceptance Scenarios**:

1. **Given** a new host wants to use Aegis, **When** it reads the feature artifacts, **Then** it can identify the stable public surfaces, required inputs, and expected outputs without depending on internal schema details.
2. **Given** an Aegis maintainer changes storage internals later, **When** the public contract stays stable, **Then** host adapters do not need a semantic rewrite.

---

### User Story 2 - Optional Hybrid Sync Model (Priority: P1)

As a maintainer, I want hybrid memory to be defined as local-first core plus optional sync so that Aegis can stay useful offline while still supporting remote backup or shared memory later.

**Why this priority**: "Hybrid" becomes dangerous if cloud behavior quietly becomes mandatory. The feature needs an explicit trust boundary before implementation.

**Independent Test**: Review the feature artifacts and confirm they define local-only behavior as the baseline, with sync as an optional layer and explicit scope/policy controls.

**Acceptance Scenarios**:

1. **Given** Aegis runs without network access, **When** a host stores, searches, or restores memory, **Then** the documented architecture still supports the full baseline workflow locally.
2. **Given** a future sync backend is enabled, **When** memory scopes are classified as local-only or sync-eligible, **Then** the architecture defines how those scopes are separated and governed.

---

### User Story 3 - Mammoth Retrieval Strategy (Priority: P2)

As a product designer, I want a documented retrieval strategy that combines exact local recall with lightweight relationship expansion so that Aegis can feed ChatGPT, Claude, Gemini, and other models better context without becoming another heavy reasoning engine.

**Why this priority**: Aegis only adds value if it improves context quality before the model call; hybrid architecture alone is not enough.

**Independent Test**: Review the feature artifacts and verify they define a retrieval flow that starts from local lexical recall, optionally expands through relationships, and returns explainable context packs.

**Acceptance Scenarios**:

1. **Given** a user query hits exact local memories, **When** Aegis builds a context pack, **Then** it first uses local lexical retrieval and only expands to related context through documented ranking rules.
2. **Given** a host model changes from GPT to Claude or Gemini, **When** the same Aegis memory store is used, **Then** the documented retrieval flow still produces host-agnostic context with provenance and conflict visibility.

---

### Edge Cases

- What happens when sync metadata exists but the remote backend is unavailable for an extended period?
- How does Aegis prevent a sync-enabled design from leaking private local-only scopes?
- What happens when local retrieval and remote-synced state disagree on version or mutation history?
- How does the architecture keep graph expansion explainable instead of returning arbitrary related noise?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST define a stable public memory surface that is host-agnostic and separate from private storage internals.
- **FR-002**: The baseline Aegis runtime MUST remain fully useful in local-only mode without requiring any network service.
- **FR-003**: Hybrid capability MUST be defined as an optional sync layer on top of the local-first core, not as a cloud-first dependency.
- **FR-004**: The architecture MUST classify memory scopes by sync eligibility, including at minimum local-only and sync-eligible behavior.
- **FR-005**: The feature artifacts MUST define where public semantics live across `app.py`, `mcp/`, host adapters, and storage modules.
- **FR-006**: Retrieval architecture MUST continue to prioritize explainable local recall before any relationship expansion or sync-aware enrichment.
- **FR-007**: The architecture MUST preserve provenance, lifecycle state, and conflict visibility across local and future sync-aware flows.
- **FR-008**: The feature MUST document non-goals that prevent Aegis from expanding into a general cloud orchestration platform.
- **FR-009**: The implementation plan MUST define a migration path from the current OpenClaw-first positioning toward a broader AI-memory-engine positioning without breaking current host behavior.

### Key Entities

- **Public Memory Surface**: The stable set of library methods and tools that outside hosts call to store, search, inspect, back up, and restore memory.
- **Local Memory Core**: The offline-capable runtime and storage layer that remains the source of truth for baseline Aegis behavior.
- **Sync Policy**: The rules that determine which scopes remain local-only and which scopes may participate in optional remote synchronization.
- **Context Pack**: The explainable retrieval payload that Aegis returns to a host model, including selected memories, provenance, and ranking reasons.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The feature artifacts define a public memory surface and module boundary clear enough that a new host integration can be planned without reading private storage helpers.
- **SC-002**: The feature artifacts define local-only baseline behavior and optional sync behavior without any requirement that baseline operations depend on a remote service.
- **SC-003**: The retrieval strategy in the feature artifacts explicitly documents lexical recall, relationship expansion, provenance, and conflict visibility as separate explainable steps.
- **SC-004**: The implementation plan and task list split the work into independently deliverable slices for public boundary cleanup, sync policy scaffolding, and retrieval evolution.
