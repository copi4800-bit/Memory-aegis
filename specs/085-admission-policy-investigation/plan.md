# Plan: 085 Admission Policy Investigation

## Intent

Turn the ingest-pressure signal into an understandable engineering finding.

## Workstreams

### 1. Decision Trace

- Identify where repeated writes become `no_op` or rejected.
- Capture the reasons in a stable diagnostic shape.

### 2. Diagnostic Surface

- Add a lightweight script or helper for repeated-ingest diagnosis.
- Reuse current runtime paths instead of duplicating logic.

### 3. Verification

- Add focused tests.
- Keep the full suite green.
