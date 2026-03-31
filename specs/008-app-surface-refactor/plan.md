# Implementation Plan: App Surface Refactor

**Branch**: `008-app-surface-refactor` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/008-app-surface-refactor/spec.md)
**Input**: Feature specification from `/specs/008-app-surface-refactor/spec.md`

## Summary

Refactor `aegis_py/app.py` by extracting public contract assembly and operational workflows into Python-owned helper modules while preserving all existing host-facing behavior and keeping TypeScript adapters thin.

## Technical Context

**Language/Version**: Python 3.13.x plus TypeScript adapter shell  
**Primary Dependencies**: `aegis_py`, SQLite, MCP integration, existing integration tests  
**Storage**: Existing SQLite schema and filesystem backup artifacts  
**Testing**: `pytest`, bootstrap integration tests, existing validation workflow  
**Target Platform**: Local Linux runtime and OpenClaw-hosted plugin shell  
**Project Type**: Brownfield refactor of a Python memory engine  
**Performance Goals**: No regression in current local runtime behavior or validation throughput  
**Constraints**: No public behavior changes, no host-side semantic migration, no rewrite  
**Scale/Scope**: One focused refactor slice centered on `app.py` boundaries

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. This is an internal refactor only.
- `Brownfield Refactor Over Rewrite`: Pass. This feature is explicitly a behavior-preserving refactor.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Public retrieval payloads must stay stable.
- `Safe Memory Mutation By Default`: Pass. Backup and restore behavior must not change semantically.
- `Measured Simplicity`: Pass. The goal is to reduce god-object complexity, not add new capability.

## Project Structure

### Documentation (this feature)

```text
specs/008-app-surface-refactor/
├── spec.md
├── plan.md
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

tests/
test/integration/
```

**Structure Decision**: Keep public semantics Python-owned, introduce focused helper modules under `aegis_py/` for surface assembly and operational workflows, and leave TypeScript as adapter-only glue.

## Phase Plan

### Phase 0 - Refactor Boundary Audit

Objective: Identify which methods in `app.py` are orchestration, which are public-surface assembly, and which are operational workflows.

### Phase 1 - Public Surface Extraction

Objective: Move `public_surface()`, result serialization, and context-pack assembly into helper modules while keeping `AegisApp` as coordinator.

### Phase 2 - Operational Service Extraction

Objective: Move backup/restore and scope-policy operations into service helpers that `AegisApp` delegates to.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New helper modules under `aegis_py/` | `app.py` needs sharper ownership boundaries | Leaving everything in `app.py` would preserve growing god-object complexity |

## Validation Plan

- preserve all existing payload contracts
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py) now owns public contract assembly, search-result serialization, and context-pack shaping
- [aegis_py/operations.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/operations.py) now owns backup, restore, and scope-policy operational workflows
- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now delegates those responsibilities while preserving existing method names and payloads
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) now documents the extracted ownership boundary

Validation results:

- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `16` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `69 passed in 1.70s`
