# Implementation Plan: Hybrid Sync Protocol Lite

**Branch**: `018-hybrid-sync-protocol-lite` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/018-hybrid-sync-protocol-lite/spec.md)
**Input**: Feature specification from `/specs/018-hybrid-sync-protocol-lite/spec.md`

## Summary

Add a file-based sync envelope workflow for `sync_eligible` scopes with export, preview, and import flows, while keeping the local DB as source of truth.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: current scope policy and operational flows  
**Storage**: local SQLite plus file-based JSON envelopes  
**Testing**: `pytest`, `vitest`, canonical repo validation  
**Constraints**: no remote backend, sync-eligible scopes only, preview before import, local-first core remains authoritative  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
- run `npm run lint`
- run `npm run test:bootstrap`
- run `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`

## Validation Evidence

Observed on 2026-03-24:

- sync-eligible scopes can now export a file-based sync envelope
- incoming envelopes can be previewed and imported through Python-owned flows
- docs now describe the hybrid sync protocol lite workflow

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed: resolved to `specs/018-hybrid-sync-protocol-lite`
- `npm run lint`
  - passed
- `npm run test:bootstrap`
  - passed: `17` tests
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed: `83 passed in 2.88s`
