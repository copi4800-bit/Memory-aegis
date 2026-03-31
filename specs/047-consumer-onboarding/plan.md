# Implementation Plan: Consumer Onboarding

**Branch**: `047-consumer-onboarding` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/047-consumer-onboarding/spec.md`

## Summary

Implement the first production onboarding flow for non-technical users on top of the Python-owned runtime. The onboarding path will run real local checks for DB availability, write success, recall success, and runtime health, and the existing `aegis-setup` wrapper will call that flow instead of the raw MCP self-test path.

## Technical Context

**Language/Version**: Python 3.13.x and existing TypeScript wrapper  
**Primary Dependencies**: `aegis_py.app`, `aegis_py.cli`, existing health contract, existing setup wrapper in `src/cli/setup.ts`  
**Storage**: SQLite local DB  
**Testing**: `pytest`, existing repo contract tests, targeted CLI/user-surface tests  
**Target Platform**: current OpenClaw local-first runtime and CLI bootstrap  
**Project Type**: runtime surface and onboarding hardening  
**Performance Goals**: onboarding should complete in a normal local environment without noticeable delay; no benchmark changes are required  
**Constraints**: must stay on the Python-owned production path; must not leave misleading onboarding probe data behind; must explain degraded versus broken states in plain language  
**Scale/Scope**: one bounded onboarding flow, one CLI entrypoint, one setup wrapper update

## Constitution Check

- **Local-First Memory Engine**: Pass. The onboarding path checks local DB, local write, and local recall with no cloud dependency.
- **Brownfield Refactor Over Rewrite**: Pass. The feature extends the existing Python runtime and current setup wrapper rather than replacing the architecture.
- **Explainable Retrieval Is Non-Negotiable**: Pass. The onboarding flow relies on the existing retrieval and health contract rather than bypassing them.
- **Safe Memory Mutation By Default**: Pass. The onboarding write probe is bounded and cleaned up so the setup flow does not silently pollute long-term memory.
- **Measured Simplicity**: Pass. The feature narrows setup to a small number of understandable checks and keeps advanced configuration out of the first-run path.

## Source Areas

```text
extensions/memory-aegis-v7/
├── aegis_py/
│   ├── app.py
│   ├── cli.py
│   └── mcp/server.py
├── src/
│   └── cli/setup.ts
├── tests/
│   ├── test_user_surface.py
│   └── test_python_only_runtime_contract.py
└── specs/
    ├── 046-consumer-ready-checklist/
    └── 047-consumer-onboarding/
```

## Validation Plan

- Add tests for successful onboarding on a fresh DB.
- Add tests for degraded or broken onboarding explanations.
- Update setup-wrapper contract tests so they require the Python onboarding path instead of the raw MCP self-test path.
- Re-run:
  - `.venv/bin/python -m pytest -q tests/test_user_surface.py tests/test_python_only_runtime_contract.py`
  - `.venv/bin/python -m pytest -q tests`

## Expected Evidence

- Python-owned onboarding report and plain-language summary
- setup wrapper invoking the Python onboarding command
- user-surface tests for onboarding success and failure/degraded explanation

## Validation Closeout

Validation run completed on 2026-03-28 for feature `047-consumer-onboarding`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python -m pytest -q tests/test_user_surface.py tests/test_python_only_runtime_contract.py
.venv/bin/python -m pytest -q tests
```

Observed results:

- `12 passed in 0.51s` for targeted onboarding and setup-wrapper coverage
- `154 passed in 3.36s` for the full Python suite

Validated additions in this feature:

- Python-owned onboarding now runs real local DB, write, recall, and health checks
- `aegis_py.cli onboarding` exposes both plain-language output and JSON payload output
- `src/cli/setup.ts` now invokes the Python onboarding command instead of the raw MCP self-test path
- degraded sync states are reported as usable local runtime during onboarding rather than as a hard failure

Remaining gaps after this slice:

- onboarding is now active on the Python path, but broader consumer UX still exposes advanced operational concepts outside setup
- backup, restore, and diagnostics remain more developer-oriented than ordinary-user-oriented

## Complexity Tracking

No constitution violations currently require exception handling.
