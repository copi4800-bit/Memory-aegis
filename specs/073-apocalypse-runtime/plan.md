# Implementation Plan: Apocalypse Runtime

## Slice

Build one compatibility-first operator harness instead of broad new runtime semantics.

## Work

1. Add `scripts/apocalypse_v7.py` with importable helpers and CLI
2. Reuse current `AegisApp` backup/restore and retrieval paths
3. Add bounded retries for SQLite busy/locked pressure instead of treating transient locks as hard failure
4. Add one reduced-profile test under `tests/`

## Validation

- `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_apocalypse_runtime.py`
- Optionally run `PYTHONPATH=. .venv/bin/python scripts/apocalypse_v7.py --profile quick`
