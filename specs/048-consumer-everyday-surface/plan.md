# Implementation Plan: Consumer Everyday Surface

**Branch**: `048-consumer-everyday-surface` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/048-consumer-everyday-surface/spec.md`

## Summary

Make the default everyday status surface readable for non-technical users without removing the existing machine-readable contract. The feature will add a plain-language status summary in the Python runtime, expose it through the default CLI `status` path, and make the OpenClaw-facing `memory_stats` tool render human-readable content first while preserving structured details.

## Technical Context

**Language/Version**: Python 3.13.x and existing TypeScript adapter shell  
**Primary Dependencies**: `aegis_py.app`, `aegis_py.cli`, `index.ts`, existing health contract and status payload  
**Storage**: SQLite local DB  
**Testing**: `pytest`, `vitest`, existing user-surface and adapter tests  
**Target Platform**: current OpenClaw local-first runtime, CLI, and plugin tool shell  
**Project Type**: runtime/user-surface refinement  
**Performance Goals**: N/A for this slice  
**Constraints**: must preserve machine-readable status payloads; must not break existing health semantics; should improve the default path without trying to redesign all advanced tools  
**Scale/Scope**: status and default user-facing output only

## Constitution Check

- **Local-First Memory Engine**: Pass. The feature changes status presentation, not the local-first contract.
- **Brownfield Refactor Over Rewrite**: Pass. The work extends the active Python-owned runtime and adapter shell.
- **Explainable Retrieval Is Non-Negotiable**: Pass. No retrieval explainability is removed.
- **Safe Memory Mutation By Default**: Pass. The feature does not broaden mutation semantics.
- **Measured Simplicity**: Pass. It narrows the default user surface while preserving advanced details for tooling.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   └── cli.py
├── index.ts
├── tests/
│   ├── test_user_surface.py
│   └── test_app_surface.py
└── test/
    └── integration/python-adapter-plugin.test.ts
```

## Validation Plan

- Add tests for plain-language status output in the Python user surface.
- Update adapter tests so `memory_stats` returns human-readable primary content while keeping structured `details`.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py tests/test_app_surface.py`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`
  - `.venv/bin/python -m pytest -q tests`

## Expected Evidence

- Python-owned status summary method and CLI plain-language default
- plugin `memory_stats` content shifting from JSON-first to summary-first
- validation proving healthy and degraded states are understandable for ordinary users

## Validation Closeout

Validation run completed on 2026-03-28 for feature `048-consumer-everyday-surface`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_user_surface.py tests/test_app_surface.py
node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts
.venv/bin/python -m pytest -q tests
```

Observed results:

- `23 passed in 1.70s` for targeted Python everyday-surface coverage
- `17 passed` in `test/integration/python-adapter-plugin.test.ts`
- `158 passed in 3.51s` for the full Python suite

Validated additions in this feature:

- `aegis_py.app` now exposes a plain-language status summary for healthy, degraded, and broken states
- `aegis_py.cli status` is plain-language by default and supports `--json` for structured output
- OpenClaw-facing `memory_stats` now renders human-readable primary content while preserving structured `details`
- degraded sync states are described as locally usable rather than as broken

Remaining gaps after this slice:

- advanced tools such as backup, restore, and doctor remain more operator-oriented than ordinary-user-oriented
- the broader plugin surface still exposes many advanced capabilities even though the default status path is now simplified

## Complexity Tracking

No constitution violations currently require exception handling.
