# Implementation Plan: Guided Host Integration

**Branch**: `051-guided-host-integration` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/051-guided-host-integration/spec.md`

## Summary

Reduce the final consumer-closure blockers by making the ordinary-user host path explicit and by turning the remaining TS-era onboarding module into a legacy stub. This feature does not remove advanced tools; it clarifies which host tools are the default consumer path and prevents the TS onboarding file from looking active.

## Technical Context

**Language/Version**: JSON and Markdown artifacts, existing TypeScript compatibility file  
**Primary Dependencies**: `openclaw.plugin.json`, `README.md`, `src/ux/onboarding.ts`, existing contract tests  
**Storage**: N/A  
**Testing**: `pytest` manifest/contract tests  
**Target Platform**: current OpenClaw plugin metadata and repo-level consumer guidance  
**Project Type**: host-surface governance and legacy-boundary cleanup  
**Performance Goals**: N/A  
**Constraints**: must not break existing advanced tool availability; must preserve the Python-owned runtime as the authoritative path; must make the host default surface explicit rather than implied  
**Scale/Scope**: manifest, README, legacy TS onboarding stub, and tests

## Constitution Check

- **Local-First Memory Engine**: Pass. The feature clarifies the default local-first path rather than changing runtime behavior.
- **Brownfield Refactor Over Rewrite**: Pass. It keeps legacy files only as explicit stubs and adds metadata/guidance instead of rewriting the host shell.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Retrieval semantics are untouched.
- **Safe Memory Mutation By Default**: Pass. No mutation behavior changes.
- **Measured Simplicity**: Pass. The work reduces ambiguity around default versus advanced host paths.

## Source Areas

```text
extensions/memory-aegis-v7/
├── openclaw.plugin.json
├── README.md
├── src/
│   └── ux/onboarding.ts
└── tests/
    └── test_python_only_runtime_contract.py
```

## Validation Plan

- Update manifest and README to declare the consumer/default surface.
- Convert the TS onboarding file into an explicit legacy stub.
- Update contract tests for the consumer surface metadata and TS legacy-stub behavior.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py`

## Expected Evidence

- explicit `consumerSurface` metadata in the plugin manifest
- README section aligning with the same default path
- TS onboarding file failing clearly with a migration message to Python onboarding

## Validation Closeout

Validation run completed on 2026-03-28 for feature `051-guided-host-integration`.

Executed command:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py
```

Observed result:

- `4 passed in 0.02s`

Validated additions in this feature:

- the plugin manifest now declares an explicit `consumerSurface` with default and advanced tool separation
- the README now describes the same bounded ordinary-user path
- `src/ux/onboarding.ts` is now an explicit legacy stub that redirects callers to the Python-owned onboarding path

## Complexity Tracking

No constitution violations currently require exception handling.
