# Feature Spec: 078 Grouped Truth Thresholds

## Summary

Aegis already reports grouped truth-evaluation results by capability. This phase turns those grouped results into governed thresholds so each core strength area must hold its own bar.

## Problem

A single overall pass rate can hide weakness inside one category. Aegis needs explicit per-group bars for correction, conflict, override, and lexical resilience so regressions are easier to catch before release.

## Goals

- Extend the truth spotlight gate with grouped thresholds.
- Keep the current summary thresholds intact while adding category-level checks.
- Make grouped failures human-readable in the gate output.

## Non-Goals

- Adding new benchmark scenarios in this phase.
- Reworking the grouped summary shape.
- Creating category-specific CI jobs.

## Acceptance Criteria

1. The truth spotlight gate checks grouped thresholds in addition to overall thresholds.
2. A grouped threshold miss fails the gate.
3. The gate output clearly identifies which category regressed.
4. Tests cover grouped pass/fail behavior.
