# Aegis Python v7

Local-first memory engine for OpenClaw and MCP-based agents.

## Product Overview

Aegis is a local-first memory system for agents that need memory to stay useful, scoped, and trustworthy over time.

The current runtime now exposes the v7 architecture primitives inside the Python-owned path:

- immutable evidence-first admission
- validation and policy gate decisions
- explicit `memory_state` plus transition audit history
- specialized storage facades for fact, local vector, and graph surfaces
- governed background planning plus auditable apply loops
- retrieval orchestration over the ranked runtime view

It is designed for a simple product promise:

- remember useful things without turning every conversation into a memory dump
- recall the right thing inside the right scope
- surface ambiguity instead of pretending conflicts do not exist
- stay usable locally even when optional sync paths are degraded

## Why Aegis

Aegis is not trying to win by being the loudest or the most magical memory layer.
It is trying to be the memory system you can trust when correctness, scope discipline, and local control matter.

The core idea is:

- easy enough to start in minutes
- disciplined enough to trust in real agent workflows
- explicit enough to debug when memory behavior matters

## What Makes It Different

- scope isolation is a product feature, not an implementation detail
- conflict-aware retrieval is visible instead of silently flattened away
- explainability and citations matter more than vague “smart memory” vibes
- hygiene and lifecycle rules keep memory from becoming an unbounded pile
- local-first control remains the default, not an optional afterthought

## Non-Goals

Aegis is not trying to be:

- a managed-only cloud dependency
- a graph-first system that adds complexity just to look advanced
- a memory layer that hides conflicts and writes with no discipline
- a pitch-heavy product that claims more than the current runtime can prove

## What It Does

Aegis Python focuses on a narrow engine contract:

- store durable memory with explicit scope and provenance, plus safe defaults for ordinary callers
- read memory citations and local file fragments through Python-owned surfaces
- retrieve scoped results with explainable ranking reasons
- keep working memory bounded through lifecycle rules
- surface conflict state instead of hiding ambiguity
- create local backups and restore them through Python-owned flows
- preview and restore either full backups or a single scope safely
- expose thin local app and MCP integration surfaces

The public v1 memory lanes are:

- `working`
- `episodic`
- `semantic`
- `procedural`

## Current Engine Surface

Core Python modules live under [aegis_py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py):

- [app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py): canonical local orchestration surface
- [mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py): thin MCP-oriented adapter
- [main.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/main.py): lightweight runtime entrypoints
- [storage/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage): SQLite schema and persistence
- [retrieval/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval): scoped search, explainability, benchmark gates
- [hygiene/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene): decay and session-end maintenance
- [conflict/](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict): contradiction detection and suggestion-first handling

## Internal Architecture

Internally, Aegis now treats the historical "23 beasts" model as contributor-facing taxonomy only. The runtime is not organized as 23 public modules. The practical architecture remains a six-module model:

- `memory`
- `retrieval`
- `hygiene`
- `profiles`
- `storage`
- `integration`

The canonical internal beast map lives in [ARCHITECTURE_BEAST_MAP.md](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/ARCHITECTURE_BEAST_MAP.md). Use that document when translating lore into refactor boundaries or module ownership. Do not use beast names as public tool/API contracts.

## Installation

Requirements:

- Python 3.11+
- SQLite with FTS5

Install:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

If you want both the Python runtime and the current OpenClaw plugin/bootstrap path, use this quickstart instead:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
python3 ./bin/aegis-setup
```

`aegis-setup` now checks core runtime prerequisites (`Python`, `SQLite FTS5`) and also reports whether the current plugin/bootstrap prerequisites (`node`, `npm`) are installed.
For Debian/Ubuntu-style system Python environments that enforce PEP 668, prefer the local `.venv` flow above instead of installing into the system interpreter.

## 5-Minute First Memory

If you are new to Aegis, start here and ignore the advanced tools for now:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
python3 ./bin/aegis-setup
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/python -m aegis_py.cli remember "My favorite drink is jasmine tea."
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/python -m aegis_py.cli recall "What is my favorite drink?"
```

That path is the intended newcomer flow:

- run `aegis-setup`
- use `remember`
- use `recall`
- check `status` or `memory_stats` only if you want confirmation

You do not need backup, sync, graph, rebuild, or conflict tools to reach first value.

## Demo Path

If you want one script that shows Aegis working end-to-end, run:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python scripts/demo_first_memory.py
```

That demo proves one short local-first story:

- setup succeeds
- a memory is stored
- the same memory is recalled
- the runtime stays healthy afterward

It is the easiest script to point at when someone asks, “What does Aegis actually do right now?”

## Why You Can Trust A Recall

Aegis is meant to be grounded, not just plausible. The current trust story comes from four visible fields in the Python-owned retrieval contract:

- `provenance`: where the memory came from, such as `[manual] docs/release-checklist.md`
- `reasons`: why the result ranked, such as `fts_match`, `scope_exact_match`, or `conflict_visible`
- `trust_state` and `trust_reason`: whether the result looks strong, weak, or conflicting and why
- `context-pack` evidence: retrieval stage, scope boundary, and source metadata for host-side reasoning

If you want a runnable proof of that contract, run:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python scripts/demo_grounded_recall.py
```

That demo shows a single grounded recall path:

- a memory is stored with explicit provenance
- explain-mode search returns provenance and ranking reasons
- context-pack preserves scope and source evidence
- trust is shown explicitly instead of being implied

## Integration Quickstart

If you are integrating Aegis from a thin host, use the Python-owned local service boundary directly:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.mcp.server --service-info
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.mcp.server --startup-probe
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.mcp.server --tool memory_setup --args-json '{}'
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.mcp.server --tool memory_recall --args-json '{"query":"What do you know about me?"}'
```

The intended thin-host flow is:

- inspect `--service-info`
- gate on `--startup-probe`
- call `--tool <name> --args-json '{...}'`
- treat Python as the semantic owner

If you want one runnable proof of that contract, run:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.venv/bin/python scripts/demo_integration_boundary.py
```

## Running Locally

Run the MCP-oriented server surface:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
export PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7
python3 aegis_py/mcp/server.py --test
```

Inspect the local service descriptor and startup probe:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.mcp.server --service-info
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.mcp.server --startup-probe
```

Run the standalone Python CLI surface:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m aegis_py.cli surface
```

The engine uses `AEGIS_DB_PATH` if set. Otherwise it defaults to a local SQLite database path.

Core host-facing Python-owned tool surfaces now include:

- `memory_search`
- `memory_conflict_prompt`
- `memory_conflict_resolve`
- `memory_context_pack`
- `memory_link_store`
- `memory_link_neighbors`
- `memory_get`
- `memory_store`
- `memory_surface`
- `memory_scope_policy`
- `memory_sync_export`
- `memory_sync_preview`
- `memory_sync_import`
- `memory_stats`
- `memory_doctor`
- `memory_clean`
- `memory_profile`
- `memory_taxonomy_clean`
- `memory_rebuild`
- `memory_scan`
- `memory_visualize`
- `memory_backup_upload`
- `memory_backup_list`
- `memory_backup_preview`
- `memory_backup_download`

`memory_backup_preview` and `memory_backup_download` now also accept optional `scopeType` and `scopeId` fields. When both are supplied, Aegis previews or restores only that scope and leaves all other local scopes untouched.

## Runtime Health Contract

`memory_stats`, `memory_doctor`, and `memory_surface` publish one bounded health contract across the runtime, docs, and plugin metadata.

- Health states are `HEALTHY`, `DEGRADED_SYNC`, and `BROKEN`.
- Structured health fields are `health.state`, `health.issues`, and `health.capabilities`.
- Capability flags currently include `local_store`, `local_search`, `local_status`, `backup_restore`, and `optional_sync`.
- Degraded sync states must not block local-first reads or writes.
- Broken state is reserved for core local runtime failures such as unavailable SQLite storage.

## Default User Path

For non-technical users, the default host-facing path is intentionally narrow:

- `memory_remember`
- `memory_recall`
- `memory_correct`
- `memory_forget`
- `memory_setup`
- `memory_stats`
- `memory_profile`

The guided first-run command is `aegis-setup`, which now routes to Python-owned onboarding.

For newcomer-first value, the intended first verbs are:

- `memory_setup`
- `memory_remember`
- `memory_recall`
- `memory_stats`
- `memory_profile`

The default ordinary-user contract also carries runtime-owned defaults:

- default scope is `agent/default`
- default provenance is `conversation` with `consumer://default`
- `memory_remember`, `memory_correct`, and `memory_forget` trigger guided/background hygiene so users do not need to run operator maintenance commands for everyday use

Advanced tools such as scope policy inspection, explicit backup controls, conflict workflows, graph inspection, and rebuild/scan surfaces still exist for operators and host integrations, but they are not the default ordinary-user path.

## Public Boundary

The stable public contract is Python-owned. Outside hosts should integrate through:

- [aegis_py/app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py) for library semantics
- [aegis_py/surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py) for public contract assembly and host-ready context-pack shaping
- [aegis_py/operations.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/operations.py) for backup, restore, and scope-policy operational workflows
- [aegis_py/mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py) for tool-oriented access
- `memory_surface` for a runtime-readable summary of the supported public operations and ownership boundaries

Outside hosts should not depend directly on storage helpers or raw SQLite schema details. The TypeScript plugin shell remains an adapter over the Python-owned contract, not the owner of memory-domain behavior.

For shell and script integrations outside OpenClaw, the supported standalone entrypoint is [aegis_py/cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py). It wraps the same Python-owned public contract and emits JSON for structured commands.

## Local Service Boundary

Aegis should be treated as a local sidecar/service boundary, not as a requirement for thin hosts to own Python-side memory semantics.

- preferred transport is a local MCP/tool process
- supported thin-host fallback is a JSON-emitting CLI process
- `--service-info` publishes the stable local-service descriptor
- `--startup-probe` publishes readiness and health before tool calls
- `--tool <name> --args-json '{...}'` is the stable local process invocation pattern for thin hosts

For JS-only or other thin hosts, the intended flow is:

1. spawn the local Python process
2. read `--service-info`
3. gate on `--startup-probe`
4. call tools through the Python-owned boundary

Thin hosts should not reimplement memory-domain behavior. They should treat Python as the semantic owner and remain adapters only.

## Hybrid Boundary

Aegis remains local-first at the core. Hybrid behavior is currently policy scaffolding only:

- scopes are `local_only` by default
- scopes may be marked `sync_eligible` explicitly
- `memory_scope_policy` inspects effective policy without requiring any remote backend
- sync metadata is descriptive scaffolding, not a mandatory service dependency

The current hybrid sync protocol lite is file-based only:

- `memory_sync_export` exports one `sync_eligible` scope into a portable JSON envelope
- `memory_sync_preview` compares an incoming envelope without mutating the DB
- `memory_sync_import` imports an envelope explicitly into a local `sync_eligible` scope
- there is still no remote backend requirement; local DB remains source of truth
- sync preview now reports `incoming_new`, `incoming_existing`, `local_only`, and `revision_mismatch`
- sync import now reports inserted, replaced, and unchanged record counts for auditability
- sync envelopes now also carry a lightweight per-scope `scope_revision` stamp

## Mammoth Retrieval

Aegis now defines a lexical-first retrieval flow for host models:

- seed recall starts with local FTS5 lexical matches
- explicit memory links may expand from lexical seed memories before broader subject expansion
- subject-linked neighbors may be expanded only after lexical seed recall succeeds
- expanded results are tagged as relationship expansion rather than pretending to be direct lexical hits
- `memory_context_pack` returns a host-ready payload with strategy steps, counts, provenance, conflict visibility, and per-result retrieval stages
- `memory_conflict_prompt` lists reviewable contradiction prompts without mutating memory state
- `memory_conflict_resolve` applies an explicit resolution decision with rationale

Weaver is now active in the Python runtime through explicit same-scope memory links:

- `memory_link_store` creates or updates a typed relation between two memories
- `memory_link_neighbors` inspects one-hop explicit neighbors for a memory
- cross-scope links are rejected to preserve scope isolation
- link-driven context-pack results now expose the link type, the seed memory that caused expansion, and lightweight link metadata
- context-pack may follow one additional explicit link hop beyond first-hop expansion, but only as a bounded and labeled `multi_hop_link_expansion`
- Weaver reranking now prefers nearer hops and stronger link types such as `procedural_supports_semantic` over weaker generic links such as `same_subject`
- entity-structure-lite now extracts lightweight entity tags into memory metadata and may use shared entities as a bounded `entity_expansion` step

The current automatic Weaver rule is intentionally narrow:

- on ingest, Aegis auto-creates bounded `same_subject` links
- on ingest, Aegis also auto-creates bounded `procedural_supports_semantic` links for same-subject procedural and semantic memory pairs
- only for active memories in the same `scope_type` and `scope_id`
- only when the new memory has a non-empty subject
- rebuild backfills this same rule for older local data

For the OpenClaw-hosted plugin path, the repository still ships a tiny JS bootstrap at `dist/index.js` because the current host contract loads extensions from JavaScript. That bootstrap now delegates runtime behavior to `aegis_py` and should not own memory-domain semantics.

## Validation Workflow

Run the current Python regression suite:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests
```

The repository also exposes Python-first npm helpers for contributors who still enter through the Node package metadata:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
npm run test:python
npm run test:bootstrap
```

Retrieval benchmark gating is defined in [benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py) and exercised by [test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py). The current gate checks:

- `Recall@1`
- `Recall@5`
- `MRR@10`
- `nDCG@10`
- scope leakage
- conflict leakage
- conflict visibility for expected conflict-bearing fixtures
- explanation completeness
- latency p95

The seeded benchmark corpus now includes:

- scoped retrieval and anti-leak cases
- punctuation-safe query handling
- empty-result behavior
- conflict-visible retrieval cases

Gate failures render explicit metric/value pairs instead of only generic pass/fail output.

## Benchmark Snapshot

The current benchmark story is simple:

- Aegis should retrieve the right memory without leaking across scopes.
- Aegis should keep conflict visibility instead of flattening contradictory memories away.
- Aegis should stay fast enough to feel local-first in practice.

The current gates and scripts support that story in different ways:

- [aegis_py/retrieval/benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py) defines the repo-native retrieval gates such as `Recall@1`, `Recall@5`, `MRR@10`, `nDCG@10`, scope leakage, conflict leakage, explanation completeness, and latency p95.
- [scripts/benchmark_dragonfly.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/benchmark_dragonfly.ts) demonstrates hard lexical recovery cases such as synonym rescue and typo-heavy recall.
- [scripts/benchmark_weaver.ts](/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/benchmark_weaver.ts) demonstrates that procedural recall can win when the user asks for a how-to flow, without blindly overriding factual recall when the user asks for concepts.

In product terms, the benchmark target is:

- grounded retrieval
- visible trust and conflict handling
- no scope leakage
- local-first responsiveness

## CI Validation

The repository-local CI source of truth for the Python engine is:

- [.github/workflows/aegis-python-validation.yml](/home/hali/.openclaw/extensions/memory-aegis-v7/.github/workflows/aegis-python-validation.yml)

It runs the same canonical command used locally:

```bash
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 python -m pytest -q tests
```

This workflow is useful even before the repo is connected to GitHub because it keeps the CI contract explicit and reviewable in the repo itself.

## Release Packaging

The current local release bundle helper is:

- [scripts/release-python-package.sh](/home/hali/.openclaw/extensions/memory-aegis-v7/scripts/release-python-package.sh)

Default usage:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
./scripts/release-python-package.sh
```

This creates a tarball under `dist/python-release/` containing:

- `aegis_py/`
- `bin/aegis-setup`
- `README.md`
- `requirements.txt`
- `scripts/demo_first_memory.py`
- `scripts/demo_integration_boundary.py`
- `scripts/demo_grounded_recall.py`
- `openclaw.plugin.json`
- `RELEASE_NOTES.txt`
- `QUICKSTART.txt`

The release bundle is now meant to be unpack-and-try friendly:

- run `bin/aegis-setup`
- run `scripts/demo_first_memory.py`
- run `scripts/demo_integration_boundary.py`
- run `scripts/demo_grounded_recall.py`
- use `README.md` and `QUICKSTART.txt` for the first-value path and validation commands

The shipped npm package now includes the same Python runtime artifacts and excludes the legacy `src/` TypeScript engine sources from the published file list.

Run the Python validation workflow before creating a release bundle.

## Spec-Kit Workflow

This repo carries the `spec-kit` project structure at [.specify](/home/hali/.openclaw/extensions/memory-aegis-v7/.specify) and active feature artifacts under [specs/](/home/hali/.openclaw/extensions/memory-aegis-v7/specs).

Current execution-relevant features include:
- [specs/006-snapshot-versioning-and-scope-restore](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore)

Recently closed user-facing roadmap slices:
- [specs/038-simple-user-surface](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/038-simple-user-surface)
- [specs/039-memory-trust-shaping](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/039-memory-trust-shaping)

Recently closed runtime-migration slices:
- [specs/004-ts-python-adapter](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter)
- [specs/005-python-only-engine](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine)

Not yet opened in Spec Kit:
- `040-long-term-consolidation`

## Workflow Governance

This repository uses **GSD + Spec Kit** together.

- **Spec Kit** is the feature source of truth
- **GSD** is the orchestration and execution layer
- [.planning/](/home/hali/.openclaw/extensions/memory-aegis-v7/.planning) is coordination only and must not override active feature artifacts
- when `.planning/` and [specs/](/home/hali/.openclaw/extensions/memory-aegis-v7/specs) disagree, `specs/` wins
- check the active feature in `specs/*` before using `/gsd:*` to plan or execute material changes

The repository-level workflow contract is:

- `specs/*` for active feature truth
- `.specify/memory/constitution.md` for governance baseline
- `.planning/*` for orchestration only

Useful check:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

## Status

As of 2026-03-24, the current repo state is stable rather than half-open:

- `038-simple-user-surface` is implemented
- `039-memory-trust-shaping` is implemented
- `004-ts-python-adapter` is implemented
- `005-python-only-engine` is implemented
- the canonical Python regression suite passes with `114 passed`
- the bootstrap validation suite passes with `17 passed`
- `040-long-term-consolidation` has not been opened yet

For the current wave, the repo can now be treated as closed and stable. What remains are optional next-wave features such as [specs/006-snapshot-versioning-and-scope-restore](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/006-snapshot-versioning-and-scope-restore) or `040-long-term-consolidation`, not unresolved migration drift inside the active runtime path.

For direct real-world testing without reopening planning overhead, use the criteria recorded in [specs/046-consumer-ready-checklist/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/046-consumer-ready-checklist/plan.md) and [specs/050-consumer-closure-review/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/050-consumer-closure-review/plan.md).

## Migration Stance

The current migration direction is:

- keep the TypeScript OpenClaw plugin shell as the adapter surface
- treat the Python engine as the canonical local memory backend
- migrate tool routing incrementally, starting with retrieval-oriented behavior

Current state:

- core tool behavior is Python-owned
- the remaining JS/TS path is a host bootstrap only
- `memory_get` and backup/restore now run through Python-owned surfaces
- backup manifests, backup listing, and dry-run restore preview now run through Python-owned surfaces
- selective scope preview and selective scope restore now also run through Python-owned surfaces
- diagnostics, taxonomy cleanup, scan, rebuild, and visualization now also run through Python-owned surfaces
- the main remaining non-Python concern is the host-mandated JS bootstrap path

The migration evidence record for that completed work lives at [specs/004-ts-python-adapter](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/004-ts-python-adapter) and [specs/005-python-only-engine](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/005-python-only-engine).
