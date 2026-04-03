# Phase 130: Truth Transition Timeline UX

## Goal
Make TruthKeep show how current truth changed over time so users can see which fact won, which fact was superseded, and why the state changed.

## Scope
- Add a truth transition timeline surface backed by governance events and memory state transitions.
- Expose the timeline through app, MCP, registry, and OpenClaw-facing metadata.
- Surface timeline previews inside workflow shell and dashboard shell.
- Add text/HTML reports, demo scripts, and regression tests.

## Non-Goals
- No changes to retrieval, truth math, or governance policy.
- No new storage schema.
- No OpenClaw native packaging overhaul.
