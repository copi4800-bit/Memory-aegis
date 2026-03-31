# Implementation Plan: Default Surface Consistency

**Branch**: `054-default-surface-consistency` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/054-default-surface-consistency/spec.md`

## Summary

 Tighten the governed consumer surface by making `memory_setup` publish consistently as a first-class default operation and by eliminating advanced host-surface drift where Python-owned sync operations were missing from host publish layers. This remains a narrow contract-alignment refinement, not a new capability wave.

## Technical Context

**Language/Version**: Python 3.13.x, TypeScript/compiled JS artifacts, Markdown docs  
**Primary Dependencies**: `aegis_py/surface.py`, `aegis_py/mcp/server.py`, `src/python-adapter.ts`, `index.ts`, `dist/`, `README.md`, contract tests  
**Storage**: N/A  
**Testing**: targeted Python contract checks and artifact import/syntax checks; full `pytest` remains the canonical suite when available  
**Target Platform**: current Aegis v4 Python-owned local-first runtime and OpenClaw host adapter  
**Constraints**: must preserve the existing bounded consumer surface; must not re-open retired TS-era semantics; must keep shipped artifacts aligned with source truth  
**Scale/Scope**: one narrow consistency slice for the consumer host/runtime surface, covering default and advanced parity

## Constitution Check

- **Local-First Memory Engine**: Pass. The work preserves the Python-owned local-first path.
- **Brownfield Refactor Over Rewrite**: Pass. This is alignment work across existing surfaces and artifacts.
- **Explainable Retrieval Is Non-Negotiable**: Pass. Retrieval behavior is untouched.
- **Safe Memory Mutation By Default**: Pass. The feature clarifies onboarding exposure, not mutation semantics.
- **Measured Simplicity**: Pass. The sole purpose is to reduce ambiguity in the default user path.

## Source Areas

```text
extensions/memory-aegis-v7/
├── README.md
├── aegis_py/
│   ├── surface.py
│   └── mcp/server.py
├── src/
│   └── python-adapter.ts
├── dist/
│   ├── index.js
│   └── src/
│       ├── python-adapter.js
│       └── python-adapter.d.ts
├── test/
│   └── integration/python-adapter-plugin.test.ts
└── tests/
    └── test_app_surface.py
```

## Validation Plan

- Lock `memory_setup` into the Python default consumer contract.
- Verify the MCP server dispatch path exposes `memory_setup` and the already-published sync operations.
- Verify shipped host artifacts export the onboarding bridge and register the governed consumer surface, including sync tools missing from prior host layers.
- Add cross-surface assertions so the manifest default and advanced tool lists match the Python public surface and the host runtime registry.
- Reduce internal duplication by making Python surface operation lists canonical for tests and by deriving host runtime tool-name registration from the tool registry instead of a second hardcoded list.
- Re-run:
  - `python3 -m unittest tests/test_app_surface.py -k test_plugin_manifest_advanced_tools_match_python_public_surface`
  - `python3 -m unittest tests/test_app_surface.py -k test_plugin_manifest_default_tools_match_python_public_surface`
  - `python3 -m unittest tests/test_app_surface.py -k test_public_surface_declares_bounded_health_contract`
  - `python3 -m unittest tests/test_app_surface.py -k test_readme_and_plugin_manifest_publish_same_health_contract`
  - `node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts`
  - `node --input-type=module -e 'import "./dist/src/python-adapter.js"; import "./dist/index.js"; console.log("ok")'`

## Expected Evidence

- Python public surface publishes `memory_setup` in `consumer_contract.default_operations`
- Python public surface advanced operations, including sync tools, match host-published metadata
- MCP `run_tool` recognizes `memory_setup` and the sync operations
- plugin manifest `consumerSurface.defaultTools` matches the Python public surface default operations
- plugin manifest `consumerSurface.advancedTools` matches the Python public surface advanced operations
- host integration test proves `memory_setup` routes through `onboardingViaPython`
- host integration test proves every manifest default tool is actually registered at runtime
- host integration test proves every manifest advanced tool is actually registered at runtime
- `dist/` artifacts expose `onboardingViaPython` and register `memory_setup`
- contract assertions include `memory_setup` in the default list

## Validation Closeout

Validation run completed on 2026-03-28 for feature `054-default-surface-consistency`.

Executed commands:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
python3 -m unittest tests/test_app_surface.py -k test_plugin_manifest_advanced_tools_match_python_public_surface
python3 -m unittest tests/test_app_surface.py -k test_plugin_manifest_default_tools_match_python_public_surface
python3 -m unittest tests/test_app_surface.py -k test_public_surface_declares_bounded_health_contract
python3 -m unittest tests/test_app_surface.py -k test_readme_and_plugin_manifest_publish_same_health_contract
node_modules/.bin/vitest run test/integration/python-adapter-plugin.test.ts
node --input-type=module -e 'import "./dist/src/python-adapter.js"; import "./dist/index.js"; console.log("ok")'
```

Observed results:

- `test_plugin_manifest_advanced_tools_match_python_public_surface` passed
- `test_plugin_manifest_default_tools_match_python_public_surface` passed
- `test_public_surface_declares_bounded_health_contract` passed
- `test_readme_and_plugin_manifest_publish_same_health_contract` passed
- `python-adapter-plugin.test.ts` passed with `8/8` tests
- `dist` import check printed `ok`

Validated additions in this feature:

- `memory_setup` is now part of the Python-owned default consumer contract
- the MCP server exposes `memory_setup` as a first-class tool path and already-aligned sync tools remain callable through the same Python-owned contract
- the manifest default tool list is now explicitly locked against the Python public surface
- the manifest advanced tool list is now explicitly locked against the Python public surface
- the host integration test now locks `memory_setup` as a Python-routed runtime tool, not just manifest metadata
- the host integration test now also proves every manifest default tool appears in the runtime registry
- the host adapter and shipped artifacts now publish the previously missing sync tools so advanced parity matches the Python contract
- Python surface operation lists now act as the canonical consumer-surface constants for contract tests
- host runtime tool registration names are now derived from the built tool registry instead of maintained as a separate manual list
- shipped host artifacts now register `memory_setup` and export the onboarding bridge used by that tool
- the consumer-surface contract tests now lock both default and advanced operation lists against the governed Python source of truth

## Complexity Tracking

No constitution violations currently require exception handling.
