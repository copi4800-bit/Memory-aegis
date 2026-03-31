# Implementation Plan: Production Observability

**Branch**: `071-production-observability` | **Date**: 2026-03-29 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/071-production-observability/spec.md)
**Input**: Feature specification from `/specs/071-production-observability/spec.md`

## Summary

Add a narrow observability foundation to the Python-owned runtime: structured runtime events, a bounded process-local metrics snapshot, and instrumentation for the highest-signal flows already used in production-shaped checks.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: stdlib, pytest  
**Storage**: in-memory process-local counters plus bounded recent-event buffer  
**Testing**: pytest  
**Target Platform**: Linux local runtime  
**Project Type**: library plus runtime integration tests  
**Constraints**: no external metrics backend, no network dependency, no rewrite of existing runtime layers  
**Scale/Scope**: observability contract and minimal flow instrumentation only

## Constitution Check

- Preserve the Python-owned runtime boundary.
- Prefer a narrow, real signal path over speculative telemetry architecture.
- Keep observability JSON-first and operator-readable.

## Structure Decision

- Add a small shared observability module under `aegis_py/observability/`.
- Instrument a handful of core `AegisApp` flows directly.
- Add focused tests rather than broad logging rewrites.

## Validation Commands

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_observability_runtime.py
PYTHONPATH=. .venv/bin/python -m pytest -q tests/acceptance tests/regression tests/test_observability_runtime.py
```

## Initial Tranche Scope

- Structured event builder
- Bounded runtime metrics registry
- Snapshot surface on `AegisApp`
- Instrumentation for:
  - `put_memory`
  - `search`
  - `plan_background_intelligence`
  - `apply_background_intelligence_run`
  - `rollback_background_intelligence_run`
  - `create_backup`
  - `preview_restore`
  - `restore_backup`

## Remaining Gaps

- This tranche keeps metrics process-local only; it does not yet add persistence, alert thresholds, or export to an external monitoring backend.
