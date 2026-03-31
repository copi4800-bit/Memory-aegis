# Feature Specification: Default Surface Consistency

**Feature Branch**: `054-default-surface-consistency`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Preserve the product-surface simplicity score by removing inconsistencies in the governed consumer path, starting with `memory_setup` not being published consistently as a first-class default operation and extending to advanced host-surface drift where Python-owned operations were not fully published by the host adapter and shipped artifacts.

## User Scenarios & Testing

### User Story 1 - Default Operations Stay Explicit Everywhere (Priority: P1)

As a maintainer or host integrator, I want the default user path to be declared the same way across the Python surface, MCP server, host adapter, manifest/docs, and shipped artifacts, so ordinary-user flows do not depend on repo archaeology.

**Independent Test**: Inspect the Python public surface, MCP dispatch path, manifest, and shipped host adapter output and verify that the same default operations are published, including `memory_setup`.

### User Story 2 - Shipped Runtime Matches Source Truth (Priority: P1)

As a maintainer, I want the built `dist/` artifacts to expose the same default-surface behavior as the source files, so published packages do not lag behind the governed Python contract.

**Independent Test**: Import the built host adapter/runtime artifacts and verify that the Python-owned consumer surface, including advanced sync tools, is registered and bridged correctly.

### User Story 3 - Contract Tests Catch Future Drift (Priority: P2)

As a maintainer, I want tests to lock the default consumer operations list, so future surface drift is caught quickly instead of reappearing as product ambiguity.

**Independent Test**: Run the targeted contract tests and verify that they assert `memory_setup` inside the default consumer operations.

## Requirements

- **FR-001**: The Python public surface MUST publish `memory_setup` as part of `consumer_contract.default_operations`.
- **FR-002**: The Python MCP server MUST expose `memory_setup` as a first-class tool and route it through the Python-owned onboarding path.
- **FR-003**: The host adapter and shipped `dist/` artifacts MUST register the governed consumer surface published by Python, including `memory_setup` and any advanced operations surfaced to hosts.
- **FR-004**: Contract tests MUST lock both the default and advanced consumer operation lists against the Python public surface and host runtime registry.
- **FR-005**: The feature MUST preserve the existing advanced-tool availability and consumer-complete claim while reducing default-surface ambiguity.

## Success Criteria

- **SC-001**: The governed consumer surface appears in the same role across source contract files, manifest metadata, host-facing adapter code, and published artifacts.
- **SC-002**: Targeted runtime and contract verification demonstrates that `memory_setup` is callable as a first-class default operation and that advanced sync operations are published consistently.
- **SC-003**: The ordinary-user surface becomes more explicit without adding host-only semantics beyond the governed Python consumer path.
