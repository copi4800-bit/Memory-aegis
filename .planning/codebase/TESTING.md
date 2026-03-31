# Testing

## Framework
- **Primary**: `pytest`
- **Secondary**: `vitest` only for transitional host/bootstrap coverage

## Test Suites
- **Python integration**: `tests/`
- **Repository host/bootstrap tests**: `test/`
- **Benchmark and retrieval quality**: Python benchmark and regression tests

## Commands
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
- `npm run test:bootstrap`
