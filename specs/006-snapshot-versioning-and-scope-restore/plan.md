# Implementation Plan: Snapshot Versioning And Scope Restore

**Branch**: `006-snapshot-versioning-and-scope-restore` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore/spec.md)
**Input**: Feature specification from `/specs/006-snapshot-versioning-and-scope-restore/spec.md`

## Summary

Add backup manifests, snapshot listing, and restore dry-run to the Python-owned runtime so Aegis backup flows become auditable and safer than the current file-only snapshot/export behavior.

## Technical Context

**Language/Version**: Python 3.13.x with minimal host bootstrap glue  
**Primary Dependencies**: `aegis_py`, SQLite, filesystem manifests, existing MCP/bootstrap integration  
**Storage**: Local SQLite database plus backup artifacts under workspace-local backup directories  
**Testing**: `pytest` for Python runtime behavior, targeted bootstrap regression for host-facing tools  
**Target Platform**: Local OpenClaw plugin environment on Linux  
**Project Type**: Brownfield extension of the existing Python-only runtime  
**Performance Goals**: Backup listing and dry-run restore remain fast enough for local interactive use on typical developer workspaces  
**Constraints**: Must stay local-first, must not mutate on dry-run, must fail closed on invalid manifests or incompatible backups  
**Scale/Scope**: One focused backup/versioning feature slice on top of feature `005`

## Constitution Check

*GATE: Must pass before implementation.*

- `Local-First Memory Engine`: Pass. All artifacts remain filesystem-local.
- `Brownfield Refactor Over Rewrite`: Pass. This extends the existing backup helpers rather than replacing the runtime.
- `Explainable Retrieval Is Non-Negotiable`: N/A directly, but backup manifests and dry-run restore improve explainability of operational state.
- `Safe Memory Mutation By Default`: Pass. Dry-run restore is explicitly non-mutating and restore validation fails closed.
- `Measured Simplicity`: Pass with caution. Versioning stays file/manifest based and avoids introducing external services.

## Project Structure

### Documentation (this feature)

```text
specs/006-snapshot-versioning-and-scope-restore/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
aegis_py/
├── app.py
├── mcp/server.py
└── ...

src/
├── python-adapter.ts
└── ...

tests/
test/integration/
```

**Structure Decision**: Keep the implementation centered in `aegis_py/app.py` and `aegis_py/mcp/server.py`, with only thin bridging changes in `src/python-adapter.ts` and host bootstrap wiring where needed.

## Phase Plan

### Phase 0 - Existing Backup Behavior Audit

Objective: Document the current Python backup/export/restore behavior and the gaps relative to the new spec.

Observed repository evidence on 2026-03-24:

- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) currently supports snapshot/export backup creation and restore but without manifests, listing, or dry-run preview.
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) exposes backup upload/download but not backup listing or restore preview.
- [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) already routes backup creation and restore through Python.

Planning implication:

- the feature can extend the current Python runtime directly without reopening the TypeScript engine question
- the safest first slice is manifests + list + dry-run rather than full scope-selective restore in one wave

### Phase 1 - Manifested Backups

Objective: Ensure every backup artifact created by the Python runtime has a companion manifest with enough metadata to support listing and validation.

Expected outputs:

- manifest writer in `aegis_py/app.py`
- manifest-backed snapshot/export creation
- tests that assert manifest presence and required fields

### Phase 2 - Listing And Dry-Run Restore

Objective: Add snapshot history navigation and restore preview without changing the mutation semantics of real restore.

Expected outputs:

- Python list-backups surface
- Python restore preview surface
- host/bootstrap bridges for these operations if needed
- tests for invalid manifests and non-mutating dry-run behavior

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| No scope-selective restore in the first slice | Keeps the first version auditable and lower-risk | Jumping straight to selective restore would increase mutation complexity before manifest/preview safety exists |

## Validation Evidence

Observed on 2026-03-24:

- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now writes manifest files for snapshot and export backups, lists manifest-backed backups, and exposes non-mutating restore preview
- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) now also supports scope-selective restore preview and scope-selective restore while preserving unrelated scopes
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) now exposes `memory_backup_list` and `memory_backup_preview`
- [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) now route backup listing, dry-run restore preview, and selective scope restore through Python-owned paths
- [tests/test_integration.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) adds regression coverage for manifests, listing, and non-mutating restore preview
- [test/integration/python-adapter-plugin.test.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/test/integration/python-adapter-plugin.test.ts) adds host/bootstrap regression coverage for backup list and preview routing

Validation results:

- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `12` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 /home/hali/.openclaw/extensions/memory-aegis-v7/.venv/bin/pytest -q tests`
  - passed: `65 passed in 1.05s`

Current residual risks:

- scope-selective restore currently restores scope-owned `memories` rows plus snapshot-backed `style_signals` and `style_profiles`; conflict/link state is still not replayed selectively and export backups still do not carry auxiliary scope metadata
- backup validity still relies on local filesystem trust and manifest consistency; checksums and signed manifests are not yet implemented
