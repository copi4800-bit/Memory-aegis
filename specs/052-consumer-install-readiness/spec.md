# Feature Specification: Consumer Install Readiness

**Feature Branch**: `052-consumer-install-readiness`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: The repo is consumer-complete for the current local-first runtime, but new users still need clearer install guidance and a direct answer about whether both the Python runtime and the OpenClaw plugin/bootstrap path are actually ready.

## User Scenarios & Testing

### User Story 1 - Understand Install Prerequisites Quickly (Priority: P1)

As a new user, I want one setup command to tell me whether Python, SQLite FTS5, Node, and npm are present, so I know whether Aegis can run and whether the plugin path is also ready.

**Independent Test**: Run the setup command and verify that it reports Python, SQLite FTS5, Node, and npm in plain language before onboarding continues.

### User Story 2 - Distinguish Runtime Readiness From Plugin Readiness (Priority: P1)

As a new user, I want setup to distinguish “core runtime is ready” from “OpenClaw plugin/bootstrap path is incomplete”, so I do not confuse a partial install with a broken engine.

**Independent Test**: Simulate missing Node or npm and verify that the install report marks the runtime usable while reporting plugin/bootstrap gaps clearly.

### User Story 3 - Follow One Short Quickstart (Priority: P2)

As a maintainer, I want the README to show one short quickstart for users who need both runtime and plugin path, so the install story is no longer implicit.

**Independent Test**: Inspect the README and verify that it includes a short `pip` + `npm` + `aegis-setup` quickstart.

## Requirements

- **FR-001**: `aegis-setup` MUST run an install preflight before onboarding.
- **FR-002**: The preflight MUST report Python and SQLite FTS5 as core runtime prerequisites.
- **FR-003**: The preflight MUST report Node and npm as plugin/bootstrap prerequisites.
- **FR-004**: The preflight MUST distinguish missing core runtime prerequisites from missing plugin/bootstrap prerequisites.
- **FR-005**: The README MUST publish a short quickstart covering the “use both” install path.
- **FR-006**: The feature MUST add tests for the install readiness report and README/install contract.

## Success Criteria

- **SC-001**: Running `aegis-setup` shows a plain-language install preflight before onboarding.
- **SC-002**: Missing Node or npm does not look like a broken Python runtime; it is reported as a plugin/bootstrap gap instead.
- **SC-003**: The README contains a short quickstart for users who need both Python runtime and plugin/bootstrap path.
