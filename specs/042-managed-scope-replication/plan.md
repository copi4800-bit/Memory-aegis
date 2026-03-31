# Implementation Plan: Managed Scope Replication And Operational Audit

**Branch**: `042-managed-scope-replication` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/042-managed-scope-replication/spec.md`

## Summary

Implement Tranche A of the Aegis Completion Program: a multi-node/replica identity model with replay-safe, scope-aware distributed sync and visible conflict resolution. This transitions the existing local-first file-based sync scaffolding into a robust, auditable multi-replica system while maintaining offline-first capabilities.

## Technical Context

**Language/Version**: Python 3.13.x (with OpenClaw/MCP runtime shell in TypeScript)
**Primary Dependencies**: Existing Python `aegis_py/` modules
**Storage**: SQLite (enhancing the existing `memory_aegis.db` schema)
**Testing**: `pytest` and integration tests for multi-node behavior
**Target Platform**: Current local-first OpenClaw/MCP runtime
**Project Type**: Memory engine (Platform capabilities)
**Constraints**: Must not violate local-first defaults. Must maintain migration paths. Must preserve safe memory mutation by default (no silent data overwriting on sync).
**Scale/Scope**: Distributed sync across multiple nodes, handling potential backlogs and replay safely.

## Constitution Check

- **Local-First Memory Engine**: Pass. Distributed capabilities are additive.
- **Brownfield Refactor Over Rewrite**: Pass. Expanding existing SQLite schema and sync layer.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Includes audit trails for sync provenance.
- **Safe Memory Mutation By Default**: Pass. Conflicts are flagged for review, never silently merged destructively.
- **Measured Simplicity**: Pass. Scope replication is scoped precisely to identity and sync.

## Project Structure

### Documentation (this feature)

```text
specs/042-managed-scope-replication/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Execution task list
```

### Source Code

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── replication/        # New module for sync policy, replay safety, and payloads
│   │   ├── __init__.py
│   │   ├── identity.py     # Node identity management
│   │   ├── sync.py         # Payload batching and idempotent application
│   │   └── conflict.py     # Conflict detection and resolution state
│   ├── models/
│   │   └── schema.py       # Updated to include sync audit/provenance fields
│   └── observability/
│       └── metrics.py      # Sync health reporting
└── tests/
    └── test_replication.py # Multi-node sync behavior tests
```

## Validation Plan

- Implement unit tests for node identity generation and validation.
- Implement integration tests mimicking two nodes syncing with interrupted/duplicated payloads to verify replay safety.
- Write tests asserting that conflicting concurrent mutations yield a `reconcile-required` state.
- Confirm backwards compatibility for existing SQLite instances via migration script tests.
