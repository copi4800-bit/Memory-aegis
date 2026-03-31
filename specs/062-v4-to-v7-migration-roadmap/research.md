# V4 To V7 Gap Analysis

This document converts the architecture proposal in [/home/hali/.openclaw/11.md](/home/hali/.openclaw/11.md) into migration terms against the current Aegis v4 codebase.

## Invariants

These remain mandatory through every tranche:

- local-first control
- scope isolation
- explainability
- provenance preservation
- conflict-aware retrieval
- hygiene and lifecycle discipline
- rollback/audit friendliness

## Anti-Goals

The v7 effort must not become:

- a full rewrite of the stable v4 runtime
- a cloud-first or managed-only pivot
- a graph-first complexity spike without evidence
- a speculative storage split before admission/state discipline exists
- a product regression on the current OpenClaw integration path

## V7 Block Mapping

### 1. Input Capture Layer

Status: `partial`

Existing v4 footing:

- [app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)
- [memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py)
- [storage/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py)

Current reality:

- v4 already captures scope, source metadata, content, and timestamps.
- consumer flows already apply stable default provenance.

Gap:

- capture is still oriented around producing a memory record early, not around preserving raw evidence as a first-class immutable object.

### 2. Immutable Evidence Log

Status: `missing`

Existing v4 footing:

- memory metadata and provenance fields in [storage/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py)

Current reality:

- v4 stores processed memory records.
- v4 does not maintain an append-only event/evidence store separate from memory state.

Gap:

- no raw evidence event table
- no immutable evidence span binding
- no “memory points back to evidence” backbone

### 3. Extraction Layer

Status: `present`

Existing v4 footing:

- [memory/extractor.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/extractor.py)
- [memory/normalizer.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/normalizer.py)
- [memory/classifier.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/classifier.py)

Current reality:

- extraction, normalization, and classification already exist.
- derived fields such as subject and summary are already hardened in v4.

Gap:

- extraction outputs do not yet live as draft candidates gated separately from durable usable memory.

### 4. Validation And Policy Gate

Status: `partial`

Existing v4 footing:

- [conflict/core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py)
- [governance/policy.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/policy.py)
- [governance/automation.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/automation.py)

Current reality:

- v4 has policy and confidence gates for some autonomous actions.
- v4 has conflict detection and suggestion-first handling.

Gap:

- there is no single admission gate that every extracted candidate must cross before becoming retrievable memory.
- policy is stronger for post-ingest automation than for pre-promotion validation.

### 5. Memory State Machine

Status: `partial`

Existing v4 footing:

- [storage/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py)
- [hygiene/transitions.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/transitions.py)
- tests around lifecycle status and archival flows

Current reality:

- v4 already tracks lifecycle-ish statuses such as `active`, `archived`, `expired`, `conflict_candidate`, and `superseded`.

Gap:

- v4 does not yet model semantic promotion states such as `draft`, `validated`, `hypothesized`, `invalidated`, and `consolidated`.
- state transitions are more lifecycle-oriented than admission-oriented.

### 6. Specialized Storage

Status: `partial`

Existing v4 footing:

- fact records in SQLite memories via [storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- link graph structures and graph analysis in [graph_analysis.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/graph_analysis.py)
- retrieval/reranking infrastructure in [retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)

Current reality:

- v4 already behaves like a fact store plus link graph inside one local SQLite-first runtime.

Gap:

- v4 does not yet separate fact, vector, and graph stores as first-class architectural layers.
- this is not the first migration priority because admission/state discipline is missing upstream.

### 7. Governed Background Intelligence

Status: `partial`

Existing v4 footing:

- [hygiene/engine.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py)
- [hygiene/consolidator.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/consolidator.py)
- [evolve/core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/evolve/core.py)
- governance modules under [governance/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance)

Current reality:

- v4 already has background maintenance, consolidation, decay, and some governed automation.

Gap:

- not all background intelligence is explicitly modeled as operating on working copies or draft outputs first.
- audit/rollback exists, but is not yet the universal mutation path for every background action.

### 8. Retrieval Orchestrator

Status: `present`

Existing v4 footing:

- [retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)
- [retrieval/contract.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/contract.py)
- [retrieval/models.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py)
- [app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)

Current reality:

- explainable retrieval, provenance, ranking reasons, conflict visibility, and context-pack shaping are strong in v4.

Gap:

- retrieval currently operates over the v4 lifecycle model rather than the richer v7 admission/state model.

### 9. Governance Shell

Status: `partial`

Existing v4 footing:

- [governance/automation.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/automation.py)
- [governance/policy.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/policy.py)
- [governance/rollback.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/governance/rollback.py)
- [observability/metrics.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/observability/metrics.py)

Current reality:

- audit, policy, rollback, and observability primitives already exist.

Gap:

- they are not yet the outer coordination shell around all ingest/promotion/background mutation paths.
- shadow testing and explicit blast-radius control are still mostly conceptual.

## Migration Tranches

### Tranche 1: Evidence Log Foundation

Goal:

- introduce immutable raw evidence as a first-class local store

Scope:

- append-only `evidence_events`
- memory records hold evidence pointers/spans
- no retrieval behavior rewrite yet

Why first:

- this is the largest architectural gap and the foundation for trustworthy validation later

### Tranche 2: Promotion Gate And Admission Control

Goal:

- separate extraction from promotion into usable memory

Scope:

- draft candidate representation
- validator/policy gate before promotion
- confidence and contradiction checks at admission time

Why second:

- it prevents “extract then immediately trust” behavior without destabilizing retrieval yet

### Tranche 3: Formal Memory State Machine

Goal:

- move from coarse lifecycle statuses to a richer admission-aware state model

Scope:

- add `draft`, `validated`, `hypothesized`, `invalidated`, `consolidated`
- map existing lifecycle statuses compatibly
- preserve current retrieval API while tightening internals

Why third:

- once evidence and promotion exist, richer state can be introduced safely

### Tranche 4: Governed Background Intelligence Hardening

Goal:

- require governed audit/rollback paths for background mutations

Scope:

- working-copy or candidate-first background operations
- stronger audit trail coverage
- rollback guarantees for governed actions

Why fourth:

- this becomes meaningful only after admission/state semantics are explicit

### Tranche 5: Specialized Storage And Retrieval Internals

Goal:

- split or formalize fact/vector/graph internals only after upstream discipline exists

Scope:

- internal storage specialization where it produces clear value
- retrieval orchestrator updated to exploit the richer state and evidence model

Why last:

- doing this earlier would maximize complexity before trust discipline is in place

## First Implementation-Ready Tranche

The first tranche that should actually be opened next is:

- `063-evidence-log-foundation`

Reason:

- it addresses the most important missing architectural primitive from `11.md`
- it strengthens auditability and rollback potential immediately
- it does not require destabilizing the currently healthy retrieval/runtime surface in one move
