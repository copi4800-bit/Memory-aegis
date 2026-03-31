# Implementation Plan: Governance Automation With Human Override

**Branch**: `043-governance-automation` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/043-governance-automation/spec.md`

## Summary

Implement Tranche B of the Aegis Completion Program. Move beyond bounded suggestion-first automation to a governed autonomous system. This requires introducing a `PolicyMatrix` to define which actions are allowed to execute automatically, enforcing confidence gates for operations like auto-resolve, and building a robust audit and rollback system for all autonomous decisions.

## Technical Context

**Language/Version**: Python 3.13.x
**Primary Dependencies**: `aegis_py/storage` and `aegis_py/replication`
**Storage**: SQLite (enhancing schemas for autonomous audit logs and policy storage)
**Testing**: `pytest` for policy logic, rollback integrity, and audit assertions.
**Target Platform**: Current OpenClaw/MCP runtime
**Project Type**: Memory engine (Governance capabilities)
**Constraints**: Must never perform destructive actions silently. Explanations for automation must be recorded.
**Scale/Scope**: Impacts all mutation paths that can potentially be automated (archive, resolve, consolidate).

## Constitution Check

- **Local-First Memory Engine**: Pass. Automation policies operate locally.
- **Brownfield Refactor Over Rewrite**: Pass. Expanding existing conflict and hygiene systems.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Extended to Explainable Mutations (Audit-first explanations).
- **Safe Memory Mutation By Default**: Pass. Governance explicitly enforces safe bounds.
- **Measured Simplicity**: Pass. Policy matrix is declarative and straightforward.

## Project Structure

### Documentation (this feature)

```text
specs/043-governance-automation/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Execution task list
```

### Source Code

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── governance/             # New module
│   │   ├── __init__.py
│   │   ├── policy.py           # PolicyMatrix definition and storage
│   │   ├── automation.py       # Executor for autonomous actions with gates
│   │   └── rollback.py         # Reversal logic based on audit IDs
│   ├── storage/
│   │   └── schema.sql          # Update to support autonomous_audit_log and policies
└── tests/
    └── governance/
        ├── test_policy.py      # Tests for policy evaluation
        ├── test_automation.py  # Tests for gated execution and explanations
        └── test_rollback.py    # Tests for state reversal
```

## Validation Plan

- Verify that `PolicyMatrix` correctly blocks disabled autonomous operations.
- Test that every executed autonomous operation generates an entry in the `autonomous_audit_log` with an explanation payload.
- Create integration tests where an autonomous consolidation is executed, then explicitly rolled back, asserting that the database state returns to exact equality with the pre-action state.
- Validate that confidence gates properly reject low-confidence automated conflict resolutions.