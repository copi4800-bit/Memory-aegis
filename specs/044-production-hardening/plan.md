# Implementation Plan: Production Hardening And SRE-Grade Guarantees

**Branch**: `044-production-hardening` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/044-production-hardening/spec.md`

## Summary

Implement Tranche C of the Aegis Completion Program. This phase now starts by restoring a fully green Python-owned runtime baseline, then hardens the engine through rigorous schema migration management, safe backup/restore drills utilizing SQLite's native backup API, formalized health states, and benchmark/regression gates.

## Technical Context

**Language/Version**: Python 3.13.x
**Primary Dependencies**: `sqlite3`, `pytest`
**Storage**: SQLite (leveraging `user_version` PRAGMA and native backup API)
**Testing**: `pytest` with a dedicated benchmark and stress-testing directory.
**Target Platform**: Current OpenClaw/MCP runtime
**Project Type**: Memory engine (Operational tooling)
**Constraints**: Backup processes must not lock the database, blocking concurrent reads/writes. Migrations must be declarative and incremental. TypeScript must remain an adapter and must not reclaim memory-domain ownership.
**Scale/Scope**: Impacts Python runtime semantics, DB initialization, backup scripts, test pipelines, and public surface alignment.

## Constitution Check

- **Local-First Memory Engine**: Pass. Formalizes offline "degraded" states as first-class operations rather than errors.
- **Brownfield Refactor Over Rewrite**: Pass. Expanding SQLite utilities rather than switching DBs.
- **Explainable Retrieval Is Non-Negotiable**: Pass. This tranche explicitly includes trust/conflict visibility and retrieval regression recovery because current failures show operations-only hardening is insufficient.
- **Safe Memory Mutation By Default**: Pass. Safe backups guarantee mutation recovery.
- **Measured Simplicity**: Pass. Using built-in SQLite backup APIs rather than complex third-party tools.

## Project Structure

### Documentation (this feature)

```text
specs/044-production-hardening/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Execution task list
```

### Source Code

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── operations/
│   │   ├── __init__.py
│   │   ├── backup.py          # Native SQLite backup and verify logic
│   │   ├── migration.py       # Versioned schema migration manager
│   │   └── health.py          # State tracking (HEALTHY, DEGRADED)
│   ├── retrieval/             # Semantic recall, trust shaping, bounded expansion fixes
│   ├── memory/                # Dedupe/correction/linking semantics
│   └── storage/
│       ├── migrations/        # Directory for sequential .sql migration scripts
│       └── manager.py         # Runtime-safe repair/migration integration
├── scripts/
│   └── aegis_backup.py        # CLI entry point for drills
├── src/
│   ├── python-adapter.ts      # Transitional adapter only
│   └── plugin.ts              # Transitional shell only
└── tests/
    ├── operations/
    │   ├── test_backup.py
    │   ├── test_migration.py
    │   └── test_health.py
    ├── retrieval/             # Semantic and trust regression gates
    └── benchmarks/            # Regression SLIs
        └── test_latency_sli.py
```

## Validation Plan

- Reproduce the current baseline with:
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`
- Recover the red Python cases before adding new surface area.
- Verify `backup.py` can clone a database successfully even while an active transaction is writing to it.
- Test the migration manager by bootstrapping an empty DB and a supported legacy DB, ensuring all scripts run in order and update `PRAGMA user_version`.
- Write tests that force the health state to `DEGRADED_SYNC` and assert that local SQLite writes still succeed instantly.
- Establish a benchmark and retrieval regression gate that fails on semantic/trust regressions as well as latency regressions.
