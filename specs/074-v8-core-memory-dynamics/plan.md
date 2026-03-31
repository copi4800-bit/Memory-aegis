# Implementation Plan: V8 Core Memory Dynamics

**Branch**: `074-v8-core-memory-dynamics` | **Date**: 2026-03-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/074-v8-core-memory-dynamics/spec.md`

## Summary

Translate the v8 theory documents into one executable tranche by adding a bounded dynamic signal model, dynamic retrieval shaping, and a minimal hysteresis-aware transition gate on top of the current Python runtime.

## Technical Context

**Language/Version**: Python runtime on local SQLite storage, existing host adapter unchanged  
**Primary Dependencies**: `aegis_py/app.py`, `aegis_py/retrieval/search.py`, `aegis_py/retrieval/engine.py`, `aegis_py/storage/manager.py`, existing state/governance helpers, runtime tests  
**Storage**: existing SQLite memory/evidence/link tables; no broad schema rewrite in this tranche  
**Testing**: `pytest` runtime/retrieval/integration suites plus apocalypse runtime validation  
**Target Platform**: current Python-owned local-first memory runtime  
**Project Type**: Python runtime/library with host integration  
**Performance Goals**: preserve the current post-hardening retrieval and apocalypse envelopes while adding bounded scoring terms  
**Constraints**: no simulator-first rewrite; no dependence on unavailable full utility learning; no public payload drift; no scope leakage regression  
**Scale/Scope**: bounded v8-core signals, bounded retrieval shaping, one minimal transition gate, compatibility-first tests

## Constitution Check

- **Local-First Memory Engine**: Pass. The tranche stays inside the local Python + SQLite runtime.
- **Brownfield Refactor Over Rewrite**: Pass. It layers v8-core signals onto the existing runtime instead of forking a new engine.
- **Explainable Retrieval Is Non-Negotiable**: Pass. The tranche requires an explainable internal/operator-facing view of trust/readiness terms.
- **Safe Memory Mutation By Default**: Pass. Transition work is bounded and hysteresis-aware; no broad autonomous mutation wave.
- **Measured Simplicity**: Pass. Full regret learning, simulator work, and energy optimization are explicitly deferred.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── retrieval/
│   │   ├── engine.py
│   │   └── search.py
│   ├── storage/
│   │   └── manager.py
│   ├── governance/
│   └── surface.py
├── tests/
│   ├── test_retrieval.py
│   ├── test_memory_core.py
│   ├── test_user_surface.py
│   └── test_apocalypse_runtime.py
└── specs/
    └── 074-v8-core-memory-dynamics/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Design Notes

- Use `12.md` as the executable formula source, `11.md` as notation, and `7.md` as the theory boundary.
- Implement only the measurable subset the runtime can support now:
  - bounded evidence signal
  - normalized support/conflict pressure
  - bounded usage surrogate
  - trust score
  - retrieval readiness
  - dynamic retrieval shaping
  - minimal draft/validated hysteresis gate
  - bounded outcome feedback for usage, regret, decay, and belief
  - bounded bundle energy/objective snapshot and regression gate
- Treat downstream utility/regret as deferred or surrogate-backed, not full-learning infrastructure.
- Keep public search/context payloads stable; add explanation through internal/operator-facing seams only.

## Validation Plan

- Add focused retrieval tests proving dynamic ranking behavior from trust/readiness.
- Add runtime tests for bounded v8-core signals and hysteresis transition behavior.
- Add focused feedback tests proving bounded usage/regret/decay/belief updates affect retrieval and remain auditable.
- Add a benchmarked retrieval-feedback case proving bundle credit assignment aligns with selection and that objective regression stays within a bounded tolerance for the seeded case.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_retrieval.py tests/test_memory_core.py tests/test_user_surface.py`
  - `.venv/bin/python -m pytest -q tests/test_apocalypse_runtime.py`

## Expected Evidence

- a bounded v8-core signal helper or module in the Python runtime
- retrieval internals consuming trust/readiness without public contract drift
- one minimal hysteresis-aware transition seam for draft/validated decisions
- one bounded outcome-feedback seam for usage/regret/decay/belief dynamics
- one bundle-level energy/objective snapshot and benchmark gate for seeded retrieval-feedback scenarios
- green focused retrieval/runtime tests and apocalypse validation

## Complexity Tracking

Main risk: allowing the v8 theory to sprawl into a simulator rewrite. Guard against that by rejecting any work item that depends on full posterior learning, full regret instrumentation, or a schema-heavy memory-field redesign.
