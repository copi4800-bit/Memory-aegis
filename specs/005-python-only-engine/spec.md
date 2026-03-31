# Feature Specification: Aegis Python-Only Runtime

**Feature Branch**: `005-python-only-engine`  
**Created**: 2026-03-23  
**Status**: Implemented  
**Input**: User description: "Remove the TypeScript runtime and ship a Python-only Aegis engine for OpenClaw"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Python Owns The Runtime Contract (Priority: P1)

As an OpenClaw user, I want the memory plugin runtime to be owned by the Python engine rather than the TypeScript implementation so that retrieval, storage, readback, maintenance, backup flows, and profile behavior all come from one canonical backend.

**Why this priority**: Without a single runtime owner, the product keeps two competing behaviors and any "migration" remains partial.

**Independent Test**: Enable the plugin in a clean workspace, run the core memory tools (`memory_search`, `memory_get`, `memory_store`, `memory_stats`, `memory_clean`, `memory_profile`, backup/restore surfaces, and remaining maintenance/inspection tools), and confirm the responses come from the Python engine without depending on TypeScript retrieval or storage logic.

**Acceptance Scenarios**:

1. **Given** a clean local workspace, **When** OpenClaw invokes the core memory tools, **Then** the Python engine handles those requests as the only source of domain behavior.
2. **Given** a retrieval or storage request, **When** the plugin returns a result, **Then** the result shape, provenance, and explanation fields come from the Python contract rather than the legacy TypeScript retrieval packet.
3. **Given** a memory citation, backup, diagnostics, taxonomy, scan, rebuild, or visualization request, **When** the plugin returns a result, **Then** that flow is served by a Python-owned surface or is explicitly rejected by Python rather than delegated to the TypeScript engine.

---

### User Story 2 - Python Packaging Replaces TypeScript Packaging (Priority: P2)

As a maintainer, I want the install and runtime packaging to target the Python engine directly so that the shipped artifact no longer depends on the TypeScript codebase for normal operation.

**Why this priority**: Removing runtime ambiguity requires packaging, startup, and validation flows to stop centering the TypeScript distribution.

**Independent Test**: Follow the repository quickstart on a fresh environment and verify that the published runtime path installs Python requirements, launches the Python entrypoint, and does not require the TypeScript build for the primary plugin behavior.

**Acceptance Scenarios**:

1. **Given** the release packaging workflow, **When** a maintainer prepares the plugin, **Then** the runtime artifact and instructions point to the Python-owned startup path.
2. **Given** the validation workflow, **When** contributors run the canonical checks, **Then** Python validation is the source of truth and TypeScript validation is either removed or clearly marked as transitional.

---

### User Story 3 - Legacy TypeScript Surface Is Explicitly Removed Or Quarantined (Priority: P3)

As a maintainer, I want the legacy TypeScript runtime surface either removed or reduced to a host-required bootstrap so that there is no hidden second engine left behind.

**Why this priority**: Leaving the old TS engine around as active code defeats the point of a Python-only migration and raises future regression risk.

**Independent Test**: Audit the runtime entrypoints and shipped files, then verify that TypeScript domain modules are no longer on the production path and any remaining non-Python code is documented as host bootstrap only.

**Acceptance Scenarios**:

1. **Given** the repository runtime entrypoints, **When** the migration is complete, **Then** no TypeScript module remains responsible for memory retrieval, storage, hygiene, or profile semantics.
2. **Given** an unavoidable host constraint, **When** a tiny non-Python bootstrap remains, **Then** it is documented as a compatibility loader rather than a second engine.

---

### Edge Cases

- What happens if the OpenClaw host contract only supports JavaScript plugin entrypoints and cannot invoke Python directly?
- How does the migration handle existing TypeScript-owned workspace data and database files so that Python becomes authoritative without silent data loss?
- What happens when the Python runtime is unavailable or dependencies are missing on a machine that previously only needed the TypeScript build?
- How does the project prevent a fallback path from quietly reactivating TypeScript retrieval or storage logic after the migration lands?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The production memory runtime MUST be owned by `aegis_py` for core behaviors including store, search, memory readback, status, hygiene, backup/restore, and profile retrieval.
- **FR-002**: The repository MUST define one canonical startup path for OpenClaw that launches the Python engine directly or through a host-supported compatibility bootstrap that contains no memory-domain logic.
- **FR-003**: The migration MUST remove or quarantine TypeScript modules that currently implement memory retrieval, storage, maintenance, profiling, or other domain semantics so they are not active runtime owners.
- **FR-004**: The release packaging and contributor quickstart MUST describe Python-first installation and validation as the canonical workflow.
- **FR-005**: The project MUST preserve local-first operation with SQLite/FTS5 and must not introduce a cloud dependency as part of removing TypeScript.
- **FR-006**: Any remaining non-Python bootstrap code MUST be explicitly documented as a host integration constraint rather than hidden runtime logic.
- **FR-007**: The migration MUST record and validate the host-loading constraint for OpenClaw because the current repository appears to load the plugin through a JavaScript entrypoint.
- **FR-008**: The migration MUST keep retrieval explanation and provenance fields intact after the TypeScript runtime path is removed.
- **FR-009**: The Python runtime MUST expose a stable `memory_get`-equivalent readback surface so the host bootstrap does not need TypeScript file/node read logic for memory citations.
- **FR-010**: The Python runtime MUST expose backup and restore entrypoints suitable for the host bootstrap, even if the host still presents them through compatibility tool names.
- **FR-011**: The Python runtime MUST expose stable entrypoints for maintenance and inspection surfaces currently named `memory_doctor`, `memory_taxonomy_clean`, `memory_rebuild`, `memory_scan`, and `memory_visualize`, so the host bootstrap no longer needs the legacy TypeScript engine for those requests.

### Key Entities *(include if feature involves data)*

- **Python Runtime Surface**: The Python app, MCP server, CLI, and packaging path that will become the only canonical runtime owner.
- **Host Bootstrap Contract**: The minimum integration layer OpenClaw requires to load the plugin, whether fully Python-native or a documented compatibility shim.
- **Legacy TypeScript Runtime Surface**: The current `src/`, `index.ts`, build outputs, and package metadata that presently host plugin behavior.
- **Migration Evidence Record**: The spec-kit artifacts that document what was removed, what remains, and why.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can point to one Python-owned runtime path for the primary memory tools without a competing TypeScript engine on the production path.
- **SC-002**: The canonical validation workflow passes using Python-first checks, and any remaining TypeScript checks are non-runtime or removed.
- **SC-003**: Core user-facing memory flows remain operational after the migration and preserve explanation, provenance, and scope behavior.
- **SC-004**: The repository clearly documents whether zero-TypeScript runtime was achieved or whether a host-mandated bootstrap remains, with no ambiguity about ownership.
