# Feature Spec: 079 Truth Scenario Catalog And Trend

## Summary

Aegis now has truth benchmark artifacts, grouped thresholds, and a readable report. This phase adds a formal scenario catalog and a lightweight historical trend section so releases show both what each scenario means and how the core is moving over time.

## Problem

Current truth reports show metrics and scenario outcomes, but they do not clearly explain what each scenario is testing or how today's artifact compares with the previous one.

## Goals

- Add a formal scenario catalog to the truth benchmark artifact.
- Add a historical trend section to the truth report using a previous artifact when available.
- Fix scenario status rendering so report output reflects pass/fail directly.

## Non-Goals

- Building a multi-run dashboard.
- Adding new scenario groups in this phase.
- Replacing the existing comparison script.

## Acceptance Criteria

1. The benchmark artifact includes machine-readable scenario catalog metadata.
2. The truth report includes catalog details and a trend section when a previous artifact exists.
3. Scenario rows render `PASS` or `FAIL` without relying on a precomputed `status` field.
4. Tests cover catalog and trend rendering.
