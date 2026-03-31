# Implementation Plan: Beast Architecture Mapping

**Branch**: `010-beast-architecture-mapping` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/spec.md)
**Input**: Feature specification from `/specs/010-beast-architecture-mapping/spec.md`

## Summary

Turn the "23 beasts" note into a canonical internal architecture guide for the Python engine, aligned with the existing six-module model and the GSD + Spec Kit workflow.

## Technical Context

**Language/Version**: Markdown documentation for a Python 3.13.x codebase  
**Primary Dependencies**: existing repo docs, [1.md](/home/hali/.openclaw/1.md), current `aegis_py/` structure  
**Storage**: repository documentation only  
**Testing**: Spec Kit prerequisite check plus standard repo validation for non-regression  
**Target Platform**: repository contributors and maintainers  
**Project Type**: Brownfield architecture documentation and workflow reconciliation  
**Performance Goals**: None; no runtime behavior changes  
**Constraints**: Keep beast taxonomy internal-facing, preserve the six-module model, do not introduce new public runtime semantics  
**Scale/Scope**: One new feature artifact set, one canonical architecture doc, one README update, one planning-state reconciliation

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. This work changes documentation and architecture guidance only.
- `Brownfield Refactor Over Rewrite`: Pass. The mapping is anchored to current modules and near-term target boundaries.
- `Explainable Retrieval Is Non-Negotiable`: Pass. The beast map keeps `Explainer`, `Reranker`, and scoped retrieval as first-class internal concepts.
- `Safe Memory Mutation By Default`: Pass. No runtime mutation semantics are changed.
- `Measured Simplicity`: Pass. The feature explicitly prevents over-fragmenting the codebase into 23 runtime modules.

## Project Structure

### Documentation (this feature)

```text
specs/010-beast-architecture-mapping/
├── spec.md
├── plan.md
├── research.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
└── ARCHITECTURE_BEAST_MAP.md

README.md
.planning/STATE.md
```

**Structure Decision**: Add one canonical internal architecture document under `aegis_py/` and update repo-level docs to reference it as the internal beast taxonomy.

## Phase Plan

### Phase 0 - Source Reconciliation

Objective: Reconcile `1.md`, feature `007` research, and current Python directories into one consistent architecture position.

### Phase 1 - Canonical Beast Map

Objective: Add an internal document that maps all 23 beasts into the six-module model with current/target/deferred ownership notes.

### Phase 2 - Repo Documentation And Workflow

Objective: Update the README and planning state so the repo officially points contributors to the new architecture guide.

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- [aegis_py/ARCHITECTURE_BEAST_MAP.md](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/ARCHITECTURE_BEAST_MAP.md) now maps all 23 beasts to the practical six-module Python architecture with current/target/deferred ownership notes
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) now explains that beast names are internal taxonomy only and points contributors to the canonical map
- [.planning/STATE.md](/home/hali/.openclaw/extensions/memory-aegis-v7/.planning/STATE.md) now anchors GSD execution to feature `010-beast-architecture-mapping`

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/010-beast-architecture-mapping`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `16` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `71 passed in 2.54s`
