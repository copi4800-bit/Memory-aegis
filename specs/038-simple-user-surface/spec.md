# Feature Specification: Simple User Surface

**Feature Branch**: `038-simple-user-surface`
**Status**: Implemented
**Input**: Roadmap 035 "Simple User Surface" slice.

## User Scenarios & Testing

### User Story 1 - Natural Interaction (Priority: P1)
As a non-technical user, I want to interact with my memory using simple verbs like "remember" and "recall" without worrying about technical parameters.

**Acceptance Scenarios**:
1. **Given** I tell Aegis to remember something, **When** I ask for it later, **Then** it provides the correct information in a simple format.

### User Story 2 - Easy Correction (Priority: P1)
As a user, I want a direct way to correct a mistaken or outdated memory.

**Acceptance Scenarios**:
1. **Given** Aegis has an old fact, **When** I use the `correct` action, **Then** the old fact is superseded and the new one takes precedence.

---

## Requirements

- **FR-001**: Implement `memory_remember`, `memory_recall`, `memory_correct`, `memory_forget`.
- **FR-002**: Hide technical fields (`scope_id`, `type`, etc.) from common user responses.
- **FR-003**: Provide human-readable, concise confirmation messages.

## Success Criteria

- **SC-001**: Users can perform all 4 actions via CLI and MCP with minimal arguments.
- **SC-002**: Integration tests pass for the new surface.
