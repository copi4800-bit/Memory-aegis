# Feature Specification: Semantic Memory Product Roadmap

**Feature Branch**: `035-semantic-memory-product-roadmap`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Use GSD + Spec Kit to define the next practical roadmap so Aegis can become more semantic, more accurate, and simpler for non-technical users without becoming bloated"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonical Post-034 Execution Order (Priority: P1)

As an Aegis maintainer, I want one canonical execution order after feature `034` so future work improves semantic memory quality and simple user experience without reopening the whole architecture.

**Why this priority**: The engine now has enough foundation that the next risk is direction drift, not missing scaffolding.

**Independent Test**: Review the roadmap and verify that it defines a bounded ordered sequence of the next product-facing slices.

**Acceptance Scenarios**:

1. **Given** a contributor wants to continue after `034`, **When** they read the roadmap, **Then** they can point to the next recommended slice and what comes after it.
2. **Given** a maintainer wants to avoid bloat, **When** they inspect the roadmap, **Then** they see a narrow sequence rather than a broad “build semantic AI” umbrella.

### User Story 2 - Product-Driven Slice Definitions (Priority: P1)

As a maintainer, I want the roadmap framed around product outcomes like remembering meaning, correcting mistakes, and staying simple so later features serve user value instead of internal jargon.

**Why this priority**: The user cares about “ngon, nhớ lâu, nhớ đúng” more than beast taxonomy.

**Independent Test**: Review the roadmap and confirm each proposed slice maps an internal capability to a concrete product outcome and an opening gate.

**Acceptance Scenarios**:

1. **Given** a contributor wants semantic improvement, **When** they inspect the roadmap, **Then** they find a bounded slice such as semantic recall, equivalence merge, or correction-first memory.
2. **Given** a contributor wants simplicity, **When** they inspect the roadmap, **Then** they find an explicit simple user surface slice instead of more raw tool growth.

### User Story 3 - Reconcile Workflow State (Priority: P2)

As a maintainer, I want the repo state and Spec Kit artifacts aligned to this product roadmap so the next tranche opens from a clean branch and feature contract.

**Why this priority**: The user asked to continue via GSD + Spec Kit, so the next direction must be tracked like the earlier slices.

**Independent Test**: Run the prerequisite check and confirm it resolves to `035-semantic-memory-product-roadmap` with task artifacts present.

**Acceptance Scenarios**:

1. **Given** the roadmap feature is active, **When** I run the prerequisite check, **Then** it resolves to `035-semantic-memory-product-roadmap`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repo MUST define a canonical post-`034` execution order for the next bounded slices that improve semantic memory quality and simple user experience.
- **FR-002**: The roadmap MUST define at least five but no more than seven recommended slices.
- **FR-003**: Each slice MUST include a product-facing outcome, primary internal capability, and an opening gate.
- **FR-004**: The roadmap MUST preserve the six-module runtime model and MUST NOT imply a large subsystem explosion.
- **FR-005**: The canonical beast architecture document MUST record the post-`034` roadmap in repo-tracked form.
- **FR-006**: `.planning/STATE.md` MUST be reconciled to the active `035-semantic-memory-product-roadmap` feature.
- **FR-007**: Validation evidence MUST show that the canonical prerequisite workflow resolves to the `035` feature.

### Key Entities

- **Product Slice**: A bounded implementation feature that maps one internal capability step to one user-visible memory outcome.
- **Semantic Recall Core**: The first slice that improves remembering by meaning instead of only by lexical overlap.
- **Simple User Surface**: A thin interaction layer that reduces memory actions to a small non-technical set such as remember, recall, correct, and forget.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The roadmap defines 5-7 ordered slices after `034`.
- **SC-002**: Each slice ties internal beast/module work to a user-facing outcome and an opening gate.
- **SC-003**: The prerequisite check resolves to `035-semantic-memory-product-roadmap` with its `tasks.md` artifact present.
