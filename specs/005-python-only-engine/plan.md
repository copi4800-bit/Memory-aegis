# Implementation Plan: Aegis Python-Only Runtime

**Branch**: `005-python-only-engine` | **Date**: 2026-03-23 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine/spec.md)
**Input**: Feature specification from `/specs/005-python-only-engine/spec.md`

## Summary

Remove the TypeScript memory engine from the production path, make `aegis_py` the only owner of memory-domain behavior, and reduce any remaining non-Python code to a host-required bootstrap only if OpenClaw cannot load Python directly.

## Technical Context

**Language/Version**: Python 3.13.x and TypeScript/Node only where the host contract still requires it  
**Primary Dependencies**: `aegis_py`, SQLite/FTS5, current OpenClaw plugin manifest, local Python virtualenv  
**Storage**: Local SQLite database owned by the Python engine  
**Testing**: `pytest` for Python engine, targeted repository integration tests for host/bootstrap behavior, packaging validation  
**Target Platform**: Local OpenClaw plugin environment on Linux  
**Project Type**: Local memory engine plus plugin runtime packaging  
**Performance Goals**: Preserve current local retrieval latency and explanation fidelity while removing duplicate runtime semantics  
**Constraints**: Must stay local-first; cannot silently keep the TypeScript engine alive; must respect any OpenClaw host-loading constraint that still requires a JS entrypoint  
**Scale/Scope**: One breaking migration wave from dual runtime to Python-only runtime ownership

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Local-First Memory Engine`: Pass. Python remains local-first and SQLite-backed.
- `Brownfield Refactor Over Rewrite`: Pass with caution. The goal is removal of the TS runtime path, but the migration should still proceed by converging and deleting duplicate behavior rather than rewriting Python semantics.
- `Explainable Retrieval Is Non-Negotiable`: Pass. The Python engine already provides the stronger explainable retrieval contract and must remain the runtime owner.
- `Safe Memory Mutation By Default`: Pass. Store, hygiene, and conflict flows should route to Python and preserve provenance/audits.
- `Measured Simplicity`: Pass with caution. Any leftover host bootstrap must stay tiny and non-semantic.

No constitutional blockers were found, but the host-loading contract is the key migration risk.

## Project Structure

### Documentation (this feature)

```text
specs/005-python-only-engine/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── main.py
├── mcp/
└── ...

src/
├── plugin.ts
├── index.ts
├── aegis-manager.ts
└── ...

openclaw.plugin.json
package.json
requirements.txt
tests/
test/
```

**Structure Decision**: Keep the current hybrid repo during migration, but move all runtime ownership to `aegis_py`. The TypeScript tree is now migration target material, not long-term architecture.

## Phase Plan

### Phase 0 - Host Constraint Verification

Objective: Prove whether OpenClaw can load a Python runtime directly or still requires a JavaScript entrypoint.

Observed repository evidence on 2026-03-23:

- [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json) currently points OpenClaw at `./dist/index.js`.
- [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json) defines the plugin manifest but does not obviously declare a direct Python command runtime.
- The TypeScript runtime currently registers tools and services through [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) and [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts).
- `openclaw.extensions` in [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json) explicitly lists `./dist/index.js` as the installed extension entry.

Planning implication:

- true zero-TypeScript runtime is only safe if OpenClaw supports direct Python or command-based plugin startup
- if the host requires JS loading, the acceptable outcome for this feature becomes "Python-only engine with documented bootstrap shim"

Current inventory of TypeScript runtime ownership:

- [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts): plugin registration, hooks, and runtime tool surface
- [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts): duplicate plugin runtime surface
- [src/aegis-manager.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/aegis-manager.ts): legacy TypeScript memory engine, storage, retrieval, maintenance, backup, and UX logic
- [src/](/home/hali/.openclaw/extensions/memory-aegis-v7/src): broad set of legacy runtime modules that still represent the old engine even when the Python adapter is enabled

### Phase 1 - Python Runtime Completion

Objective: Ensure every core memory behavior needed by OpenClaw is available through Python-owned surfaces.

Target capabilities:

- `memory_search`
- `memory_get`
- `memory_store`
- `memory_status` / `memory_stats`
- `memory_clean`
- backup/restore surfaces
- `memory_profile`
- session/recall hook equivalents where they are still needed by the host integration

Extension added on 2026-03-24:

- finish Python-owned surfaces for `memory_get`, backup upload/export, and backup restore so the host bootstrap no longer reports them as unsupported compatibility placeholders

Implemented on 2026-03-24:

- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now exposes Python-owned readback, snapshot/export, and restore helpers
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) now serves `memory_get`, `memory_backup_upload`, and `memory_backup_download`
- [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) now route those host tools into Python rather than returning unsupported

Implemented on 2026-03-23:

- [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) now acts as a Python-first host bootstrap for core tools instead of a fallback-heavy TypeScript engine
- core runtime tools `memory_search`, `memory_store`, `memory_stats`, `memory_clean`, and `memory_profile` now execute through [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) without TypeScript manager fallback
- the `before_agent_start` recall hook now pulls memory context through Python only
- the `agent_end` auto-capture flow now stores user text through Python and optionally runs Python maintenance instead of using the TypeScript manager
- [src/plugin.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/plugin.ts) is reduced to a re-export of the root bootstrap so the repo no longer carries two competing plugin runtime implementations

### Phase 2 - Packaging And Host Entry Simplification

Objective: Rework packaging and startup so that OpenClaw runs Python directly if possible, or via a minimal host bridge if not.

Expected outputs:

- updated manifest/package metadata
- explicit Python startup command or bootstrap contract
- contributor instructions that no longer center the TS build for runtime ownership

Implemented on 2026-03-24:

- [src/cli/setup.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/cli/setup.ts) no longer initializes the legacy TypeScript manager and now runs the Python MCP self-test through a Node compatibility wrapper
- [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json) now ships `aegis_py`, `requirements.txt`, and Python-facing release docs while excluding the legacy `src/` tree from published package files
- [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json) now exposes Python-first contributor scripts such as `test:python`, `validate:python`, and `package:python`
- [openclaw.plugin.json](/home/hali/.openclaw/extensions/memory-aegis-v7/openclaw.plugin.json) now reflects the actual bootstrap tool surface and labels unsupported advanced tools as compatibility surfaces instead of pretending they are Python-complete
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) and [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md) now describe the Python-first validation and packaging contract more explicitly

### Phase 3 - TypeScript Runtime Removal

Objective: Delete or quarantine the legacy TypeScript engine once the Python path is validated.

Scope:

- remove TS retrieval/storage/hygiene/profile ownership
- keep only host bootstrap code if proven necessary
- remove stale TS tests, docs, and packaging assumptions that refer to the old engine as active runtime

Implemented on 2026-03-24:

- [src/aegis-manager.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/aegis-manager.ts) is now a compatibility stub that fails fast instead of providing a working TypeScript memory engine
- [src/index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/index.ts) no longer re-exports `AegisMemoryManager` or `closeAllManagers` as part of the package public surface
- manager-centric legacy tests that treated the TypeScript engine as a supported runtime path were removed from [test/](/home/hali/.openclaw/extensions/memory-aegis-v7/test)
- [test/README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/test/README.md) now documents that `tests/` is canonical and `test/` is legacy/bootstrap-only

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Transitional host bootstrap may remain | OpenClaw may still require a JS-loaded plugin entry | A hard delete of all JS/TS before proving host support could leave the plugin unloadable |

## Validation Evidence

Observed on 2026-03-23:

- `npm test -- --run test/integration/python-adapter-plugin.test.ts`
  - passed: `8` tests
  - proves the root plugin bootstrap routes core tools and hook flows through Python
  - proves unsupported legacy TS-only tools now fail explicitly instead of reviving the old TS engine
- `npm run lint`
  - passed
  - confirms the reduced bootstrap still type-checks
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/pytest -q tests`
  - passed: `55 passed in 0.91s`
  - confirms the Python engine remains green after the bootstrap reduction

Observed on 2026-03-24:

- `npm run lint`
  - passed
  - confirms the host bootstrap, Python-first setup wrapper, and `AegisMemoryManager` compatibility stub still type-check
- `npm run test:bootstrap`
  - passed: `17` tests
  - confirms the JS bootstrap now routes `memory_get`, backup upload, and restore in addition to the earlier core tools and hook flows
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/pytest -q tests`
  - passed: `114 passed in 3.92s`
  - includes Python runtime smoke tests for citation readback, backup/export/restore, maintenance, inspection, trust shaping, and the current user-facing surface

Current residual risks:

- [package.json](/home/hali/.openclaw/extensions/memory-aegis-v7/package.json) still makes OpenClaw load `./dist/index.js`, so a tiny JS bootstrap remains on the host path
- the repository still contains many legacy TypeScript helper modules under [src/](/home/hali/.openclaw/extensions/memory-aegis-v7/src) even though the central manager and public engine surface have been quarantined
- some legacy TypeScript utility tests still remain in [test/](/home/hali/.openclaw/extensions/memory-aegis-v7/test) for isolated helper behavior, so contributors must continue to treat that tree as non-canonical

Ops/inspection extension implemented on 2026-03-24:

- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now exposes Python-owned doctor, taxonomy cleanup, rebuild, scan, and graph snapshot helpers
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) now serves `memory_doctor`, `memory_taxonomy_clean`, `memory_rebuild`, `memory_scan`, and `memory_visualize`
- [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) now route those host tools into Python rather than reporting unsupported

Additional validation observed on 2026-03-24:

- `npm run test:bootstrap`
  - passed: `17` tests
  - confirms all remaining maintenance and inspection tools now route through Python
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/pytest -q tests`
  - passed: `114 passed in 3.92s`
  - includes runtime coverage for doctor, taxonomy cleanup, rebuild, scan, and visualize
