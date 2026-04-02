# Plan: 080 Truth Release Evidence Bundle

## Intent

Turn the existing truth evaluation outputs into one release-facing bundle without reopening any of the lower-level evaluation logic.

## Workstreams

### 1. Bundle Contract

- Define the manifest shape.
- Keep file references relative and repo-friendly.

### 2. Bundle Generator

- Read current truth artifacts.
- Persist a bundle manifest with status and file references.

### 3. Verification

- Add bundle-generation tests.
- Run benchmark, gate, report, bundle, and full suite.
