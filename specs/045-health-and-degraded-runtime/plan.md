# Implementation Plan: Health States And Degraded Runtime Operation

**Branch**: `045-health-and-degraded-runtime` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/045-health-and-degraded-runtime/spec.md`

## Summary

Implement the next bounded slice after `044-production-hardening`: make runtime health a first-class contract instead of an implicit byproduct of doctor/status output. The goal is to preserve local-first operation while surfacing degraded and broken states explicitly across Python runtime surfaces and host-facing metadata.

## Technical Context

**Language/Version**: Python 3.13.x, existing TypeScript adapter shell  
**Primary Dependencies**: `sqlite3`, `pytest`, existing `aegis_py.app`, `aegis_py.operations`, `aegis_py.surface`, TS adapter/status surfaces  
**Storage**: SQLite remains the local source of truth  
**Testing**: `pytest`, targeted integration tests, parity checks for surface alignment  
**Target Platform**: Current OpenClaw/MCP local-first runtime  
**Project Type**: Runtime contract and operational-state hardening  
**Constraints**: Do not block local writes for degraded optional features. Do not move memory-domain ownership back into TypeScript.

## Constitution Check

- **Local-First Memory Engine**: Pass. The feature exists to preserve local-first guarantees while optional capabilities degrade.
- **Brownfield Refactor Over Rewrite**: Pass. Extends current doctor/status paths instead of replacing runtime architecture.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Health-state reporting becomes more explicit and structured.
- **Safe Memory Mutation By Default**: Pass. No mutation semantics are broadened here.
- **Measured Simplicity**: Pass. Bounded health states are simpler than scattered implicit failure handling.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── operations.py
│   ├── surface.py
│   └── mcp/server.py
├── src/
│   └── python-adapter.ts
├── README.md
├── openclaw.plugin.json
└── tests/
    ├── test_integration.py
    ├── test_python_only_runtime_contract.py
    └── operations/
```

## Validation Plan

- Add tests for bounded health-state enums and structured issue reporting.
- Add tests proving local writes continue under degraded states.
- Add tests proving broken local storage is distinguished from degraded optional-service issues.
- Re-run:
  - `.venv/bin/python -m pytest -q tests`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`

## Expected Evidence

- Explicit tests around health-state semantics
- Updated runtime/status payloads
- Surface parity across docs, runtime contract, and plugin metadata

## Validation Closeout

Validation run completed on 2026-03-28 for feature `045-health-and-degraded-runtime`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_app_surface.py tests/test_python_only_runtime_contract.py
node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts
.venv/bin/python -m pytest -q tests
```

Observed results:

- `13 passed in 1.07s` for targeted Python surface and manifest coverage
- `17 passed` in `test/integration/python-adapter-plugin.test.ts`
- `150 passed in 3.19s` for the full Python suite

Validated additions in this feature:

- bounded health states remain `HEALTHY`, `DEGRADED_SYNC`, and `BROKEN`
- `memory_stats`, `memory_doctor`, and `memory_surface` expose structured `health.state`, `health.issues`, and `health.capabilities`
- degraded sync states preserve local-first write and search behavior
- broken local storage remains distinct from degraded optional-sync conditions
- README, plugin metadata, Python public surface, and TS adapter-facing outputs now describe the same health contract

Remaining gaps after this slice:

- degraded mode is currently bounded to sync-adjacent state rather than a broader taxonomy of optional-service failures
- adapter parity is validated at the tool-shell contract level, not through a live end-to-end host session
