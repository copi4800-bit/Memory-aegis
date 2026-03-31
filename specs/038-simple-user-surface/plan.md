# Implementation Plan: Simple User Surface

**Branch**: `038-simple-user-surface`
**Spec**: [spec.md](./spec.md)

## Summary
Implement a high-level, human-friendly surface for Aegis Python, reducing complexity to 4 core actions.

## Work Plan
1.  Extend `AegisApp` with `memory_remember`, `memory_recall`, `memory_correct`, `memory_forget`.
2.  Update `surface.py` metadata.
3.  Add CLI entrypoints.
4.  Add MCP tool definitions.
5.  Add integration tests.
6.  Fix `common.sh` prefix conflict.

## Validation Plan
- `pytest tests/test_user_surface.py`
- full regression suite for non-regression
- prerequisite checks for both the active `038` feature and the duplicate-prefix `035` workflow case

## Validation Evidence

Observed on 2026-03-24 after reviewing and reconciling feature `038-simple-user-surface`:

- `AegisApp` exposes `memory_remember`, `memory_recall`, `memory_correct`, and `memory_forget` as the thin non-technical surface.
- simplified CLI commands now support positional text arguments in addition to flag-based input, so `python -m aegis_py.cli remember "..."` works as documented.
- `memory_forget` now records an auditable lifecycle transition instead of mutating archive state with a raw SQL update.
- the existing `common.sh` exact-match branch-to-spec resolution is validated against the duplicate `035-*` prefix case.

Validation results:

- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_user_surface.py`
  - passed
  - `5 passed in 0.33s`
- `SPECIFY_FEATURE=035-semantic-memory-product-roadmap ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - resolved `FEATURE_DIR` to `/home/hali/.openclaw/extensions/memory-aegis-v7/specs/035-semantic-memory-product-roadmap`
- `SPECIFY_FEATURE=038-simple-user-surface ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - resolved `FEATURE_DIR` to `/home/hali/.openclaw/extensions/memory-aegis-v7/specs/038-simple-user-surface`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `112 passed in 2.76s`
