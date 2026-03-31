# Implementation Plan: Ingest Precision Roadmap

**Branch**: `024-ingest-precision-roadmap` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/024-ingest-precision-roadmap/spec.md)
**Input**: Feature specification from `/specs/024-ingest-precision-roadmap/spec.md`

## Summary

Turn Tranche A into an executable sequence for Extractor, Normalizer, Classifier, and Scorer so ingest precision can improve in bounded steps without an ingest rewrite.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `023-beast-depth-tranches`, canonical beast map, current `memory` write path  
**Storage**: repo-tracked markdown and the existing `memory` module boundaries  
**Testing**: prerequisite check plus documentation review  
**Constraints**: keep scope planning-only, stay within the six-module model, and avoid opening more than one thin ingest slice at a time  

## Constitution Check

- `Local-First Memory Engine`: Pass.
- `Brownfield Refactor Over Rewrite`: Pass.
- `Explainable Retrieval Is Non-Negotiable`: Pass.
- `Safe Memory Mutation By Default`: Pass.
- `Measured Simplicity`: Pass.

## Design Direction

- deepen ingest quality before adding new retrieval or hygiene complexity
- treat `Extractor` and `Normalizer` as earlier leverage than `Classifier` and `Scorer`
- keep each ingest beast tied to a narrow deliverable and an explicit opening gate
- preserve the `memory` module as the default home for Tranche A work

## Work Plan

1. reconcile `.planning/STATE.md` to feature `024-ingest-precision-roadmap`
2. extend the canonical beast map with Tranche A sub-order, deliverables, and gates
3. record the implementation roadmap in `tasks.md` for later execution features
4. validate feature resolution through the canonical prerequisite workflow

## Validation Plan

- run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`

## Validation Evidence

Observed on 2026-03-24 after creating 024-ingest-precision-roadmap:

- `.planning/STATE.md` now anchors the coordination layer to `024-ingest-precision-roadmap`
- the canonical beast architecture document now records a concrete Tranche A sub-order for `Extractor`, `Normalizer`, `Classifier`, and `Scorer`
- each Tranche A beast now has bounded deliverables and explicit opening gates so later implementation features can stay narrow

Validation results:

- `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/024-ingest-precision-roadmap`
  - `AVAILABLE_DOCS=["tasks.md"]`
