# Implementation Plan: Python CLI Surface

**Branch**: `009-python-cli-surface` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/009-python-cli-surface/spec.md)
**Input**: Feature specification from `/specs/009-python-cli-surface/spec.md`

## Summary

Add a host-agnostic Python CLI that wraps the existing Aegis public memory contract so external tools can use Aegis without OpenClaw or TypeScript adapters.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py`, standard-library `argparse`, existing runtime modules  
**Storage**: Existing local SQLite runtime paths and filesystem backup artifacts  
**Testing**: `pytest`, targeted CLI integration tests, existing bootstrap tests for non-regression  
**Target Platform**: Local Linux shell usage and scriptable host environments  
**Project Type**: Brownfield CLI addition to a Python memory engine  
**Performance Goals**: No meaningful regression to existing runtime paths; CLI startup remains lightweight  
**Constraints**: No new semantics, no OpenClaw dependency, JSON-first outputs for structured commands  
**Scale/Scope**: One standalone CLI entrypoint covering core and operational public surfaces

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. CLI is a local-only entrypoint.
- `Brownfield Refactor Over Rewrite`: Pass. The CLI wraps existing runtime behavior.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Search and context-pack outputs remain Python-owned.
- `Safe Memory Mutation By Default`: Pass. Backup and restore CLI commands reuse existing safe runtime flows.
- `Measured Simplicity`: Pass. One thin CLI is simpler than requiring every host to build its own bridge.

## Project Structure

### Documentation (this feature)

```text
specs/009-python-cli-surface/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── cli.py
├── app.py
├── surface.py
├── operations.py
└── ...

tests/
```

**Structure Decision**: Add a Python-native CLI module under `aegis_py/` that calls the existing `AegisApp` surfaces directly and emits stable JSON payloads where appropriate.

## Phase Plan

### Phase 0 - Command Mapping

Objective: Map current public runtime surfaces to CLI commands without introducing new semantics.

### Phase 1 - Core CLI Commands

Objective: Add CLI access for public surface inspection, status, store, search, and context-pack.

### Phase 2 - Operational CLI Commands

Objective: Add CLI access for backup and scope-policy workflows that already exist in the Python runtime.

## Validation Plan

- add CLI integration tests in the Python test suite
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py) now exposes a standalone Python CLI over the existing Aegis public surface
- the CLI wraps `surface`, `status`, `store`, `search`, `context-pack`, `backup-upload`, `backup-preview`, and `scope-policy` without requiring OpenClaw
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md) now documents standalone CLI usage for non-OpenClaw integrations
- [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) now includes subprocess-driven CLI integration coverage

Validation results:

- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `16` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `71 passed in 2.51s`
