# Implementation Plan: Resolution Decay Pragmatism

**Branch**: `040-resolution-decay-pragmatism` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)

## Summary

Implement the next trust-and-hygiene product slice from [`2.md`](/home/hali/.openclaw/2.md): add bounded user-in-the-loop handling for hard conflicts, refine decay toward an archive-first practical retention model, and explicitly keep graph evolution SQLite-first with optional non-authoritative analysis helpers only.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/conflict`, `aegis_py/hygiene`, `aegis_py/retrieval`, `aegis_py/storage`, integration surfaces in `app.py`, `surface.py`, and `mcp/server.py`  
**Storage**: SQLite with FTS5 and existing `memories`, `conflicts`, and `memory_links` tables  
**Testing**: `pytest` integration and module-level regression coverage  
**Target Platform**: Local-first OpenClaw/MCP runtime on Linux  
**Project Type**: Local memory engine library plus MCP/CLI surfaces  
**Performance Goals**: Keep user-prompt classification bounded to same-subject or same-scope candidate sets and preserve current local retrieval responsiveness  
**Constraints**: No destructive ambiguous mutation by default, no new graph database, preserve explainability and migration-friendly schema behavior  
**Scale/Scope**: One feature slice spanning conflict policy, lifecycle shaping, and graph architecture guardrails

## Constitution Check

- **Local-First Memory Engine**: Pass. Work remains SQLite-first and offline-capable.
- **Brownfield Refactor Over Rewrite**: Pass. The plan extends existing conflict, hygiene, and link surfaces instead of replacing them.
- **Explainable Retrieval Is Non-Negotiable**: Pass with requirement. Conflict prompts, decay transitions, and graph boundaries must expose auditable reasons.
- **Safe Memory Mutation By Default**: Pass with emphasis. User prompting replaces ambiguous auto-resolution, and decay remains archive-first rather than destructive.
- **Measured Simplicity**: Pass. The plan explicitly rejects early graph-database adoption and keeps optional graph analysis non-authoritative.

## Implementation Steps

### Phase 1: Hard Conflict Resolution Policy

1. Define a bounded hard-conflict policy helper under `aegis_py/conflict/` that separates:
   - deterministic correction/supersession cases
   - weak or low-confidence candidates
   - true user-resolution candidates
2. Extend conflict result shaping so Aegis can return a structured resolution prompt payload with:
   - old memory
   - new memory
   - conflict type
   - bounded actions
   - recommendation cues
3. Add write-path support for recording explicit resolution outcomes and lifecycle events without destroying provenance.
4. Expose the new prompt/result shape through the Python-owned app and MCP/user surfaces without introducing orchestration-heavy UI logic.

### Phase 2: Practical Decay Refinement

1. Refine the current decay logic in `aegis_py/hygiene/` and `aegis_py/storage/manager.py` so retention is shaped by:
   - age
   - salience
   - reinforcement/access
   - memory type/tier
2. Keep lifecycle transitions archive-first:
   - active
   - cold but retrievable
   - archive candidate
   - deprecated candidate
3. Add bounded recall reinforcement so recently recalled memories recover somewhat without erasing age signals completely.
4. Preserve compatibility with existing maintenance flows and schema expectations.

### Phase 3: SQLite-First Graph Boundary

1. Reconcile current link and traversal surfaces with an explicit graph boundary contract:
   - SQLite links remain source of truth
   - optional in-memory analysis helpers remain non-authoritative
2. If graph analysis helpers are added, keep them isolated from storage semantics and runtime requirements.
3. Document that graph-native storage is intentionally deferred until bounded evidence shows SQLite links no longer meet recall or maintenance needs.

### Phase 4: Validation And Workflow Reconciliation

1. Add regression coverage for:
   - user-prompt-worthy hard conflicts
   - non-prompt deterministic correction flows
   - practical decay and bounded reinforcement
   - graph boundary expectations
2. Run the canonical prerequisite and Python validation workflows.
3. Reconcile `.planning/STATE.md` so GSD points at `040-resolution-decay-pragmatism` rather than the previously closed hold state.
4. Record closeout evidence back into this feature once implementation lands.

## Validation Plan

- `SPECIFY_FEATURE=040-resolution-decay-pragmatism ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
- targeted regression subsets for conflict, hygiene, retrieval, and integration behavior relevant to this slice

## Validation Evidence

Planning-only evidence recorded on 2026-03-24:

- feature `040-resolution-decay-pragmatism` was created to capture the new scope from `2.md`
- the feature now has explicit `spec.md`, `plan.md`, and `tasks.md` artifacts
- `.planning/STATE.md` is reconciled to point GSD at this feature as the active derivative coordination slice
- `SPECIFY_FEATURE=040-resolution-decay-pragmatism ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism`
  - `AVAILABLE_DOCS=["tasks.md"]`

Implementation evidence is pending until code and tests land.

Observed on 2026-03-24 after implementing `US1` for feature `040-resolution-decay-pragmatism`:

- hard same-scope ambiguous contradictions now classify into `user_resolution_required` instead of falling straight to generic manual review
- the Python runtime exposes `memory_conflict_prompt` and `memory_conflict_resolve` through the public surface and MCP server
- explicit user decisions now resolve conflicts with auditable lifecycle traces instead of silent mutation
- `memory_scan` now surfaces `resolution_prompt_count` so inspection paths can detect pending hard-conflict decisions

Validation results:

- `SPECIFY_FEATURE=040-resolution-decay-pragmatism ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/040-resolution-decay-pragmatism`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_conflict_core.py`
  - passed
  - `4 passed`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_integration.py -k 'public_surface_describes_python_owned_contract or python_runtime_ops_and_inspection_surfaces'`
  - passed
  - `2 passed, 38 deselected`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `116 passed in 3.28s`
- `npm run test:bootstrap`
  - passed
  - `17 passed`

Observed on 2026-03-24 after implementing `US2` for feature `040-resolution-decay-pragmatism`:

- practical decay now performs archive-first retention shaping after score cooling instead of only lowering activation scores
- active memories now receive explicit retention stages such as `cold`, while low-signal memories are archived with `archive_candidate` or `deprecated_candidate` metadata rather than being silently deleted
- bounded reinforcement now recovers recalled memories without resetting them to runaway activation levels

Additional validation results:

- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_hygiene.py tests/test_hygiene_core.py tests/test_memory_lifecycle.py`
  - passed
  - `13 passed`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_integration.py -k 'ingest_assigns_write_time_scores_but_preserves_explicit_values or context_pack_enforces_stage_budgets_and_reports_stage_counts'`
  - passed
  - `2 passed, 38 deselected`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `118 passed in 3.21s`

Observed on 2026-03-24 after implementing `US3` for feature `040-resolution-decay-pragmatism`:

- the runtime now states explicitly that SQLite-backed `memory_links` remain the graph source of truth
- `memory_visualize` can optionally return bounded local-only graph analysis without becoming an authoritative storage layer
- the public surface now marks graph-native storage as a non-goal and SQLite link ownership as a guarantee

Additional validation results:

- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_integration.py -k 'public_surface_describes_python_owned_contract or weaver_link_store_neighbors_and_visualization'`
  - passed
  - `2 passed, 38 deselected`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_python_only_runtime_contract.py`
  - passed
  - `3 passed`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `118 passed in 3.38s`
- `npm run test:bootstrap`
  - passed
  - `17 passed`
