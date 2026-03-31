# Implementation Plan: Demo And Benchmark Presentation

**Branch**: `058-demo-and-benchmark-presentation` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/058-demo-and-benchmark-presentation/spec.md`

## Summary

Execute the next Tranche B slice by making Aegis easier to demo and easier to benchmark-read. This slice adds one runnable first-value demo script and one clearer README section that translates benchmark gates into product-facing language.

## Technical Context

**Language/Version**: Python and Markdown  
**Primary Dependencies**: `README.md`, `scripts/benchmark_*.ts`, existing Python CLI/setup flow, runtime-contract tests  
**Storage**: local SQLite via existing CLI/runtime paths  
**Testing**: `pytest` for README/demo contract coverage  
**Target Platform**: newcomer demos and maintainer benchmark storytelling  
**Constraints**: must stay tied to real repo scripts; must preserve the Python-owned newcomer path; should avoid fake or hand-wavy benchmark claims  
**Scale/Scope**: one demo script, README demo/benchmark sections, and targeted test coverage

## Constitution Check

- **Local-First Memory Engine**: Pass. The demo remains local-first.
- **Brownfield Refactor Over Rewrite**: Pass. This is presentation and scripting over existing flows.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Benchmark messaging stays grounded in explainable retrieval gates.
- **Safe Memory Mutation By Default**: Pass. The demo uses beginner-safe default verbs.
- **Measured Simplicity**: Pass. The slice improves demoability without broadening the core surface.

## Source Areas

```text
extensions/memory-aegis-v7/
├── README.md
├── scripts/
│   ├── demo_first_memory.py
│   ├── benchmark_dragonfly.ts
│   └── benchmark_weaver.ts
├── tests/
│   ├── test_python_only_runtime_contract.py
│   └── test_user_surface.py
├── .planning/
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 058-demo-and-benchmark-presentation/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Validation Plan

- Add `scripts/demo_first_memory.py` as a runnable newcomer demo.
- Add README sections that explain how to run the demo and what benchmark scripts currently prove.
- Add or update tests for README demo/benchmark language and demo-script output.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "storytelling or demo or benchmark"`
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "demo_first_memory"`
  - `.venv/bin/python -m pytest -q tests`

## Validation Evidence

- `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "storytelling or demo or benchmark"` -> `2 passed`
- `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "demo_first_memory"` -> `1 passed`
- `.venv/bin/python -m pytest -q tests` -> `183 passed`

## Expected Evidence

- one runnable newcomer demo script
- README demo section tied to that script
- README benchmark summary tied to current benchmark scripts/gates
- tests locking the new presentation

## Complexity Tracking

No constitution violations currently require exception handling.
