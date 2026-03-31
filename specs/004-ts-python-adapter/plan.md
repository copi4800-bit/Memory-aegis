# Implementation Plan: Aegis TypeScript Adapter To Python Engine

**Branch**: `004-ts-python-adapter` | **Date**: 2026-03-23 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter/spec.md)
**Input**: Feature specification from `/specs/004-ts-python-adapter/spec.md`

## Summary

Migrate Aegis toward the Python engine without breaking the current OpenClaw integration by keeping the TypeScript plugin as a thin adapter, routing the safest canonical behaviors to Python first, and documenting the remaining parity gaps explicitly.

## Technical Context

**Language/Version**: TypeScript/Node adapter layer plus Python 3.13.x engine  
**Primary Dependencies**: Existing TypeScript plugin shell, `aegis_py` local engine, current OpenClaw plugin manifest and tool definitions  
**Storage**: Python local SQLite/FTS5 engine remains the intended canonical memory backend  
**Testing**: Existing Python regression suite plus repository-level TypeScript/plugin tests where applicable  
**Target Platform**: Local OpenClaw plugin environment and repository-local validation workflows  
**Project Type**: Hybrid migration feature across plugin adapter code and Python engine contract  
**Performance Goals**: Keep current plugin usability while reducing duplicated retrieval semantics between TS and Python  
**Constraints**: Do not break the existing plugin shell abruptly, do not claim parity for unsupported tools, keep migration incremental and explicit  
**Scale/Scope**: One migration wave focused on adapter strategy, tool parity mapping, and the first safe routing surface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Local-First Memory Engine`: Pass. Python remains the local-first backend target.
- `Brownfield Refactor Over Rewrite`: Pass. This feature is explicitly an adapter migration wave, not a rewrite.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Retrieval migration should favor Python because it is the clearer canonical path.
- `Safe Memory Mutation By Default`: Pass. This feature concerns adapter routing, not more aggressive mutation semantics.
- `Measured Simplicity`: Pass with caution. The adapter must stay thin and avoid creating a second long-lived truth.

No constitutional violations are expected for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/004-ts-python-adapter/
├── plan.md
├── spec.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── plugin.ts
├── aegis-manager.ts
└── ...

aegis_py/
├── app.py
├── mcp/server.py
└── ...

openclaw.plugin.json
tests/
test/
```

**Structure Decision**: Keep the hybrid repository structure. This feature should primarily touch the TypeScript plugin shell, Python engine integration contract, plugin manifest mapping, and migration planning artifacts.

## Phase Plan

### Phase 0 - Tool Parity Inventory

Objective: Compare the current TypeScript tool surface and Python engine surface, and identify the safest first routing targets.

Current inventory reconciled on 2026-03-24:

- The root TypeScript bootstrap in `index.ts` now exposes only a host-facing adapter layer over Python-owned tools:
  - `memory_search`
  - `memory_context_pack`
  - `memory_link_store`
  - `memory_link_neighbors`
  - `memory_get`
  - `memory_store`
  - `memory_surface`
  - `memory_scope_policy`
  - `memory_backup_upload`
  - `memory_backup_download`
  - `memory_backup_list`
  - `memory_backup_preview`
  - `memory_stats`
  - `memory_doctor`
  - `memory_clean`
  - `memory_rebuild`
  - `memory_scan`
  - `memory_profile`
  - `memory_visualize`
  - `memory_taxonomy_clean`
- `openclaw.plugin.json` now matches that adapter-oriented public surface.
- The Python canonical engine now exposes the same runtime-facing capability set through `aegis_py/app.py` and `aegis_py/mcp/server.py`.

Immediate conclusion:

- the earlier retrieval-first migration slice is complete
- the TypeScript layer now acts as an adapter/bootstrap, not a competing runtime
- remaining differences are host-loading constraints and contributor cleanup, not tool parity gaps inside the current public surface

### Phase 1 - Adapter Contract

Objective: Define how the TypeScript plugin shell will call or map to the Python engine without claiming full parity.

Primary Files:

- [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts)
- [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts)
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)
- [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json)

First routing slice recommendation:

- route `memory_search` to the Python engine first
- immediately extend the same adapter path to `memory_store`, `memory_stats`/`memory_status`, `memory_clean`, and `memory_profile` once the shell contract is proven
- treat any still-missing legacy surface outside the manifest as out of scope rather than reviving the old TS engine

### Phase 2 - First Routing Slice

Objective: Route the safest canonical surface, likely retrieval-oriented behavior, through Python while keeping unsupported tools explicit.

Implemented on 2026-03-23:

- `memory_search` in [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) and [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts) now supports a Python-backed retrieval slice via [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts)
- the adapter invokes [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) with a single-tool CLI contract instead of re-implementing Python retrieval semantics in TypeScript
- the same adapter path now covers `memory_store`, `memory_stats`, `memory_clean`, and `memory_profile` for the TypeScript shell
- the `before_agent_start` recall hook also prefers Python retrieval when the adapter is enabled, so the highest-value recall path no longer stays pinned to the TypeScript retriever
- routing is intentionally gated by `pythonToolAdapter` / `pythonRetrievalAdapter` (`off`, `auto`, `force`) so the migration can be exercised without claiming full parity
- `auto` mode falls back to the existing TypeScript manager if the Python route fails; `force` mode surfaces the Python-side error directly
- the adapter sets an isolated `AEGIS_DB_PATH` under the workspace when no explicit DB path is configured, avoiding accidental reuse of the stale repository-root SQLite file

Reconciled parity map on 2026-03-24:

| Surface | TS Runtime | Manifest | Python | Migration Status |
|---------|------------|----------|--------|------------------|
| `memory_search` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_context_pack` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_link_store` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_link_neighbors` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_store` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_stats` | Yes | Yes | Yes | Python-backed mapping implemented |
| `memory_clean` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_profile` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_get` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_surface` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_scope_policy` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_backup_upload` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_backup_download` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_backup_list` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_backup_preview` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_doctor` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_rebuild` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_scan` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_visualize` | Yes | Yes | Yes | Python-backed adapter implemented |
| `memory_taxonomy_clean` | Yes | Yes | Yes | Python-backed adapter implemented |

### Phase 3 - Migration Evidence Record

Objective: Record what the adapter now delegates, what remains TS-only, and what parity work is still required.

Staged replacement strategy:

1. lock the parity map and runtime-vs-manifest mismatches
2. migrate `memory_search` to Python behind the TS shell
3. add adapter coverage proving TS tool output preserves Python retrieval semantics
4. migrate adjacent low-risk surfaces only after the first slice is stable
5. defer advanced TS-only tools until Python parity exists or the manifest/runtime contract is simplified

## Validation Evidence

Observed on 2026-03-23:

- `npm test -- --run test/integration/python-adapter-plugin.test.ts`
  - passed
  - proves `memory_search`, `memory_store`, `memory_stats`, `memory_clean`, and `memory_profile` all work through the TypeScript shell with Python-backed execution where expected
  - proves `memory_search` falls back to the TypeScript manager in `auto` mode
  - proves the `before_agent_start` recall hook prefers Python retrieval when forced
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/pytest -q tests`
  - passed: `55 passed in 1.66s`
  - confirms the Python canonical engine remains green after exposing the single-tool CLI path
- `AEGIS_DB_PATH=/tmp/aegis_python_adapter_smoke.db PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/python aegis_py/mcp/server.py --tool memory_search --args-json '{"text":"SQLite retrieval","limit":2,"scope_type":"project","scope_id":"aegis-v4"}'`
  - passed
  - returned `[]` on a fresh isolated database, which is expected for an empty Python store

Observed on 2026-03-24:

- `SPECIFY_FEATURE=004-ts-python-adapter ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - resolved `FEATURE_DIR` to `specs/004-ts-python-adapter`
  - confirms the feature artifact directory is still valid for Spec Kit execution
- `npm run lint`
  - passed
  - confirms the TypeScript layer remains a valid host bootstrap after the quarantine of the old engine
- `npm run test:bootstrap`
  - passed: `17` tests
  - confirms the public TS bootstrap routes the current manifest tool surface through Python-owned behavior
- `PYTHONPATH=. /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/pytest -q tests`
  - passed: `114 passed in 3.92s`
  - confirms the Python canonical engine remains green while serving the adapter-owned public surface

## Residual Risks

- OpenClaw still loads the plugin through `./dist/index.js`, so the repository keeps a small JS bootstrap on the host path
- legacy helper modules still exist under `src/`, even though the former `AegisMemoryManager` runtime has been quarantined behind a fail-fast stub
- future new tools must continue to be added Python-first to avoid recreating parity drift

## Complexity Tracking

No constitution violations currently require exception handling.
