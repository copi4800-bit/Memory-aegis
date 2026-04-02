# Feature Spec: 080 Truth Release Evidence Bundle

## Summary

Aegis already produces truth benchmark JSON, a gate result, and a Markdown report. This phase bundles those outputs into one release-evidence package for easier review, archival, and CI consumption.

## Problem

Truth evaluation artifacts are now strong but scattered. A release reviewer still has to gather several files mentally instead of opening one bundle that summarizes the current run.

## Goals

- Produce one machine-readable bundle manifest for the current truth evaluation run.
- Reference the benchmark summary, report, and gate outcome in one place.
- Keep the bundle derivative and lightweight.

## Non-Goals

- Replacing the underlying benchmark, gate, or report files.
- Adding a database or dashboard.
- Broadening the release gate scope beyond truth evaluation.

## Acceptance Criteria

1. A script writes a truth release-evidence bundle manifest.
2. The bundle includes pointers to current summary, report, and gate status.
3. The bundle is documented in the repo's truth evaluation flow.
4. Automated tests cover bundle generation.
