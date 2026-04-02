# Feature Spec: 084 Ingest Pressure Gauntlet

## Summary

The operations-pressure gauntlet surfaced repeated `ingest_rejected` and `no_op` signals during rebuild-pressure setup. This phase turns that signal into an explicit evaluation slice.

## Problem

Aegis currently looks strong under retrieval and recovery pressure, but write-path behavior under repetitive ingest pressure is still under-explained. Without a focused ingest gauntlet, it is hard to know whether no-op decisions are healthy protection or hidden throughput weakness.

## Goals

- Add explicit ingest-pressure scenarios to the gauntlet.
- Record admission/no-op patterns in the gauntlet artifact.
- Distinguish acceptable dedup/admission behavior from suspicious write-path collapse.

## Non-Goals

- Rewriting ingest logic in this phase.
- Load-testing with concurrent multi-process writers.
- Long soak ingestion.

## Acceptance Criteria

1. The gauntlet includes at least one repetitive ingest-pressure scenario.
2. The artifact records accepted vs rejected/no-op behavior for that scenario.
3. The scenario has a bounded pass/fail bar instead of only raw logs.
