# Tasks: Default Surface Consistency

**Input**: Design documents from `/specs/054-default-surface-consistency/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Python Contract Alignment

- [x] T001 [CORE] Publish `memory_setup` in `aegis_py/surface.py` as part of `consumer_contract.default_operations`.
- [x] T002 [CORE] Expose and dispatch `memory_setup` in `aegis_py/mcp/server.py` through `app.onboarding(...)`.

## Phase 2: Host Artifact Alignment

- [x] T003 [DOCS] Align `README.md` with the governed default operations list including `memory_setup`.
- [x] T004 [CORE] Ensure the shipped host adapter/artifacts expose `memory_setup`, the onboarding bridge needed to execute it, and the advanced sync tools already published by the Python contract.

## Phase 3: Contract Locking

- [x] T005 [TEST] Update `tests/test_app_surface.py` to compare both manifest default tools and manifest advanced tools against the Python public surface.
- [x] T006 [TEST] Update `test/integration/python-adapter-plugin.test.ts` so `memory_setup` is locked as a Python-routed host tool and every manifest default/advanced tool is required in the runtime registry.
- [x] T007 [TEST] Re-run targeted Python contract checks, host integration coverage, and a `dist` import check for the built host artifacts.

## Phase 4: Duplication Reduction

- [x] T008 [CORE] Extract canonical consumer operation lists in `aegis_py/surface.py` so tests reuse one Python-owned source.
- [x] T009 [CORE] Derive host runtime `toolNames` from the registered tool list instead of maintaining a second manual allowlist in `index.ts` and `dist/index.js`.
