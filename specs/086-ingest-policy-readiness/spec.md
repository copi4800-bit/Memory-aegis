# Feature Spec: 086 Ingest Policy Readiness

## Summary

Turn the admission-policy investigation into a clear stop/go verdict for the current local-first deployment class.

## Problem

Phase `085` explains why repetitive ingest pressure produces `no_op` and rejection behavior, but it does not yet answer when the branch can be closed with confidence.

## Goals

- Add one bounded readiness bar for the current ingest policy.
- Prove low-confidence repetitive pressure is blocked for clear reasons.
- Prove high-confidence distinct writes still admit cleanly.

## Non-Goals

- Rewriting admission thresholds in this phase.
- Opening concurrency, soak, or distributed-ingest concerns.
- Claiming a broader deployment class than the current local-first scope.

## Acceptance Criteria

1. The repo gains a readiness check for the current ingest-policy behavior.
2. The readiness check uses both a protective case and a healthy-admission case.
3. Tests cover the readiness logic.
