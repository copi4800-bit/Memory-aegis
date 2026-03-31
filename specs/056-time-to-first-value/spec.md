# Feature Specification: Time To First Value

**Feature Branch**: `056-time-to-first-value`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Execute Tranche A from `.planning/AEGIS-ADOPTION-ROADMAP.md` so a new user can install Aegis, run setup, remember one thing, and recall it within minutes.

## User Scenarios & Testing

### User Story 1 - New User Reaches First Success Fast (Priority: P1)

As a new user, I want one short path from install to successful remember/recall, so I can feel Aegis working before I learn any advanced features.

**Independent Test**: Follow the quickstart from a clean local setup and verify that it leads through setup, one remember action, and one recall action in a few minutes.

### User Story 2 - The Beginner Path Avoids Operator Noise (Priority: P1)

As a new user, I want the first-run docs and setup flow to emphasize only the default consumer verbs, so I am not forced to parse backup, sync, graph, and maintenance tooling before I get value.

**Independent Test**: Inspect the beginner quickstart and verify that it centers on `memory_setup`, `memory_remember`, `memory_recall`, `memory_stats`, and `memory_profile` rather than advanced tools.

### User Story 3 - Maintainers Can Measure First-Value Quality Explicitly (Priority: P2)

As a maintainer, I want the feature to define evidence for “time to first value”, so later polish work can be judged against a concrete first-success bar.

**Independent Test**: Verify that the plan defines specific evidence targets for quickstart length, first-success flow, and beginner-facing docs.

## Requirements

- **FR-001**: The repository MUST publish one short beginner quickstart focused on setup plus one remember/recall success path.
- **FR-002**: The beginner path MUST use the governed default consumer surface and avoid requiring advanced operator tooling.
- **FR-003**: The feature MUST define evidence targets for first-value success, including setup, first memory write, and first recall.
- **FR-004**: GSD planning artifacts MUST record this slice as the first execution tranche under the adoption roadmap.

## Success Criteria

- **SC-001**: A new user can understand the shortest useful Aegis path without reading advanced-tool docs first.
- **SC-002**: The repo has one explicit first-success flow that demonstrates setup, memory write, and memory recall.
- **SC-003**: Future beginner-facing work can cite this feature as the governing first-value bar.
