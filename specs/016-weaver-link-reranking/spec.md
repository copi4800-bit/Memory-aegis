# Feature Specification: Weaver Link Reranking

**Feature Branch**: `016-weaver-link-reranking`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Add better reranking for Weaver link expansion using GSD + Spec Kit"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rank First-Hop Above Second-Hop (Priority: P1)

As a host integrator, I want first-hop link expansions to rank above second-hop expansions when all else is similar so context packs stay focused.

**Independent Test**: Build `A -> B -> C` and verify `B` scores above `C`.

### User Story 2 - Prefer Stronger Link Types (Priority: P1)

As a maintainer, I want typed links such as `procedural_supports_semantic` to score more strongly than weaker generic links like `same_subject`.

**Independent Test**: Compare same-scope candidates connected with different link types and verify scores reflect the link-type policy.

## Requirements *(mandatory)*

- **FR-001**: Link expansion scoring MUST be centralized in a Python helper rather than hard-coded inline.
- **FR-002**: First-hop explicit link expansion MUST generally score above second-hop expansion when other signals are similar.
- **FR-003**: Link type MUST influence score.
- **FR-004**: Memory type and link weight MAY influence score in a bounded way.
- **FR-005**: Docs and workflow artifacts MUST be updated through GSD + Spec Kit.

## Success Criteria *(mandatory)*

- **SC-001**: Link reranking is more intentional and test-covered.
- **SC-002**: Context packs prioritize stronger and nearer link relationships.
