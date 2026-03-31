# Implementation Plan: Consumer Recovery Trust

**Branch**: `049-consumer-recovery-trust` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/049-consumer-recovery-trust/spec.md`

## Summary

Make recovery and trust-oriented diagnostics understandable for ordinary users without changing the underlying Python-owned payloads. The feature will add plain-language summaries for doctor and backup/restore CLI commands, keep JSON behind explicit flags, and make the OpenClaw-facing `memory_doctor` tool summary-first while preserving structured `details`.

## Technical Context

**Language/Version**: Python 3.13.x and existing TypeScript adapter shell  
**Primary Dependencies**: `aegis_py.app`, `aegis_py.cli`, `aegis_py.operations`, `index.ts`, existing backup and health contracts  
**Storage**: SQLite local DB and filesystem backup artifacts  
**Testing**: `pytest`, `vitest`, existing backup and adapter tests  
**Target Platform**: current OpenClaw local-first runtime, CLI, and plugin shell  
**Project Type**: recovery/diagnostics surface refinement  
**Performance Goals**: N/A for this slice  
**Constraints**: must preserve structured operational payloads; must not redesign backup semantics; must improve ordinary-user trust without hiding important failure states  
**Scale/Scope**: diagnostics and recovery presentation only

## Constitution Check

- **Local-First Memory Engine**: Pass. The feature improves understanding of local-first recovery and diagnostics without introducing hosted dependencies.
- **Brownfield Refactor Over Rewrite**: Pass. It extends the active Python-owned operational surfaces.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Retrieval behavior is untouched.
- **Safe Memory Mutation By Default**: Pass. Restore preview communication becomes clearer without relaxing safety.
- **Measured Simplicity**: Pass. The work narrows default output to the minimum useful trust surface and leaves advanced payloads intact.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── cli.py
│   └── operations.py
├── index.ts
├── tests/
│   ├── test_user_surface.py
│   └── operations/test_backup.py
└── test/
    └── integration/python-adapter-plugin.test.ts
```

## Validation Plan

- Add tests for plain-language doctor and recovery summaries on the CLI/user surface.
- Update adapter tests so `memory_doctor` returns human-readable primary content while preserving details.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py tests/operations/test_backup.py`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`
  - `.venv/bin/python -m pytest -q tests`

## Expected Evidence

- Python-owned summary helpers for diagnostics and recovery flows
- CLI defaults shifting to trust-oriented summaries with explicit `--json` escape hatches
- plugin `memory_doctor` moving from JSON-first to summary-first content

## Validation Closeout

Validation run completed on 2026-03-28 for feature `049-consumer-recovery-trust`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_integration.py tests/test_user_surface.py tests/operations/test_backup.py
node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts
.venv/bin/python -m pytest -q tests
```

Observed results:

- `57 passed in 2.68s` for targeted integration, user-surface, and backup coverage
- `17 passed` in `test/integration/python-adapter-plugin.test.ts`
- `162 passed in 4.33s` for the full Python suite

Validated additions in this feature:

- `doctor`, `backup-upload`, `backup-list`, `backup-preview`, and `backup-download` are now summary-first on the CLI
- explicit `--json` support preserves structured payloads for automation and tests
- plugin `memory_doctor` now returns human-readable primary content while preserving structured `details`
- restore preview and diagnostics now explain degraded local usability in more understandable language

Remaining gaps after this slice:

- the broader plugin and manifest surface still contains many advanced tools that ordinary users would not need directly
- a final closure review is still required before any "consumer-complete" claim is justified

## Complexity Tracking

No constitution violations currently require exception handling.
