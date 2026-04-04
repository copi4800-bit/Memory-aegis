# Phase 132 - OpenClaw Plugin Hardening

## Goal

Make TruthKeep behave like a coherent OpenClaw plugin package by aligning public commands, packaging metadata, manifest contracts, and first-run documentation.

## Scope

- Expose real public setup/check/MCP entrypoints under the `truthkeep-*` namespace.
- Align `pyproject.toml`, `package.json`, and `openclaw.plugin.json`.
- Add a minimal OpenClaw package metadata block so host-side loaders can discover the manifest.
- Update public docs to point to the real commands.
- Add packaging consistency tests and smoke verification.

## Non-Goals

- No retrieval, governance, truth-state, or storage math changes.
- No new memory features.
- No broad tool-surface redesign beyond plugin-hardening metadata.
