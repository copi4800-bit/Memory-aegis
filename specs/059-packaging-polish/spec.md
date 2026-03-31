# Feature Specification: Packaging Polish

**Feature Branch**: `059-packaging-polish`  
**Created**: 2026-03-28  
**Status**: Implemented  
**Input**: Improve Aegis packaging so the shipped release bundle and published package feel newcomer-usable, not just source-complete.

## User Scenarios & Testing

### User Story 1 - Release Bundle Feels Ready To Try (Priority: P1)

As a newcomer, I want the local release bundle to include setup and demo artifacts, so I can unpack it and reach first value without reconstructing repo-only paths.

**Independent Test**: Create the release bundle and verify that it contains `aegis_py/`, `bin/aegis-setup`, `scripts/demo_first_memory.py`, and package guidance files.

### User Story 2 - README Explains What Packaging Includes (Priority: P1)

As a maintainer, I want the README release section to explain what ships and why, so packaging feels like part of the product story instead of a hidden helper script.

**Independent Test**: Read the README and verify that the release packaging section names the included newcomer-facing artifacts and the intended first steps.

### User Story 3 - Published Package Keeps First-Value Assets (Priority: P2)

As an integrator, I want the published npm package file list to preserve the Python runtime and demo assets, so the shipped package still reflects the Python-first product path.

**Independent Test**: Verify that `package.json` publishes the Python runtime, setup entrypoint, and first-value demo artifact.

## Requirements

- **FR-001**: The local release bundle MUST include the Python runtime, setup entrypoint, and one runnable first-value demo script.
- **FR-002**: The local release bundle MUST include one plain-text quickstart note for setup, demo, and validation.
- **FR-003**: The README MUST describe the shipped packaging contents in newcomer-facing language.
- **FR-004**: `package.json` MUST publish the Python-first runtime artifacts needed for setup and demo.
- **FR-005**: GSD and Spec Kit artifacts MUST record this packaging slice as the next product-polish execution feature.

## Success Criteria

- **SC-001**: A release tarball feels like something a newcomer can unpack and try immediately.
- **SC-002**: A maintainer can explain what ships in one short README section.
- **SC-003**: Packaging reinforces the Python-first product story instead of hiding it behind source-tree assumptions.
