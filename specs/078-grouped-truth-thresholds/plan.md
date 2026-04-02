# Plan: 078 Grouped Truth Thresholds

## Intent

Protect Aegis core behavior at the capability-group level without broadening the evaluation system beyond the existing benchmark artifact.

## Workstreams

### 1. Contract

- Define default grouped thresholds for each current category.
- Keep the defaults strict but aligned with current benchmark reality.

### 2. Gate Runtime

- Extend the gate script to read `grouped_summary`.
- Fail when a category misses its required pass rate or visibility bar.

### 3. Verification

- Add grouped gate tests.
- Re-run benchmark, gate, report, and full suite.
