# Plan: 086 Ingest Policy Readiness

## Intent

Define when the admission branch is safe to close for the current deployment class.

## Workstreams

### 1. Diagnostic Contrast

- Extend the ingest diagnostic to include a high-confidence distinct-write scenario.
- Keep the low-confidence repetitive scenario as the protective baseline.

### 2. Readiness Gate

- Add a thin verdict script with explicit pass/fail rules.
- Keep it artifact-first and deterministic.

### 3. Verification

- Add focused tests for the readiness logic.
- Keep the full suite green.
