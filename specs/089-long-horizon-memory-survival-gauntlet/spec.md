# Feature Spec: 089 Long Horizon Memory Survival Gauntlet

## Summary

Stress Aegis across simulated 90-day and 1-year memory lifecycles to test whether current truth survives while stale and noisy data gets cleaned up.

## Problem

Short deterministic gauntlets are not enough to prove that Aegis will stay healthy over long-lived memory horizons. The repo needs bounded evidence that truth survives while stale rows and DB footprint stay under control.

## Goals

- Simulate long-horizon memory aging with real decay, retention, archive, hygiene, and compaction primitives.
- Measure whether current truth remains retrievable after cleanup.
- Measure whether stale/archived/superseded noise is actually removed.

## Non-Goals

- Real wall-clock soak tests.
- Distributed or multi-process concurrency stress.
- Rewriting retention thresholds in this phase.

## Acceptance Criteria

1. The repo gains a long-horizon survival gauntlet covering at least `90` and `365` day horizons.
2. The gauntlet proves current truth survives the cleanup flow.
3. The gauntlet records evidence that stale rows are compacted.
