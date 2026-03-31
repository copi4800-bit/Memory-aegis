# Feature Specification: Integration Story

**Feature Branch**: `060-integration-story`  
**Created**: 2026-03-28  
**Status**: Implemented  
**Input**: Make the thin-host integration path easier to understand by providing one runnable integration demo and one README section that explains the service-boundary flow with real commands.

## User Scenarios & Testing

### User Story 1 - Integrator Can See The Boundary In One Script (Priority: P1)

As an integrator, I want one runnable script that exercises `--service-info`, `--startup-probe`, and `--tool`, so I can see the Python-owned service boundary working end-to-end.

**Independent Test**: Run the integration demo script and verify that it prints the service descriptor, readiness probe, setup, remember, and recall results.

### User Story 2 - README Shows The Host Flow In Plain Language (Priority: P1)

As a maintainer, I want the README to explain the thin-host integration flow with real commands, so I can point host developers at one short section instead of several scattered notes.

**Independent Test**: Open the README and verify that it includes an integration quickstart section with the `--service-info`, `--startup-probe`, and `--tool` pattern.

### User Story 3 - Shipped Artifacts Preserve The Integration Demo (Priority: P2)

As a package consumer, I want the integration demo to ship in the published package and release bundle, so the integration story survives outside the source tree.

**Independent Test**: Verify that the package file list and release tarball both include the integration demo script.

## Requirements

- **FR-001**: The repo MUST include one runnable integration demo that exercises the Python-owned service boundary.
- **FR-002**: The README MUST describe the integration quickstart using real commands and the current local service contract.
- **FR-003**: The published package MUST include the integration demo script.
- **FR-004**: The release bundle MUST include the integration demo script.
- **FR-005**: GSD and Spec Kit artifacts MUST record this slice as the current integration/polish execution feature.

## Success Criteria

- **SC-001**: An integrator can understand the boundary by running one script.
- **SC-002**: The README exposes a concise, copy-pasteable host integration path.
- **SC-003**: The integration story stays grounded in the shipped Python-owned contract.
