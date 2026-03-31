# Implementation Plan: Integration Story

**Branch**: `060-integration-story` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/060-integration-story/spec.md`

## Summary

Turn the service-boundary contract into a clearer product story by adding one runnable integration demo and one concise README quickstart for thin hosts.

## Technical Context

**Language/Version**: Python, Markdown, JSON tests  
**Primary Dependencies**: `aegis_py/mcp/server.py`, `README.md`, `package.json`, `scripts/release-python-package.sh`, integration/runtime tests  
**Storage**: temporary local SQLite DB created through the existing Python service boundary  
**Testing**: `pytest` targeted integration/package tests and full Python suite  
**Target Platform**: thin hosts and local integrators  
**Constraints**: must use the existing Python-owned boundary; must not reintroduce TS-owned memory semantics; must stay runnable locally  
**Scale/Scope**: one integration demo script, README quickstart, shipped-artifact updates, and tests

## Constitution Check

- **Local-First Memory Engine**: Pass. The demo uses the local Python boundary only.
- **Brownfield Refactor Over Rewrite**: Pass. This is a documentation and scripting slice over current surfaces.
- **Explainable Retrieval Is Non-Negotiable**: Pass. No retrieval semantics are weakened.
- **Safe Memory Mutation By Default**: Pass. The demo uses ordinary-user setup/remember/recall flows.
- **Measured Simplicity**: Pass. The slice makes the host path easier to follow without widening the public surface.

## Source Areas

```text
extensions/memory-aegis-v7/
├── README.md
├── package.json
├── scripts/
│   ├── demo_first_memory.py
│   ├── demo_integration_boundary.py
│   └── release-python-package.sh
├── tests/
│   ├── test_python_only_runtime_contract.py
│   ├── test_release_workflow.py
│   └── test_user_surface.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 060-integration-story/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Validation Plan

- Add a runnable integration demo script that exercises `--service-info`, `--startup-probe`, and `--tool`.
- Add a README integration quickstart section tied to the real local service contract.
- Update shipped-artifact paths for the integration demo.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "integration or package or release"`
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "integration_boundary"`
  - `.venv/bin/python -m pytest -q tests/test_release_workflow.py`
  - `.venv/bin/python -m pytest -q tests`

## Validation Evidence

- `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "integration or package or release"` -> `3 passed`
- `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "integration_boundary"` -> `1 passed`
- `.venv/bin/python -m pytest -q tests/test_release_workflow.py` -> `2 passed`
- `.venv/bin/python -m pytest -q tests` -> `186 passed`

## Expected Evidence

- one runnable integration demo script
- README quickstart tied to `--service-info`, `--startup-probe`, and `--tool`
- package and release artifacts include the integration demo
- tests lock the integration story

## Complexity Tracking

No constitution violations currently require exception handling.
