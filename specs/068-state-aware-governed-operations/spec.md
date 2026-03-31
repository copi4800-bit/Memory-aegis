# Feature Specification: State-Aware Governed Operations

**Feature Branch**: `068-state-aware-governed-operations`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Turn tranche 068 into a concrete refactor map so governance/background work can land without app/storage/surface sprawl. Use the repo planning space and gSD style."

## User Scenarios & Testing

### User Story 1 - Maintainers Can Isolate Governed Runtime Surfaces (Priority: P1)

As a maintainer, I want the governance, background-operation, and operator-facing runtime paths to have explicit ownership boundaries so tranche `068` can land without deepening the existing `AegisApp` god-object pattern.

**Why this priority**: The runtime already works, but current architecture density makes the next tranche risky to extend.

**Independent Test**: Review the implementation plan and verify it defines bounded owners for app surfaces, governed operations, storage slices, and contract publication without reopening retired TypeScript engine semantics.

**Acceptance Scenarios**:

1. **Given** the current Python-owned runtime, **When** a maintainer reads the `068` spec and plan, **Then** they can identify which files and modules should own governed operations versus simple adapter glue.
2. **Given** the current `AegisApp` and `StorageManager` density, **When** the tranche is planned, **Then** the plan breaks work into small slices rather than a rewrite.
3. **Given** the existing CLI, MCP, TS adapter, and plugin manifest surfaces, **When** the tranche is planned, **Then** the plan preserves one semantic owner and treats other layers as derived adapters.

---

### User Story 2 - Operators Keep Stable Public Contracts While Internals Evolve (Priority: P1)

As an operator or host integrator, I want the current Python-owned tool payloads and health surfaces to remain stable while tranche `068` hardens internals, so architecture cleanup does not become a product regression.

**Why this priority**: The repo has already crossed the line where architectural cleanup can easily drift shipped behavior unless contracts are treated as first-class invariants.

**Independent Test**: Re-run the existing Python and host contract suites after each planned slice and verify that `status`, `doctor`, storage tools, sync tools, and background/governance tools keep their payload shape.

**Acceptance Scenarios**:

1. **Given** a runtime with current operator tools, **When** internals are refactored, **Then** the observable payload shapes remain stable.
2. **Given** the current health and storage surfaces, **When** internal helpers fail, **Then** status and doctor still degrade safely instead of crashing.
3. **Given** the TS host adapter, **When** new or refactored Python-owned tools ship, **Then** the host remains a thin bridge rather than re-owning semantics.

---

### User Story 3 - Future Tranches Can Build on Explicit Seams Instead of Duplication (Priority: P2)

As a future maintainer, I want one explicit contract registry and smaller runtime service seams so later work can add governed behavior, observability, and production discipline without repeating the same tool declarations and orchestration logic in multiple files.

**Why this priority**: Current duplication across `surface.py`, `mcp/server.py`, `src/python-adapter.ts`, `index.ts`, and `openclaw.plugin.json` is survivable now but expensive for follow-on tranches.

**Independent Test**: Inspect the plan and verify it defines a bounded path toward reducing duplicate contract publication and overgrown orchestration files.

**Acceptance Scenarios**:

1. **Given** a new Python-owned tool, **When** a maintainer follows the refactor map, **Then** they know the canonical definition point and the derived publication points.
2. **Given** governance and background logic need more state-aware behavior, **When** tranche `068` lands, **Then** follow-on work can extend dedicated services instead of stuffing more methods into `AegisApp`.

## Edge Cases

- What happens when architecture cleanup is attempted while the repo is already mid-tranche and tests are green?
- How do we split `AegisApp` and `StorageManager` without accidentally changing public payloads?
- How do we reduce contract duplication without reviving TypeScript-owned semantics?
- How do we add governed-operation seams while keeping storage fail-safe behavior for degraded runtime states?

## Requirements

### Functional Requirements

- **FR-001**: Tranche `068` MUST define explicit ownership boundaries for state-aware governed operations inside the Python runtime.
- **FR-002**: The implementation plan MUST treat `AegisApp` as an orchestration root, not the long-term home for every operator and governance method.
- **FR-003**: The implementation plan MUST define a bounded decomposition strategy for `StorageManager` that preserves a single SQLite connection owner while separating memory, evidence, governance, and storage-hygiene concerns.
- **FR-004**: The implementation plan MUST preserve the Python-owned public contract and treat CLI, MCP, TS adapter, and plugin manifest layers as derived adapters.
- **FR-005**: The implementation plan MUST identify duplicated contract publication as a real maintenance risk and define a bounded registry strategy to reduce drift.
- **FR-006**: The tranche MUST remain brownfield and compatibility-first; it MUST NOT propose a rewrite of the runtime or a return to a TypeScript-owned engine.
- **FR-007**: The tranche MUST keep current user-facing payload shapes and validation commands as first-class invariants during execution.
- **FR-008**: The tranche SHOULD identify a safe execution order that can be validated slice by slice with existing Python and host tests.

### Key Entities

- **Runtime Surface Facade**: A Python-owned module or service that exposes a coherent group of behaviors such as health, operator, backup, sync, or governed background actions.
- **Governed Operation**: A background, governance, or mutation-capable workflow that must consume explicit state, evidence, and policy while remaining explainable and bounded.
- **Contract Registry**: The canonical runtime-owned declaration of public tool names, parameter shapes, and ownership semantics from which adapter layers can derive their bindings.
- **Storage Slice**: A focused repository-style surface over the SQLite source of truth, such as memory rows, evidence rows, governance rows, or storage-hygiene operations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `specs/068-state-aware-governed-operations/spec.md` and `plan.md` define a concrete, bounded architecture path for governed operations instead of leaving tranche `068` empty.
- **SC-002**: The plan identifies at least three executable refactor slices that reduce architecture drag without broad rewrite scope.
- **SC-003**: The plan explicitly preserves the Python-owned runtime boundary and current validation command set.
- **SC-004**: The plan gives future tranche work a clear place to add governed behavior without increasing surface duplication.
