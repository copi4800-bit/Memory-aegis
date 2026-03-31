# Implementation Plan: Hybrid Memory Core

**Branch**: `007-hybrid-memory-core` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/spec.md)
**Input**: Feature specification from `/specs/007-hybrid-memory-core/spec.md`

## Summary

Reposition Aegis as a host-agnostic, local-first memory engine with a stable public memory surface, an optional sync policy layer, and a retrieval strategy that improves context packs for external model providers without making cloud dependencies mandatory.

## Technical Context

**Language/Version**: Python 3.13.x plus thin TypeScript host adapters  
**Primary Dependencies**: `aegis_py`, SQLite/FTS5, MCP integration, existing plugin bootstrap  
**Storage**: Local SQLite database as source of truth, filesystem backup artifacts, optional future sync metadata  
**Testing**: `pytest`, bootstrap integration tests, retrieval benchmark gates where ranking behavior changes  
**Target Platform**: Linux local runtime and host-integrated agent environments  
**Project Type**: Brownfield Python memory engine with adapter shells  
**Performance Goals**: Baseline local retrieval remains low-latency and offline-capable; hybrid design must not add mandatory network overhead to core operations  
**Constraints**: Local-first by default, explainable retrieval, migration-safe boundaries, no cloud-required baseline path  
**Scale/Scope**: Architecture and contract feature covering public surfaces, sync boundaries, and retrieval strategy for the next implementation wave

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. The plan treats sync as optional and keeps local SQLite/FTS5 as the baseline source of truth.
- `Brownfield Refactor Over Rewrite`: Pass. The work clarifies and refactors current boundaries rather than replacing the runtime.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Retrieval evolution is constrained to explainable lexical recall plus explicit relationship expansion.
- `Safe Memory Mutation By Default`: Pass. Hybrid design work is policy-first and avoids undocumented sync mutation semantics.
- `Measured Simplicity`: Pass with caution. The plan explicitly limits sync to an optional layer and rejects cloud-first drift.

## Project Structure

### Documentation (this feature)

```text
specs/007-hybrid-memory-core/
├── spec.md
├── plan.md
├── research.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── mcp/
├── retrieval/
├── storage/
└── ...

src/
├── python-adapter.ts
├── retrieval/
└── ...

tests/
test/integration/
```

**Structure Decision**: Keep the Aegis Python runtime as the semantic source of truth, use `app.py` and MCP surfaces as the public contract boundary, and treat the TypeScript plugin shell as a host adapter rather than a memory-domain owner.

## Phase Plan

### Phase 0 - Boundary Audit

Objective: Identify which current entrypoints are already public surfaces and which host or storage modules still leak internal semantics.

Expected outputs:

- documented public-vs-private boundary for `app.py`, `mcp/server.py`, `src/python-adapter.ts`, and storage helpers
- migration notes from "OpenClaw plugin" wording toward "AI memory engine" wording
- inventory of current host-coupled assumptions

### Phase 1 - Local-First Public Surface

Objective: Formalize a stable public memory surface for library and tool callers without breaking current host behavior.

Expected outputs:

- documented public operations for store/search/get/profile/backup/restore/list/preview
- contract rules for arguments, result shapes, provenance, and conflict visibility
- tests or contract fixtures that protect host-facing behavior

### Phase 2 - Hybrid Sync Policy Scaffold

Objective: Define the minimal schema and policy hooks needed for optional sync-eligible scopes while keeping local-only mode complete.

Expected outputs:

- scope classification model such as `local_only` and `sync_eligible`
- optional sync metadata boundary that does not become required for core runtime
- explicit non-goals for remote orchestration, multi-tenant cloud control planes, and mandatory hosted services

### Phase 3 - Mammoth Retrieval Evolution

Objective: Specify the retrieval flow that starts with lexical local recall, then optionally expands through explicit relationships to build explainable context packs for any host model.

Expected outputs:

- lexical-first retrieval flow
- relationship-expansion rules and ranking/explanation hooks
- benchmark expectations for any future ranking changes

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Optional sync policy layer in a local-first engine | Hybrid memory needs a clear trust boundary before implementation | Treating all memory as purely local would block future cross-device or shared-memory use cases |
| Public surface formalization across Python and host adapters | Aegis needs to serve multiple hosts without schema coupling | Letting each host import internals would preserve current ambiguity and break portability |

## Validation Plan

Before implementation work begins for this feature:

- confirm Spec Kit resolves to `007-hybrid-memory-core`
- keep `.planning/STATE.md` derivative of this spec while orchestration continues
- use the existing Python-first validation workflow as the baseline guardrail for any boundary changes

Implementation-time evidence to capture later:

- updated integration tests or contract tests for public memory surfaces
- retrieval benchmark evidence if ranking behavior changes
- migration notes showing current OpenClaw behavior remains supported while boundaries are cleaned up

## Validation Evidence

Observed on 2026-03-24:

- [research.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/research.md) now records how [1.md](/home/hali/.openclaw/1.md) maps into the active feature without replacing the constitution or active spec
- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now exposes `public_surface()` as the Python-owned description of the stable memory contract and ownership boundaries
- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now also exposes local-first scope sync-policy inspection with safe defaults and explicit `sync_eligible` scaffolding
- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now exposes `search_context_pack()` for host-ready lexical-first context assembly
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) now exposes `memory_surface`
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) now exposes `memory_scope_policy`
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) now exposes `memory_context_pack`
- [aegis_py/storage/schema.sql](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) and [aegis_py/storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) now persist optional scope policy metadata with a `local_only` default
- [aegis_py/retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) now keeps `memory_search` lexical-first while adding subject-based relationship expansion only for context-pack flows
- [aegis_py/retrieval/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py) and [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now emit `retrieval_stage` and `relation_via_subject` for explainable expansion
- [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) now route `memory_surface`, `memory_scope_policy`, and `memory_context_pack` through the Python-owned contract rather than adding host-only semantics
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json) now document the public boundary and runtime-readable contract surface
- [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py), [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py), and [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts) now protect public-surface, scope-policy, and Mammoth retrieval behavior

Validation results:

- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `16` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `69 passed in 2.00s`
