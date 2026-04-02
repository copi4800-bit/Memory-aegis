# Feature Spec: 075 Truth Evaluation Gate

## Summary

Aegis needs a governed way to prove that its memory core still returns current truth under correction, conflict, lexical traps, and override pressure. This phase turns the existing spotlight benchmark into a release-facing evaluation gate.

## Problem

The repo now has spotlight demos and a benchmark artifact, but it still lacks a single governed success bar that says when truth behavior is strong enough to ship. Without that gate, the strongest part of the Aegis core is still easy to regress silently.

## Goals

- Define a release-facing truth evaluation contract for spotlight behavior.
- Turn spotlight benchmark output into an explicit pass/fail gate.
- Keep the gate narrow and core-focused: current truth selection, suppressed visibility, and stale-fact resistance.
- Make the gate easy to run locally and in CI.

## Non-Goals

- Rewriting retrieval or governance algorithms.
- Expanding into a broad benchmark lab for every memory workflow.
- Replacing the existing test suite with benchmark-only validation.

## User-Facing Outcome

Developers and operators can run one command and see whether the Aegis core still clears the current-truth bar expected for release.

## Acceptance Criteria

1. A single gate command fails when spotlight truth metrics fall below the configured threshold.
2. The gate consumes the benchmark artifact produced by `scripts/benchmark_truth_spotlight.py`.
3. The release/validation path documents when this gate must run.
4. The repo includes at least one automated verification path covering gate pass/fail behavior.

## Success Metrics

- `current_truth_top1_rate` must remain at or above the governed threshold.
- `suppressed_visibility_rate` must remain at or above the governed threshold.
- The gate must surface a human-readable failure summary when thresholds are missed.
