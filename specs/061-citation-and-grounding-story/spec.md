# Feature Specification: Citation And Grounding Story

**Feature Branch**: `061-citation-and-grounding-story`  
**Created**: 2026-03-28  
**Status**: Implemented  
**Input**: Close the current productization tranche by making Aegis trust/grounding visible through one runnable demo and one README section that explains citations, provenance, and explainability in product terms.

## User Scenarios & Testing

### User Story 1 - Maintainer Can Show Why Aegis Is Trustworthy (Priority: P1)

As a maintainer, I want one runnable demo that prints provenance, trust state, and ranking reasons, so I can show why an Aegis answer should be trusted instead of asking people to infer it from raw JSON.

**Independent Test**: Run the grounding demo and verify that it prints provenance, trust state, trust reason, and ranking reasons from the current runtime.

### User Story 2 - README Explains Grounding In Product Language (Priority: P1)

As a newcomer or evaluator, I want the README to explain what Aegis means by citations and grounding, so I can understand the trust story without reading the retrieval internals.

**Independent Test**: Open the README and verify that it includes a section describing provenance, ranking reasons, trust state, and context-pack grounding.

### User Story 3 - Shipped Assets Preserve The Trust Demo (Priority: P2)

As a package consumer, I want the grounding demo to ship in the package and release bundle, so the trust story survives outside the source tree.

**Independent Test**: Verify that the published package and release tarball both include the grounding demo script.

## Requirements

- **FR-001**: The repo MUST include one runnable demo for citations/provenance/trust output.
- **FR-002**: The README MUST explain Aegis grounding in terms of provenance, ranking reasons, trust state, and context-pack evidence.
- **FR-003**: The published package MUST include the grounding demo script.
- **FR-004**: The release bundle MUST include the grounding demo script.
- **FR-005**: GSD and Spec Kit artifacts MUST record this slice as the closing trust-oriented productization step for the current tranche.

## Success Criteria

- **SC-001**: A maintainer can demo why Aegis is grounded with one script.
- **SC-002**: The README makes the trust story understandable without overclaiming.
- **SC-003**: The current productization tranche can be closed after this slice without an obvious trust-story gap.
