# Implementation Plan: Aegis Python vNext Memory Engine

**Branch**: `001-aegis-vnext-memory-engine` | **Date**: 2026-03-23 | **Spec**: [`/home/hali/.openclaw/extensions/memory-aegis-v7/specs/001-aegis-vnext-memory-engine/spec.md`](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/001-aegis-vnext-memory-engine/spec.md)
**Input**: Feature specification from `/specs/001-aegis-vnext-memory-engine/spec.md`

**Note**: This plan is tailored to the current brownfield `aegis_py` codebase. The immediate goal is to harden and reshape the existing Python implementation into a stable local-first memory engine, not to perform a disruptive rewrite.

## Summary

Build Aegis Python vNext as a local-first, explainable memory engine by stabilizing the current SQLite/FTS5 core, unifying duplicated storage and retrieval semantics, strengthening lifecycle and conflict handling, and tightening the MCP/app integration surface around explicit service boundaries. The plan prioritizes scope-safe retrieval and explainability first, then lifecycle and hygiene correctness, then product-grade integration and benchmarking.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: Standard library `sqlite3`, current internal Python modules under `aegis_py`, existing dataclass/Pydantic-style models in memory/storage layers  
**Storage**: Local SQLite with FTS5  
**Testing**: Existing Python test suite under `tests/`; expected execution via `pytest`  
**Target Platform**: Local Linux/macOS developer environments and OpenClaw-hosted local agent runtimes  
**Project Type**: Local library + CLI/MCP integration surface  
**Performance Goals**: Retrieval remains interactive for local use; benchmark and track Recall@1/@5, MRR@10, nDCG@10, scope leakage, conflict leakage, latency p50/p95, and explain completeness  
**Constraints**: Offline-capable by default, no mandatory cloud dependency, behavior-preserving refactor in early phases, no destructive memory mutation by default  
**Scale/Scope**: Single local-user memory engine with durable long-lived memory store, multiple scopes, and product-grade maintainability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Local-First Memory Engine`: Pass. The current design already uses SQLite/FTS5 and must stay that way for the default path.
- `Brownfield Refactor Over Rewrite`: Pass with caution. Current code shows overlapping implementations in [`storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py), [`storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py), [`memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py), and [`retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py). Refactor must converge these paths without breaking public flows abruptly.
- `Explainable Retrieval Is Non-Negotiable`: Pass only if retrieval refactors preserve and improve ranking reasons, provenance, scope visibility, and conflict visibility.
- `Safe Memory Mutation By Default`: Pass only if hygiene, conflict, and lifecycle work remains suggestion-first and provenance-preserving.
- `Measured Simplicity`: Pass. This feature explicitly excludes full orchestration-platform scope and keeps focus on memory engine boundaries.

No constitutional violations are required at this stage. Complexity should be reduced, not justified upward.

## Project Structure

### Documentation (this feature)

```text
specs/001-aegis-vnext-memory-engine/
├── plan.md
└── spec.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── main.py
├── memory/
│   ├── core.py
│   ├── filter.py
│   ├── ingest.py
│   └── models.py
├── retrieval/
│   ├── benchmark.py
│   ├── models.py
│   └── search.py
├── storage/
│   ├── db.py
│   ├── manager.py
│   ├── models.py
│   ├── schema.py
│   └── schema.sql
├── hygiene/
│   └── engine.py
├── conflict/
│   └── core.py
├── preferences/
│   ├── extractor.py
│   └── manager.py
└── mcp/
    └── server.py

tests/
├── test_benchmark_core.py
├── test_hygiene.py
├── test_ingest.py
├── test_integration.py
├── test_memory_core.py
├── test_memory_lifecycle.py
├── test_preferences.py
├── test_retrieval.py
└── test_storage.py
```

**Structure Decision**: Keep the single Python project layout and refactor within the existing module boundaries. Introduce clearer service and repository seams only where needed, but avoid large path churn until behavior is stabilized and benchmarked.

## Phase Plan

### Phase 0 - Baseline Alignment And Gap Mapping

Objective: Establish a verified baseline of current behavior and pinpoint the boundary conflicts that block product-grade evolution.

Deliverables:

- Inventory current storage, retrieval, lifecycle, conflict, and MCP flows.
- Record overlap and divergence between:
  - [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
  - [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py)
  - [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)
  - [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)
- Confirm current schema coverage versus the v1 spec and constitution.
- Identify which existing tests are authoritative for current behavior.

Exit Criteria:

- We can describe the current end-to-end path for store, search, session lifecycle, hygiene, and MCP operations.
- We know which modules are canonical, redundant, transitional, or inconsistent.

### Phase 1 - Canonical Domain And Storage Contract

Objective: Define and enforce a single canonical domain/storage contract for memories, links, conflicts, statuses, and scope/provenance fields.

Workstreams:

- Align memory models used by storage and retrieval around one canonical contract.
- Reconcile schema definitions in SQL and Python wrappers so field names and lifecycle states are consistent.
- Standardize status values, provenance fields, and scope semantics required by the spec.
- Minimize god-object behavior by moving raw persistence concerns into storage-focused modules only.

Primary Files:

- [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql)
- [`aegis_py/storage/schema.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.py)
- [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py)
- [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [`aegis_py/memory/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/models.py)
- [`aegis_py/storage/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py)

Exit Criteria:

- Storage, retrieval, hygiene, and MCP layers all rely on a shared understanding of memory shape and status semantics.
- Schema and model inconsistencies no longer force translation hacks across the stack.

### Phase 2 - Retrieval Unification And Explainability

Objective: Converge the duplicated retrieval paths into one explainable, scope-safe retrieval pipeline.

Workstreams:

- Choose one canonical retrieval path and retire or adapt the competing one.
- Preserve FTS5 as the baseline search path while formalizing ranking, normalization, and explanation fields.
- Add explicit handling for scope filters, optional global fallback, stale-memory risk, and conflict visibility.
- Ensure the returned result contract is stable for both internal Python consumers and MCP-facing output.

Primary Files:

- [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)
- [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)
- [`aegis_py/retrieval/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py)
- [`aegis_py/memory/filter.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/filter.py)
- relevant tests under [`tests/test_retrieval.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py) and [`tests/test_benchmark_core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)

Exit Criteria:

- A single retrieval contract exists for scoped search.
- Results include stable explanation fields for score reasons, provenance, scope, and conflict state.
- Retrieval-impacting changes are benchmarkable.

### Phase 3 - Lifecycle, Hygiene, And Conflict Safety

Objective: Turn lifecycle and hygiene into explicit, bounded engine behavior rather than ad hoc side effects.

Workstreams:

- Separate decay, archival, session conclusion, and conflict workflows into clearer services or service-like modules.
- Ensure working-memory lifecycle behavior is explicit and test-covered.
- Make conflict detection and maintenance operations suggestion-first and audit-friendly.
- Preserve traceability for archived, expired, superseded, and conflict-candidate records.

Primary Files:

- [`aegis_py/hygiene/engine.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py)
- [`aegis_py/conflict/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py)
- [`aegis_py/evolve/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/evolve/core.py)
- lifecycle-related logic in [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)
- relevant tests under [`tests/test_hygiene.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_hygiene.py) and [`tests/test_memory_lifecycle.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_memory_lifecycle.py)

Exit Criteria:

- Session end behavior, decay, archival, and conflict handling are explicit, predictable, and covered by tests.
- No ambiguous destructive mutation occurs by default.

### Phase 4 - Integration Surface Hardening

Objective: Keep `app`, `main`, and MCP integration thin, stable, and aligned with canonical services.

Workstreams:

- Update MCP/server output to use the canonical retrieval and memory service contract.
- Remove domain duplication from integration entrypoints.
- Normalize JSON output, error handling, and empty-result behavior.
- Ensure local initialization and operational commands remain simple and cloud-free.

Primary Files:

- [`aegis_py/app.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)
- [`aegis_py/main.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/main.py)
- [`aegis_py/mcp/server.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)

Exit Criteria:

- External callers interact with a compact surface that reflects canonical engine behavior.
- Integration tests cover store, search, status, clean, and export workflows.

### Phase 5 - Benchmarks, Regression Gates, And Release Readiness

Objective: Make quality regressions visible before shipping changes.

Workstreams:

- Expand or stabilize benchmark fixtures for scoped retrieval and explanation completeness.
- Tighten regression tests around storage, retrieval, lifecycle, and MCP flows.
- Document a minimum local validation workflow for contributors.
- Define the “ready” bar for the vNext baseline.

Primary Files:

- [`aegis_py/retrieval/benchmark.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py)
- test suite under [`tests/`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests)

Exit Criteria:

- Retrieval-affecting changes are benchmarked.
- Core engine flows are covered by repeatable automated tests.
- The project can be iterated on without guessing whether behavior improved or regressed.

## Workstream Ordering

1. Stabilize the canonical data and status contract.
2. Unify retrieval semantics and result shape.
3. Tighten lifecycle, hygiene, and conflict safety.
4. Refactor integration surfaces to consume canonical services.
5. Strengthen benchmarks and regression gates.

This ordering preserves the constitution: behavior-preserving refactor first, measurement before speculative expansion, and simplicity before extra features.

## Risks And Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dual storage/retrieval paths continue diverging | Hidden regressions and inconsistent behavior | Pick a canonical path early and add contract tests around it |
| Schema/model mismatch across modules | Runtime errors, weak provenance, broken lifecycle states | Align schema and model contracts before deeper feature work |
| MCP/server drifts from core engine semantics | Users see inconsistent results across interfaces | Make integration layers thin adapters over canonical services |
| Hygiene or conflict logic mutates records too aggressively | Trust loss and provenance corruption | Keep changes suggestion-first, preserve source/history, add explicit tests |
| Retrieval tweaks optimize relevance but hide ambiguity | Higher apparent quality with lower trust | Include explanation completeness and conflict visibility in benchmark gates |

## Complexity Tracking

No constitution violations currently require exception handling.

## Validation Closeout

Validation run completed on 2026-03-23 against the Python suite.

Executed command:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests
```

Observed result:

- `48 passed in 0.85s`

Validated areas:

- storage schema and persistence behavior
- scoped retrieval, explainability, and leakage resistance
- lifecycle, hygiene, and conflict safety
- app, main, and MCP integration surfaces
- seeded benchmark regression gate for relevance, leakage, and explanation completeness

Remaining gaps to track after this feature baseline:

- benchmark fixture breadth is still small and should grow before release hardening
- contributor-facing release workflow is documented, but no dedicated CI wiring is captured in this feature
- TypeScript brownfield surfaces remain reference-only and are not part of the Python validation gate
