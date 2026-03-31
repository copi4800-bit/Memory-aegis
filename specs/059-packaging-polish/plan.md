# Implementation Plan: Packaging Polish

**Branch**: `059-packaging-polish` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/059-packaging-polish/spec.md`

## Summary

Improve the release and published-package story so Aegis ships with the assets a newcomer actually needs: setup, a runnable demo, a clear quickstart note, and packaging documentation that matches reality.

## Technical Context

**Language/Version**: Bash, JSON, Markdown, Python tests  
**Primary Dependencies**: `scripts/release-python-package.sh`, `package.json`, `README.md`, release/runtime contract tests  
**Storage**: release tarball under `dist/python-release/`  
**Testing**: `pytest` targeted release/runtime tests and full Python suite  
**Target Platform**: local release bundle consumers and npm package consumers  
**Constraints**: preserve Python-first story; avoid promising non-shipped artifacts; keep release helper local and deterministic  
**Scale/Scope**: one release script polish slice, README update, package file-list update, and tests

## Constitution Check

- **Local-First Memory Engine**: Pass. Packaging remains local-first.
- **Brownfield Refactor Over Rewrite**: Pass. This is a release-path refinement.
- **Explainable Retrieval Is Non-Negotiable**: Pass. No retrieval semantics change.
- **Safe Memory Mutation By Default**: Pass. Packaging changes do not widen mutation behavior.
- **Measured Simplicity**: Pass. The slice reduces unpack-and-try friction.

## Source Areas

```text
extensions/memory-aegis-v7/
├── README.md
├── package.json
├── scripts/
│   └── release-python-package.sh
├── tests/
│   ├── test_python_only_runtime_contract.py
│   └── test_release_workflow.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 059-packaging-polish/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Validation Plan

- Update release packaging to include setup/demo/newcomer guidance assets.
- Update README release section and package file-list expectations.
- Add or update tests for package file-list and release bundle contents.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "package or release"`
  - `.venv/bin/python -m pytest -q tests/test_release_workflow.py`
  - `.venv/bin/python -m pytest -q tests`

## Validation Evidence

- `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "package or release"` -> `2 passed`
- `.venv/bin/python -m pytest -q tests/test_release_workflow.py` -> `2 passed`
- `.venv/bin/python -m pytest -q tests` -> `184 passed`

## Expected Evidence

- release tarball includes setup/demo/newcomer guidance artifacts
- README explains shipped packaging contents and first steps
- published package file-list preserves Python-first assets
- tests lock the package story

## Complexity Tracking

No constitution violations currently require exception handling.
