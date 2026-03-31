# Feature Specification: Production Observability

**Feature Branch**: `071-production-observability`  
**Created**: 2026-03-29  
**Status**: Draft  
**Input**: User description: "Make Aegis v7 observable enough that operators can see what happened, where it failed, and whether the runtime is degrading before it becomes dangerous."

## User Scenarios & Testing

### User Story 1 - Structured Runtime Events (Priority: P1)

As an operator, I want core runtime actions to emit a stable structured event shape so I can inspect behavior without grepping ad-hoc strings.

**Why this priority**: If the event contract is unstable, every later metric and alert becomes fragile.

**Independent Test**: Run an observability-focused test suite that proves core actions emit events with the agreed fields.

**Acceptance Scenarios**:

1. **Given** successful runtime actions, **When** observability events are recorded, **Then** each event includes `tool`, `scope_type`, `scope_id`, `session_id`, `latency_ms`, `result`, and `error_code`.
2. **Given** an action that returns no useful result or fails, **When** the event is emitted, **Then** the result classification remains explicit instead of falling back to ambiguous strings.

---

### User Story 2 - Operator Metrics Snapshot (Priority: P1)

As a maintainer, I want a process-local metrics snapshot so I can answer "how often" and "how slow" for core runtime actions.

**Why this priority**: Structured logs alone still make it tedious to answer operational questions during a bad day.

**Independent Test**: Run a focused suite that exercises several runtime actions and validates the metrics snapshot contract.

**Acceptance Scenarios**:

1. **Given** several successful runtime actions, **When** the metrics snapshot is read, **Then** counters and latency summaries exist per tool.
2. **Given** recent runtime activity, **When** the snapshot is read, **Then** the recent-event buffer preserves the newest events in bounded order.

---

### User Story 3 - Core Flow Instrumentation (Priority: P2)

As a system owner, I want the highest-signal flows instrumented first so observability starts helping now instead of waiting for a full rewrite.

**Why this priority**: Shipping narrow, real instrumentation beats designing a perfect telemetry system that never lands.

**Independent Test**: Run focused runtime tests that prove put/search/background/backup/restore paths update observability state.

**Acceptance Scenarios**:

1. **Given** memory write and retrieval flows, **When** they complete, **Then** the observability snapshot records them under their tool names.
2. **Given** governed background and recovery flows, **When** they complete, **Then** the snapshot distinguishes success from no-op or error outcomes.

## Requirements

### Functional Requirements

- **FR-001**: The runtime MUST define a stable structured event contract for core runtime actions.
- **FR-002**: The runtime MUST provide a process-local observability snapshot with counters, latency summaries, and recent events.
- **FR-003**: The feature MUST instrument at least these flows in this tranche: memory write, memory search, background plan/apply/rollback, backup create, restore preview, and restore apply.
- **FR-004**: The event contract MUST remain JSON-serializable and avoid dependence on external services.
- **FR-005**: The feature MUST keep observability bounded in memory so it remains safe for local runtime use.

## Success Criteria

- **SC-001**: Operators can inspect a stable snapshot after exercising core flows and see counts plus recent events without reading SQLite directly.
- **SC-002**: Observability-focused tests run green locally.
- **SC-003**: The runtime emits structured events for the targeted flows in this tranche.
