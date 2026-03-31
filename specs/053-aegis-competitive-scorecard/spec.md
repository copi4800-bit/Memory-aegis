# Feature Specification: Aegis Competitive Scorecard

**Feature Branch**: `053-aegis-competitive-scorecard`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Convert the seven product-critical Aegis criteria into a reusable scorecard that maintainers can apply across milestones.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer Can Judge Current Strength Honestly (Priority: P1)

As a maintainer, I want a written scorecard with explicit dimensions, scoring logic, and current judgments, so Aegis is evaluated against real product criteria instead of momentum or architecture vibes.

**Why this priority**: Without a scorecard, discussion about “Aegis is strong” remains too subjective and drifts between code health, research ambition, and product readiness.

**Independent Test**: Open the scorecard document and verify that all seven criteria are scored with explicit rationale, evidence references, and next moves.

**Acceptance Scenarios**:

1. **Given** the scorecard, **When** a maintainer reviews Aegis, **Then** they can see a numeric and narrative judgment for recall, scope isolation, conflict usefulness, explainability, hygiene payoff, product simplicity, and packaging/docs/onboarding.
2. **Given** a strong or weak score, **When** the maintainer reads that section, **Then** they can see why the score was assigned and what would improve it.

---

### User Story 2 - Future Milestones Can Be Judged Against the Same Bar (Priority: P1)

As a maintainer, I want the scorecard to define pass thresholds and a decision rule, so later milestones can be judged consistently rather than reinventing criteria each time.

**Why this priority**: Aegis needs a product bar, not only a feature backlog.

**Independent Test**: Verify that the scorecard includes threshold guidance and a bottom-line rule for when Aegis is merely “near-product” versus clearly superior.

**Acceptance Scenarios**:

1. **Given** the scorecard, **When** a maintainer plans future work, **Then** they can see which dimensions must reach `8+` for Aegis to count as clearly superior.

### Edge Cases

- A dimension can be technically impressive but still score below `8` if product payoff is not yet proven.
- A dimension can score well even if packaging is unfinished, but the overall judgment must still reflect the lagging adoption path.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST include a scorecard document that evaluates Aegis against seven specific dimensions: recall quality, scope isolation, conflict usefulness, explainability, hygiene/lifecycle payoff, product surface simplicity, and packaging/docs/onboarding.
- **FR-002**: Each dimension MUST include a current score, rationale, evidence references, and a next move.
- **FR-003**: The scorecard MUST define threshold guidance so maintainers can distinguish strong, usable, and weak dimensions.
- **FR-004**: The scorecard MUST define an overall decision rule for when Aegis can be described as clearly superior rather than merely near-product.

### Key Entities *(include if feature involves data)*

- **ScorecardDimension**: One of the seven product-critical evaluation axes, including score, status, rationale, evidence, and next move.
- **DecisionRule**: The threshold-based rule that determines whether Aegis is merely promising or genuinely superior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Maintainers can read one document and understand how Aegis currently scores on all seven product-critical dimensions.
- **SC-002**: The scorecard includes a clear threshold for what counts as genuinely strong versus merely usable.
- **SC-003**: The scorecard can be reused in future milestone reviews without redefining the evaluation framework.
