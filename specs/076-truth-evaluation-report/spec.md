# Feature Spec: 076 Truth Evaluation Report

## Summary

Aegis now has a governed truth spotlight gate, but the release signal is still mostly terminal-first. This phase adds a readable evaluation report so current-truth strength can be reviewed, shared, and compared more easily.

## Problem

The benchmark artifact and gate are machine-friendly, but release evidence is still harder to inspect than it should be. A stronger final-form Aegis needs a thin reporting layer that turns truth metrics and scenario outcomes into a compact human-readable artifact.

## Goals

- Generate a Markdown report from the truth spotlight benchmark artifact.
- Include summary metrics and per-scenario outcomes in one release-friendly document.
- Keep the report aligned with the existing benchmark and gate instead of inventing a second evaluation path.

## Non-Goals

- Expanding into a dashboard service.
- Replacing JSON artifacts as the canonical machine-readable source.
- Reworking the spotlight benchmark itself.

## User-Facing Outcome

Developers can produce one report artifact that shows whether Aegis still wins on current-truth behavior and which scenarios passed or failed.

## Acceptance Criteria

1. A script generates a Markdown report from the truth spotlight artifact.
2. The report includes summary metrics and per-scenario selected vs expected outcomes.
3. The report is documented in the repo validation story.
4. At least one automated test covers the report rendering path.
