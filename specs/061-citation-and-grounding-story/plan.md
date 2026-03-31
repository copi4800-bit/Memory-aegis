# Implementation Plan: Citation And Grounding Story

**Branch**: `061-citation-and-grounding-story` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/061-citation-and-grounding-story/spec.md`

## Summary

Close the current product-facing tranche by turning Aegis explainability into a clear product story: one runnable grounding demo, one README section for trust/citations, and shipped artifacts that preserve that story.

## Technical Context

**Language/Version**: Python, Markdown, JSON tests  
**Primary Dependencies**: `aegis_py/app.py`, `aegis_py/cli.py`, `README.md`, `package.json`, `scripts/release-python-package.sh`, runtime/package tests  
**Storage**: temporary local SQLite DB created inside the demo script  
**Testing**: `pytest` targeted trust/package tests and full Python suite  
**Target Platform**: evaluators, maintainers, and package consumers  
**Constraints**: must use existing explain/provenance fields only; must stay grounded in current runtime outputs; must not invent richer trust signals than the runtime exposes  
**Scale/Scope**: one grounding demo, one README trust section, shipped-artifact updates, and tests

## Constitution Check

- **Local-First Memory Engine**: Pass. The trust demo remains local-first.
- **Brownfield Refactor Over Rewrite**: Pass. This is presentation over existing contracts.
- **Explainable Retrieval Is Non-Negotiable**: Pass. The slice reinforces this invariant directly.
- **Safe Memory Mutation By Default**: Pass. The demo uses ordinary store/search flows with explicit provenance.
- **Measured Simplicity**: Pass. The slice closes a trust gap without widening the surface.

## Source Areas

```text
extensions/memory-aegis-v7/
├── README.md
├── package.json
├── scripts/
│   ├── demo_grounded_recall.py
│   └── release-python-package.sh
├── tests/
│   ├── test_python_only_runtime_contract.py
│   ├── test_release_workflow.py
│   └── test_user_surface.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 061-citation-and-grounding-story/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Validation Plan

- Add a runnable grounding demo that prints provenance, trust state, trust reason, and reasons.
- Add a README trust/grounding section tied to current `search` and `context-pack` behavior.
- Ship the grounding demo in the package and release bundle.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "grounding or package or release"`
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "grounded_recall"`
  - `.venv/bin/python -m pytest -q tests/test_release_workflow.py`
  - `.venv/bin/python -m pytest -q tests`

## Validation Evidence

- `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "grounding or package or release"` -> `3 passed`
- `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "grounded_recall"` -> `1 passed`
- `.venv/bin/python -m pytest -q tests/test_release_workflow.py` -> `2 passed`
- `.venv/bin/python -m pytest -q tests` -> `188 passed`

## Expected Evidence

- one runnable grounding demo
- README trust/grounding section
- package and release artifacts include the grounding demo
- tests lock the trust story

## Complexity Tracking

No constitution violations currently require exception handling.
