# Research: Beast Architecture Mapping

**Date**: 2026-03-24  
**Feature**: [010-beast-architecture-mapping](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/010-beast-architecture-mapping/spec.md)

## Input Reviewed

- [1.md](/home/hali/.openclaw/1.md): the 23-beast architecture synthesis and six-module consolidation
- [specs/007-hybrid-memory-core/research.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/007-hybrid-memory-core/research.md): prior feature-level interpretation of the beast model
- [aegis_py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py): current Python package structure
- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md): current contributor-facing architecture summary

## Key Findings

### 1. The main gap is no repo-canonical beast map

Feature `007` already established that the beast model should remain an internal taxonomy. What is still missing is a single contributor-facing document in the repo that translates all 23 beasts into current Python ownership boundaries.

Decision:

- add one canonical internal map under `aegis_py/`
- keep it internal-facing and contributor-oriented

### 2. The six-module consolidation remains the correct architecture target

The strongest section of [1.md](/home/hali/.openclaw/1.md) remains the six-module consolidation:

- `memory`
- `retrieval`
- `hygiene`
- `profiles`
- `storage`
- `integration`

The current repo is close to this already, with `preferences/` serving most of the target `profiles/` role and root-level surfaces such as `app.py`, `cli.py`, and `mcp/server.py` serving the integration boundary.

Decision:

- keep the six-module model as the canonical interpretation
- document current directory mismatches rather than forcing a rename now

### 3. A beast map should distinguish current ownership from target ownership

Some beasts map cleanly to code today:

- `Scout` -> `retrieval/search.py`
- `Explainer` -> retrieval contract/result shaping
- `Archivist` -> backup and restore flows
- `Meerkat` -> conflict detection

Other beasts are only partial or target-state concerns:

- `Oracle` remains optional
- `Navigator` exists only as bounded subject expansion
- `Weaver` is still mostly target-state because dedicated relation storage is not yet first-class

Decision:

- every beast entry should carry an ownership status
- use `current`, `partial`, `target`, or `deferred`

### 4. Beast names should not leak into the public contract

The repo now has stable public surfaces such as `memory_surface`, `memory_context_pack`, `memory_scope_policy`, and the Python CLI. These should stay operational and plain. Beast naming belongs in internal docs, not in user-facing APIs or tool names.

Decision:

- document beast names as internal architecture vocabulary only
- keep public contract naming unchanged

## Resulting Guidance

This feature should produce:

- one canonical beast map for contributors
- one README update that explains how to use that map
- one planning-state update so the work is tracked through GSD + Spec Kit

This feature should not produce:

- new public tool names based on beasts
- a 23-module runtime split
- runtime behavior changes without a later feature spec
