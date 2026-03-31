# Implementation Plan: Production Hardening

**Branch**: `070-production-hardening` | **Date**: 2026-03-29 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/070-production-hardening/spec.md)
**Input**: Feature specification from `/specs/070-production-hardening/spec.md`

## Summary

Harden the already-working Aegis v7 runtime by adding acceptance coverage for critical flows, explicit regression coverage for known failure classes, and invariant-focused tests for dry-run safety, rollback safety, restore safety, and scope isolation.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: stdlib, sqlite3, pytest  
**Storage**: SQLite with local temporary databases and workspaces  
**Testing**: pytest  
**Target Platform**: Linux local runtime  
**Project Type**: library plus CLI/runtime tests  
**Performance Goals**: Keep the acceptance suite focused enough to run locally while still covering the highest-signal production flows  
**Constraints**: No live network dependency, no dependence on Telegram uptime, no rewrite of the runtime architecture during this tranche  
**Scale/Scope**: test and validation hardening within the Python-owned runtime

## Constitution Check

- Preserve the Python-owned runtime boundary.
- Prefer proof of behavior over net-new feature breadth.
- Keep the tranche narrow: acceptance, regression, invariants.

## Project Structure

### Documentation (this feature)

```text
specs/070-production-hardening/
├── plan.md
├── spec.md
└── tasks.md
```

### Source Code (repository root)

```text
tests/
├── acceptance/
├── regression/
├── test_integration.py
├── test_v7_runtime.py
└── test_storage.py

scripts/
└── smoke/
```

**Structure Decision**: Keep this tranche test-heavy. Prefer new acceptance/regression modules and minimal helper code over touching the runtime unless the hardening work reveals a real behavioral defect.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New acceptance/regression test slices | Needed to separate production-critical checks from broad general-purpose suites | Reusing only the broad existing test files would make release-critical behavior harder to audit quickly |

## Expected Deliverables

- Focused acceptance tests for critical flows.
- Regression tests for selected known failure classes.
- Invariant checks for dry-run, rollback, restore, and scope isolation.
- A documented validation command set for this tranche.

## Selected Regression Classes

- Dry-run and preview non-mutation: lock the rule that inspection-only paths cannot change durable rows or revision-sensitive state.
- Governed rollback integrity: lock the rule that a successful background apply can be fully reversed, including neighbor graph changes, while the persisted run record returns to the runtime's `discarded` terminal state with rollback evidence attached.
- Scope-policy and sync stability: lock the rule that sync-eligible policy remains usable for export, preview, and import flows without silent contract drift.
- Restore contract stability: lock the rule that backup restore into a separate database preserves the expected records and operator-visible metadata.

## Validation Commands

Run the focused hardening tranche with:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q tests/acceptance tests/regression
```

Run the broader supporting confidence checks with:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_v7_runtime.py tests/test_retrieval.py tests/test_storage.py tests/test_user_surface.py tests/test_workflow_governance.py tests/test_python_only_runtime_contract.py
PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_integration.py -k 'scope_policy_defaults_local_only_and_lists_explicit_sync_eligible or python_cli_sync_export_preview_import'
```

## Remaining Gaps After This Tranche

- Telegram and gateway soak behavior still needs long-run validation outside local pytest coverage.
- Restore has contract coverage, but not yet a timed operational drill against a larger, production-shaped dataset.
- Sync coverage is strong for local envelopes, but not yet multi-node or adversarial import scenarios.
- This tranche improves trust; it does not replace staging, canary rollout, or runtime metrics/alerts.
