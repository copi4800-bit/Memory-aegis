# Implementation Plan: Consumer Install Readiness

**Branch**: `052-consumer-install-readiness` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/052-consumer-install-readiness/spec.md`

## Summary

Add a lightweight install preflight ahead of onboarding so new users can tell whether the Python runtime is ready and whether the OpenClaw plugin/bootstrap path is also ready. Keep the implementation local-first and repo-only.

## Technical Context

**Language/Version**: Python 3.13.x, existing Python bootstrap script, Markdown docs  
**Primary Dependencies**: `bin/aegis-setup`, `README.md`, Python stdlib (`sqlite3`, `subprocess`, `shutil`)  
**Storage**: N/A  
**Testing**: `pytest`  
**Target Platform**: current Aegis v4 local-first repo  
**Constraints**: must not require OpenClaw changes; must keep Python onboarding as the active production path; must distinguish runtime vs plugin readiness  
**Scale/Scope**: one install-preflight helper, one setup wrapper update, one README quickstart update, and tests

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   └── install_check.py
├── bin/
│   └── aegis-setup
├── README.md
└── tests/
    ├── test_user_surface.py
    └── test_python_only_runtime_contract.py
```

## Validation Plan

- Add tests for the install readiness report.
- Update runtime contract tests to lock the new quickstart/install surface.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py tests/test_python_only_runtime_contract.py`
  - `.venv/bin/python -m pytest -q tests`

## Validation Closeout

Validation run completed on 2026-03-28 for feature `052-consumer-install-readiness`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_user_surface.py tests/test_python_only_runtime_contract.py
npm run test:bootstrap
.venv/bin/python -m pytest -q tests
python3 ./bin/aegis-setup
```

Observed results:

- `23 passed in 1.14s` for targeted install/onboarding and runtime-contract coverage
- bootstrap contract test passed: `5/5`
- `167 passed in 4.14s` for the full Python suite
- `aegis-setup` now prints install preflight for Python, SQLite FTS5, Node, and npm before running onboarding

Validated additions in this feature:

- `aegis_py.install_check` now separates core runtime prerequisites from plugin/bootstrap prerequisites
- `aegis-setup` now tells new users whether the Python runtime is ready and whether the plugin/bootstrap path is also ready
- `README.md` now publishes a short “use both” quickstart for the Python runtime plus the current plugin/bootstrap path
