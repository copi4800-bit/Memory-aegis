# Research: Hybrid Memory Core

**Date**: 2026-03-24  
**Feature**: [007-hybrid-memory-core](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/spec.md)

## Input Reviewed

- [1.md](/home/hali/.openclaw/1.md): architectural synthesis of Aegis v4 "23 beasts" grouped into foundations, capture, retrieval, hygiene, structure, and identity systems
- [aegis_py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py): current Python runtime structure
- [Aegis Python Constitution](/home/hali/.openclaw/extensions/memory-aegis-v7/.specify/memory/constitution.md)

## Key Findings

### 1. The 23-beast model is useful as an internal architecture map, not as a literal module plan

The source note in [1.md](/home/hali/.openclaw/1.md) is strongest where it collapses lore into practical ownership boundaries. It should not be implemented as 23 first-class runtime modules. Doing so would violate the constitution's `Measured Simplicity` rule and over-fragment the codebase.

Decision:

- treat the "beasts" as internal design taxonomy only
- keep public surfaces plain and operational
- keep module count close to the existing Python runtime boundaries

### 2. The six-module consolidation in `1.md` is compatible with the current Python structure

The most useful section of [1.md](/home/hali/.openclaw/1.md) is its consolidation into:

- `memory/`
- `retrieval/`
- `hygiene/`
- `profiles/`
- `storage/`
- `integration/`

This maps cleanly to the current repo with one adjustment:

- current [preferences/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/preferences) is already serving most of the proposed `profiles/` role and should evolve rather than be renamed immediately

Decision:

- adopt the six-module model as the architectural target
- continue evolving current directories rather than renaming them aggressively

### 3. Retrieval guidance from `1.md` is directionally correct if constrained

`1.md` recommends separate retrieval roles for lexical recall, semantic recall, navigation, reranking, explanation, and scope. That aligns with the constitution if interpreted narrowly:

- lexical recall stays baseline and local-first
- semantic recall remains optional
- graph/navigation must stay selective and explainable
- reranking and explanation remain core differentiators

Decision:

- keep `Scout`, `Reranker`, `Explainer`, and `Scope` as real design concepts
- keep `Oracle` optional and non-mandatory
- implement `Navigator` only through bounded, explainable expansion flows such as the new Mammoth context-pack strategy

### 4. Hygiene and lifecycle recommendations are strongly compatible with Aegis

The note's emphasis on:

- conflict detection
- taxonomy cleanup
- rebuild of derived links
- decay/retention
- consolidation
- storage hygiene

matches the existing Aegis direction and the constitution's `Safe Memory Mutation By Default` rule.

Decision:

- keep these concerns inside `hygiene/` and `storage/`
- avoid turning them into public lore-heavy primitives
- maintain suggest-first and audit-friendly semantics

### 5. The note reinforces that host integrations should remain thin adapters

The note's final grouping places API, CLI, MCP, and host runners into an integration layer. That directly supports the feature goal of making Aegis a host-agnostic memory engine rather than an OpenClaw-owned plugin.

Decision:

- preserve Python-owned semantics in [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) and [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)
- keep [src/python-adapter.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/src/python-adapter.ts) and [index.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/index.ts) as adapters only

## Applied Recommendations For Feature 007

The research from [1.md](/home/hali/.openclaw/1.md) directly supports the choices already made in this feature:

- `US1`: public surface ownership is Python-first and adapter-thin
- `US2`: hybrid stays policy-first rather than cloud-first
- `US3`: retrieval evolution is lexical-first with selective relationship expansion and explicit explanation tags

## Rejected Or Deferred Ideas

- Do not create 23 separate Python modules based on beast names
- Do not make vector or semantic retrieval mandatory for baseline recall
- Do not graph-encode every memory path before benchmark evidence justifies the complexity
- Do not expose beast taxonomy in the public user-facing surface

## Resulting Guidance

For future Aegis work, [1.md](/home/hali/.openclaw/1.md) should be treated as:

- an internal architecture interpretation aid
- a refactor map for module ownership
- a naming guide for internal design language

It should not be treated as:

- a replacement for the active feature spec
- a reason to bypass constitution checks
- a mandate to expand the runtime into a highly fragmented cognitive framework
