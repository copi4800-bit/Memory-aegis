# Feature Specification: V4 To V7 Migration Roadmap

**Feature Branch**: `062-v4-to-v7-migration-roadmap`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Convert the architecture proposal in [/home/hali/.openclaw/11.md](/home/hali/.openclaw/11.md) into an executable Spec Kit + GSD migration roadmap for Aegis v4 rather than leaving it as an isolated concept document.

## User Scenarios & Testing

### User Story 1 - Maintainer Can See What V7 Really Means For V4 (Priority: P1)

As a maintainer, I want a gap analysis that maps each major Aegis v7 architecture block to the current v4 codebase, so I can distinguish what already exists, what partially exists, and what is genuinely missing.

**Independent Test**: Read the roadmap and verify that it maps the major v7 components in `11.md` to concrete v4 modules and identifies gaps without hand-wavy rewrite language.

### User Story 2 - Team Can Migrate In Tranches Instead Of Rewriting (Priority: P1)

As a team, I want the v4 to v7 path split into ordered migration tranches, so we can execute toward v7 incrementally without breaking the stable local-first runtime already in production.

**Independent Test**: Read the roadmap and verify that it defines a tranche order, tranche goals, dependencies, and explicit stop/go boundaries between stages.

### User Story 3 - V7 Work Preserves Current Aegis Invariants (Priority: P1)

As a maintainer, I want the migration roadmap to lock non-negotiable invariants such as local-first control, scope isolation, explainability, and hygiene discipline, so v7 work does not regress the properties that already make v4 valuable.

**Independent Test**: Verify that the roadmap contains explicit invariants and anti-goals that rule out a rewrite-heavy or cloud-first interpretation of v7.

### User Story 4 - Planning Layer Knows What Comes After Productization (Priority: P2)

As a maintainer, I want `.planning/ROADMAP.md` and `.planning/STATE.md` to treat the v4 to v7 migration roadmap as the next major planning layer after the productization tranche, so repo planning stays coherent.

**Independent Test**: Verify that GSD planning artifacts reference this migration roadmap as the next architectural strategy layer after `061-citation-and-grounding-story`.

## Requirements

- **FR-001**: The repo MUST contain one migration roadmap feature that translates `11.md` into executable v4-to-v7 planning terms.
- **FR-002**: The roadmap MUST map the v7 architecture blocks to the current v4 codebase and classify each block as present, partial, or missing.
- **FR-003**: The roadmap MUST define an ordered tranche plan for reaching v7 without a full rewrite.
- **FR-004**: The roadmap MUST preserve Aegis invariants: local-first control, scope isolation, explainability, hygiene/lifecycle discipline, conflict awareness, and provenance discipline.
- **FR-005**: The roadmap MUST identify the first migration tranche that should actually be implemented next.
- **FR-006**: GSD planning artifacts MUST record this roadmap as the post-productization architectural strategy layer.

## Success Criteria

- **SC-001**: A maintainer can explain the v4-to-v7 path as an incremental migration instead of a rewrite.
- **SC-002**: The first implementation-ready tranche after this roadmap is obvious.
- **SC-003**: The repo no longer depends on `11.md` as an orphaned architecture note for v7 direction.
