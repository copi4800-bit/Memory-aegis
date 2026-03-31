# Feature Specification: Python CLI Surface

**Feature Branch**: `009-python-cli-surface`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add a host-agnostic Python CLI surface for Aegis so external tools can use the public memory contract without OpenClaw"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Call Public Memory Surface From Shell (Priority: P1)

As an external tool integrator, I want a Python CLI for Aegis so I can store, search, inspect, and query memory state without needing OpenClaw or TypeScript adapters.

**Why this priority**: A host-agnostic memory engine needs at least one first-class public entrypoint outside the OpenClaw runtime.

**Independent Test**: Run the CLI against a temporary local DB and verify that core commands return the same contract payloads as the Python runtime.

**Acceptance Scenarios**:

1. **Given** a local Aegis database, **When** I run CLI commands for store/search/surface/status, **Then** they complete without requiring OpenClaw.
2. **Given** a new external host wants to script Aegis, **When** it uses the CLI, **Then** it can access the public contract through stable command names and JSON outputs.

---

### User Story 2 - Operational Workflows Via CLI (Priority: P1)

As a maintainer, I want backup, preview, restore, and scope-policy inspection reachable from the Python CLI so operational workflows are not trapped behind OpenClaw tooling.

**Why this priority**: The CLI must expose the parts of Aegis that prove it is a standalone memory engine, not just an embedded plugin component.

**Independent Test**: Run CLI backup/scope-policy commands against a temporary DB and verify payloads match the Python runtime contract.

**Acceptance Scenarios**:

1. **Given** a backup workflow, **When** I invoke the CLI, **Then** I can create backups and preview restore impact through JSON output.
2. **Given** sync-policy scaffolding exists, **When** I invoke the CLI, **Then** I can inspect scope policy without any remote backend.

---

### User Story 3 - Document Standalone Usage (Priority: P2)

As a future adopter, I want the README and feature artifacts to describe the Python CLI so I can understand how to use Aegis outside OpenClaw.

**Why this priority**: A standalone CLI only helps if users can discover it and trust that it is part of the supported public surface.

**Independent Test**: Review docs and confirm they show how to run the CLI and how it relates to the public memory contract.

**Acceptance Scenarios**:

1. **Given** a user reads the repo docs, **When** they look for standalone entrypoints, **Then** they can find the Python CLI and example commands.

---

### Edge Cases

- What happens when the CLI is pointed at a brand-new database path?
- How does the CLI behave when required arguments for scoped operations are only partially provided?
- What happens when backup preview or restore paths do not exist?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Aegis MUST expose a Python CLI entrypoint that works without OpenClaw.
- **FR-002**: The CLI MUST wrap existing Python-owned public surfaces instead of introducing divergent behavior.
- **FR-003**: The CLI MUST emit machine-readable JSON for command outputs that already return structured runtime payloads.
- **FR-004**: The CLI MUST support at minimum surface inspection, status, store, search, context-pack, backup upload, backup preview, and scope-policy inspection.
- **FR-005**: The feature MUST document how to invoke the CLI against a local database path.
- **FR-006**: Existing runtime and adapter behavior MUST remain unchanged.

### Key Entities

- **Python CLI Surface**: A command-line entrypoint that wraps the Python-owned public memory contract.
- **CLI Command Payload**: The structured output returned by a CLI command, typically as JSON for host scripting.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can invoke core Aegis memory commands from Python without OpenClaw.
- **SC-002**: CLI payloads remain aligned with the existing Python public surface and pass regression tests.
- **SC-003**: Repo docs describe standalone CLI usage clearly enough for a host integrator to script it.
