# Aegis Python Constitution

## Core Principles

### I. Local-First Memory Engine
Aegis Python is a local-first memory engine for OpenClaw and MCP-based agents. The default runtime path must work with local SQLite and FTS5 without requiring cloud services, hosted vector stores, or mandatory external APIs. Optional semantic or embedding enhancements may exist, but the baseline product must remain useful, testable, and operable offline.

### II. Brownfield Refactor Over Rewrite
This codebase is already functional and must be evolved by refactor, hardening, and productization rather than wholesale rewrite. Public behavior exposed through the current Python surfaces in `app.py`, `main.py`, MCP integration, and storage-backed memory workflows must be preserved unless a spec explicitly approves a breaking semantic change and documents migration impact.

### III. Explainable Retrieval Is Non-Negotiable
Retrieval is a first-class product capability, not a black box. Every retrieval path must be able to explain which memories were returned, from which scope and source, what scoring signals contributed, and whether conflict or lifecycle state affected ranking. New search or reranking logic in modules such as `memory/core.py` and `retrieval/search.py` must improve explanation fidelity, not reduce it.

### IV. Safe Memory Mutation By Default
Aegis must never perform destructive or ambiguous memory mutation silently. Conflict handling, hygiene, consolidation, reinforcement, decay, archival, and supersession must prefer suggest-first, log-first, and provenance-preserving flows. If a memory change cannot be justified and traced, it does not belong in the default automation path.

### V. Measured Simplicity
Architectural simplicity outranks speculative cleverness. Aegis is a memory engine, not a general orchestration platform. New features must justify themselves through correctness, maintainability, and measurable value. If a capability increases cognitive load, schema complexity, or retrieval uncertainty without clear benchmark improvement, it should not be merged into the core system.

## Product Scope And Architecture Guardrails

### Product Scope
The v1 public memory model is limited to four memory types:

- `working`
- `episodic`
- `semantic`
- `procedural`

Nuance such as social, temporal, contextual, or preference state should remain metadata, facets, or profile signals unless a later spec proves that promoting them to first-class types improves retrieval and lifecycle outcomes.

### Architectural Boundaries
The codebase must continue moving toward explicit boundaries already visible in the current layout:

- `storage/` owns SQLite persistence, schema, indexes, CRUD, and serialization.
- `retrieval/` owns query planning, candidate collection, score fusion, ranking, and explanation payloads.
- `hygiene/` owns lifecycle, decay, archival, and maintenance policies.
- `preferences/` owns user or agent preference extraction and profile state.
- `mcp/`, `app.py`, and `main.py` are integration surfaces and should not accumulate heavy domain logic.

Business semantics must not be buried inside low-level persistence helpers. If a module grows into a god-object or starts mixing storage, retrieval, and hygiene decisions in one place, it must be split before adding further capability.

### Data Model Guardrails
The storage model must preserve explicit scope, provenance, lifecycle state, and explainability. Memory records must retain identifiers, scope fields, source metadata, status, timestamps, and structured metadata sufficient for audits and re-ranking. Schema changes must remain migration-friendly and future-safe for provenance, conflict tracking, and lifecycle evolution.

## Quality Gates And Delivery Workflow

### Benchmark Gate For Retrieval Changes
Any change that affects retrieval quality, ranking, scope filtering, conflict filtering, or score fusion must be evaluated against a benchmark set. At minimum, relevant work should measure:

- Recall@1 and Recall@5
- MRR@10
- nDCG@10
- scope leakage rate
- conflict leakage rate
- latency p50 and p95
- explain completeness rate

Retrieval changes that cannot be measured should be treated as incomplete.

### Test Expectations
Every material change must add or update tests at the right level. This codebase already has meaningful module boundaries across memory, retrieval, hygiene, storage, preferences, and integration; changes must preserve or improve that test discipline. Schema, lifecycle, retrieval, and MCP-facing behavior require integration-oriented coverage, not just isolated unit assertions.

### GSD + Spec Kit Delivery
Feature work should follow the combined GSD + Spec Kit flow in this project:

1. Establish or refine constitutional rules when the product contract changes.
2. Write or update the feature specification.
3. Clarify ambiguous requirements before planning.
4. Produce an implementation plan that respects existing module boundaries.
5. Break work into tasks that preserve behavior first, then tighten semantics.
6. Use GSD artifacts under `.planning/` only for orchestration, sequencing, and codebase mapping against the active feature artifacts.
7. Implement with tests, benchmarks, and explanation output in mind.

## Governance

This constitution overrides ad hoc preferences, README prose, and convenience shortcuts when they conflict.

- Aegis Python must remain local-first and audit-friendly.
- Breaking changes require explicit specification, migration notes, and clear user-facing rationale.
- Retrieval, conflict, hygiene, and schema work must be judged on measured correctness and explainability, not intuition alone.
- Complexity must be paid for with better boundaries, better tests, or better benchmark results.
- When roadmap material, `.planning/`, specs, and current code disagree, the active spec and this constitution govern the next change set.

**Version**: 1.0.0 | **Ratified**: 2026-03-23 | **Last Amended**: 2026-03-23
