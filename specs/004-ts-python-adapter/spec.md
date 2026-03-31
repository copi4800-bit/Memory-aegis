# Feature Specification: Aegis TypeScript Adapter To Python Engine

**Feature Branch**: `004-ts-python-adapter`  
**Created**: 2026-03-23  
**Status**: Implemented  
**Input**: User description: "Keep the TypeScript OpenClaw plugin as an adapter while routing canonical memory engine behavior to the Python backend"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - TS Plugin Uses Python Retrieval Core (Priority: P1)

As an OpenClaw user, I want the existing TypeScript plugin surface to use the Python memory engine for canonical retrieval behavior so that I can get the safer, better-tested Python retrieval path without losing the current plugin entrypoint.

**Why this priority**: This is the least risky migration path. It preserves the current OpenClaw-facing shell while replacing the most important internal behavior first.

**Independent Test**: This can be tested by exercising the existing TypeScript-facing tool surface and confirming that retrieval requests return data shaped by the Python engine contract.

**Acceptance Scenarios**:

1. **Given** the existing TypeScript plugin entrypoint, **When** a retrieval-oriented tool is invoked, **Then** the TypeScript layer delegates to the Python engine instead of maintaining a separate retrieval truth.
2. **Given** the Python engine returns scope, provenance, reasons, and conflict state, **When** the TypeScript adapter returns the result to OpenClaw, **Then** those fields remain visible or are mapped without loss of meaning.

---

### User Story 2 - TS Plugin Tool Parity Map (Priority: P2)

As a maintainer planning the migration, I want an explicit parity map between TypeScript plugin tools and Python engine capabilities so that I know which surfaces can be routed immediately and which still require Python work.

**Why this priority**: Without a parity map, migration work becomes guesswork and risks breaking tools that Python does not yet support.

**Independent Test**: This can be tested by documenting the current TypeScript tool surface, mapping it to Python capability status, and confirming that unsupported tools are explicitly marked rather than silently routed.

**Acceptance Scenarios**:

1. **Given** the TypeScript plugin manifest and tool registry, **When** migration planning is reviewed, **Then** each tool is marked as supported by Python, adapter-only, or still TypeScript-only.
2. **Given** a tool that Python does not yet support, **When** the migration adapter is defined, **Then** the unsupported status is explicit and not misrepresented as complete parity.

---

### User Story 3 - Incremental Replacement Strategy (Priority: P3)

As a maintainer, I want the migration strategy recorded in active artifacts so that future work can replace TypeScript piece by piece instead of attempting an unsafe full swap.

**Why this priority**: The repo currently has both implementations. A staged replacement plan is needed to avoid regressions and duplicate semantics.

**Independent Test**: This can be tested by ensuring the active plan and task artifacts describe a staged adapter strategy, explicit validation steps, and remaining gaps for the next migration wave.

**Acceptance Scenarios**:

1. **Given** the migration feature artifacts, **When** a future maintainer reads them, **Then** they can see which plugin surfaces are safe to route to Python now and which require follow-up parity work.

---

### Edge Cases

- What happens when the TypeScript plugin expects a tool result shape that the Python engine does not yet expose?
- How does the adapter behave when Python is available but a specific advanced TS-only tool has no Python equivalent yet?
- What happens when retrieval semantics diverge between TS and Python during the migration window?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The migration plan MUST preserve the current TypeScript OpenClaw plugin as the user-facing adapter during the initial replacement wave.
- **FR-002**: The migration plan MUST define which retrieval or memory surfaces should be routed to the Python engine first.
- **FR-003**: The project MUST document a tool parity map between the TypeScript plugin surface and Python engine capabilities.
- **FR-004**: The migration plan MUST make unsupported or TS-only tools explicit rather than implying full Python parity prematurely.
- **FR-005**: The active feature artifacts MUST describe an incremental replacement strategy and the validation evidence needed before removing TypeScript-owned behavior.

### Key Entities *(include if feature involves data)*

- **TS Adapter Surface**: The existing TypeScript plugin entrypoints and tool handlers exposed to OpenClaw.
- **Python Canonical Engine Surface**: The current Python app and MCP contracts that can serve as the new backend truth.
- **Parity Map**: The per-tool record of whether a TypeScript surface can be delegated to Python, remains TS-only, or requires follow-up parity work.
- **Migration Wave Record**: The feature artifact that records what has been routed, what remains, and what evidence is required before further replacement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can identify which current TypeScript plugin surfaces are safe to route to Python in the first migration wave.
- **SC-002**: The active feature artifacts clearly separate Python-backed tools from TS-only tools.
- **SC-003**: The migration strategy is staged and reviewable, rather than depending on a one-step TypeScript removal.
