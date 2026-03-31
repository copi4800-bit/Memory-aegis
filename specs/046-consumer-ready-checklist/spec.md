# Feature Specification: Consumer Ready Checklist

**Feature Branch**: `046-consumer-ready-checklist`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User request to determine whether Aegis v4 is truly complete for non-technical users and to use Spec Kit as the source of truth.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Honest Readiness Assessment (Priority: P1)

As a maintainer, I want one explicit checklist for "consumer-ready" status so the team can stop making vague completion claims and judge the current repo against concrete criteria.

**Why this priority**: The repo already has strong runtime and test evidence, but "100% complete" is a product claim, not a code-count claim. That boundary must be written down before more implementation work starts.

**Independent Test**: Read the checklist artifact and verify that each criterion is concrete, observable in the repo, and clearly marked as met, partial, or missing.

**Acceptance Scenarios**:

1. **Given** the current repo state, **When** a maintainer reads the checklist, **Then** they can distinguish engine readiness from non-technical-user readiness.
2. **Given** a future claim that Aegis is "complete", **When** the checklist is consulted, **Then** the claim can be accepted or rejected without relying on chat history or intuition.

---

### User Story 2 - Consumer Journey Gap Mapping (Priority: P1)

As a product owner, I want the non-technical user journey broken into concrete gates such as onboarding, everyday actions, diagnostics, and recovery so remaining work can be sequenced by value.

**Why this priority**: The current runtime already supports memory operations, but the gaps are mostly in productization and usability. Those gaps need to be mapped in the same source of truth as the rest of the product.

**Independent Test**: Compare the checklist against the repo and verify that each gate points to concrete evidence or explicitly states that the capability is absent, partial, legacy-only, or developer-facing.

**Acceptance Scenarios**:

1. **Given** the current repo, **When** the product owner reviews the checklist, **Then** onboarding, simple usage, health reporting, and backup/recovery are assessed separately.
2. **Given** a capability exists only on a technical or legacy path, **When** the checklist records it, **Then** it is not counted as consumer-ready by default.

---

### User Story 3 - Sequenced Completion Tranches (Priority: P2)

As an implementation maintainer, I want the remaining work grouped into reviewable tranches so the team can improve readiness incrementally without reopening completion ambiguity.

**Why this priority**: The repo already uses Spec Kit heavily. A new readiness claim should be earned through bounded follow-up features, not by one broad "finish everything" statement.

**Independent Test**: Review the defined tranches and confirm that they can each become follow-up features under `specs/*` with their own code, tests, and closeout evidence.

**Acceptance Scenarios**:

1. **Given** the checklist and assessment, **When** a maintainer plans the next work, **Then** they can open a focused feature for the highest-value missing tranche.
2. **Given** some checklist items are already met, **When** the plan is reviewed, **Then** only unmet or partial items remain in the follow-up sequence.

### Edge Cases

- What happens when a capability exists in code but only on a retired or compatibility path? It must be marked as non-qualifying for consumer readiness.
- What happens when tests prove developer flows but not end-user flows? The checklist must mark the capability as partial rather than complete.
- What happens when README or chat claims conflict with the active repo evidence? The repo evidence and active feature artifacts win.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST define a bounded checklist for claiming Aegis v4 is ready for non-technical users.
- **FR-002**: The checklist MUST separate core engine readiness from consumer-product readiness.
- **FR-003**: The assessment MUST classify each checklist item using explicit states such as `MET`, `PARTIAL`, or `MISSING`.
- **FR-004**: The assessment MUST cite concrete repo evidence for each material claim, including code, tests, docs, or workflow artifacts.
- **FR-005**: Legacy compatibility surfaces or retired TypeScript engine paths MUST NOT count as consumer-ready capability by default.
- **FR-006**: The resulting plan MUST identify the minimum follow-up feature tranches required before Aegis may be called complete for non-technical users.
- **FR-007**: The feature MUST preserve the existing constitutional position that "100% complete" is a governed claim requiring explicit evidence, not a conversational judgment.

### Key Entities *(include if feature involves data)*

- **ConsumerReadyChecklistItem**: A concrete criterion for non-technical-user readiness with a name, description, qualification rule, and current state.
- **ReadinessAssessment**: The current repo-level judgment for each checklist item, including supporting evidence and a status of `MET`, `PARTIAL`, or `MISSING`.
- **CompletionTranche**: A bounded follow-up slice of work that can be opened as its own Spec Kit feature to close one or more checklist gaps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can read one feature artifact and determine whether Aegis v4 is consumer-ready without consulting chat history.
- **SC-002**: Every checklist item has an explicit current-state judgment and at least one repo evidence reference.
- **SC-003**: The assessment concludes with a defensible overall judgment on whether Aegis v4 is currently suitable for non-technical users.
- **SC-004**: The follow-up work is reduced to a finite set of reviewable tranches that can each become future features under `specs/*`.
