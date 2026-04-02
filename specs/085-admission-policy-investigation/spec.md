# Feature Spec: 085 Admission Policy Investigation

## Summary

The ingest-pressure gauntlet showed that repetitive writes often resolve to `ingest_rejected` or `no_op`. This phase investigates that behavior so Aegis can distinguish healthy protection from hidden throughput weakness.

## Problem

Right now the repo can measure admission pressure, but it cannot yet explain that result clearly. Without explanation, Aegis cannot confidently claim that its write-path behavior is intentional and healthy.

## Goals

- Trace the current ingest/admission decision path.
- Surface actionable rejection/no-op reasons for repeated writes.
- Keep the investigation bounded and artifact-first.

## Non-Goals

- Rewriting the admission system in this phase.
- Changing product claims before the investigation is complete.
- Opening concurrency or soak layers.

## Acceptance Criteria

1. The repo gains a small diagnostic path that explains repetitive ingest rejections or no-ops.
2. The diagnostic output is grounded in the current admission decision logic.
3. Tests cover the diagnostic behavior.
