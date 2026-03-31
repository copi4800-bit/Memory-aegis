# Tasks: Health States And Degraded Runtime Operation

**Input**: Design documents from `/specs/045-health-and-degraded-runtime/`
**Prerequisites**: `plan.md`, `spec.md`

## Phase 1: Health Contract

- [x] T001 [CORE] Define the canonical bounded health states and issue model in the Python-owned runtime.
- [x] T002 [CORE] Update status/doctor/public surface output so health state, issues, and capability flags are machine-readable.
- [x] T003 [TEST] Add tests for healthy, degraded, and broken state reporting.

## Phase 2: Degraded Runtime Behavior

- [x] T004 [OPS] Introduce or harden degraded-state handling for sync-adjacent or deferred workflows without blocking local store/search.
- [x] T005 [TEST] Add tests proving local writes and reads continue while degraded states are active.
- [x] T006 [TEST] Add tests proving broken local storage is reported distinctly from degraded optional-service issues.

## Phase 3: Surface Parity

- [x] T007 [DOCS] Align `README.md`, `aegis_py/surface.py`, `openclaw.plugin.json`, and any relevant adapter-facing status output with the new health contract.
- [x] T008 [TEST] Re-run runtime and adapter parity validation after the health contract lands.

## Phase 4: Closure

- [x] T009 [DOCS] Record closure evidence for `045-health-and-degraded-runtime`.
