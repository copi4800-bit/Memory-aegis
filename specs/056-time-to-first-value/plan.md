# Implementation Plan: Time To First Value

**Branch**: `056-time-to-first-value` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/056-time-to-first-value/spec.md`

## Summary

Execute Tranche A from the adoption roadmap by publishing and validating the shortest meaningful newcomer path through Aegis. The goal is to get a user from install and setup to one successful remember/recall flow quickly, without burying them in advanced surfaces.

## Technical Context

**Language/Version**: Markdown, existing Python setup script, existing Python CLI/user-facing surfaces  
**Primary Dependencies**: `.planning/AEGIS-ADOPTION-ROADMAP.md`, `README.md`, `bin/aegis-setup`, `specs/047-consumer-onboarding/`, `specs/048-consumer-everyday-surface/`, `specs/052-consumer-install-readiness/`, user-surface and runtime-contract tests  
**Storage**: N/A  
**Testing**: `pytest` and existing host integration coverage  
**Target Platform**: newcomer-facing setup and quickstart workflow  
**Constraints**: must preserve the bounded default consumer path; must not reintroduce advanced-tool-first onboarding; should stay honest about the current product state  
**Scale/Scope**: beginner quickstart/docs, first-success setup guidance, and validation coverage

## Constitution Check

- **Local-First Memory Engine**: Pass. The slice focuses on local-first first success.
- **Brownfield Refactor Over Rewrite**: Pass. This is roadmap/scoping work, not a runtime rewrite.
- **Explainable Retrieval Is Non-Negotiable**: Pass. The first-value path should stay compatible with explainable retrieval.
- **Safe Memory Mutation By Default**: Pass. The first-value path uses governed default verbs.
- **Measured Simplicity**: Pass. This slice is explicitly about newcomer simplicity.

## Source Areas

```text
extensions/memory-aegis-v7/
├── README.md
├── bin/
│   └── aegis-setup
├── tests/
│   ├── test_python_only_runtime_contract.py
│   └── test_user_surface.py
├── .planning/
│   ├── AEGIS-ADOPTION-ROADMAP.md
│   ├── ROADMAP.md
│   └── STATE.md
└── specs/
    └── 056-time-to-first-value/
        ├── spec.md
        ├── plan.md
        └── tasks.md
```

## Validation Plan

- Publish a beginner-first quickstart in `README.md`.
- Make `aegis-setup` print explicit first-value next steps after onboarding.
- Add test coverage for the quickstart language and setup next-step output.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "quickstart or first_memory"`
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py -k "onboarding_cli or aegis_setup"`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`
  - `.venv/bin/python -m pytest -q tests`

## Expected Evidence

- `README.md` contains a newcomer-first “5-Minute First Memory” flow
- `aegis-setup` ends with explicit remember/recall/status next steps
- tests lock the beginner quickstart and first-value setup output
- roadmap/state references show `056-time-to-first-value` as the first execution slice from the adoption roadmap

## Validation Closeout

Validation run completed on 2026-03-28 for feature `056-time-to-first-value`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_python_only_runtime_contract.py -k "quickstart or first_memory"
.venv/bin/python -m pytest -q tests/test_user_surface.py -k "onboarding_cli or aegis_setup"
node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts
.venv/bin/python -m pytest -q tests
```

Observed results:

- `2 passed, 7 deselected` for quickstart/runtime-contract coverage
- `3 passed, 16 deselected` for onboarding/setup user-surface coverage
- `8/8` tests passed in `python-adapter-plugin.test.ts`
- `180 passed in 4.60s` for the full Python suite

Validated additions in this feature:

- the README now publishes a clear newcomer “5-Minute First Memory” path
- `aegis-setup` now prints explicit first-value next steps after setup completes
- newcomer-facing tests now lock both the quickstart guidance and the setup output

## Complexity Tracking

No constitution violations currently require exception handling.
