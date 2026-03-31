# Aegis Beast Architecture Map

Internal architecture guide for translating the "23 beasts" into the practical Python engine structure.

## Usage Rule

- Beast names are internal contributor vocabulary.
- Beast names are not part of the public runtime or tool contract.
- The runtime stays organized around the six-module model:
  - `memory`
  - `retrieval`
  - `hygiene`
  - `profiles`
  - `storage`
  - `integration`

## Six-Module Model

### `memory`

Owns ingest, extraction, normalization, classification, and write-time scoring.

Current anchors:

- [memory/ingest.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/ingest.py)
- [memory/core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)
- [memory/filter.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/filter.py)

### `retrieval`

Owns lexical recall, optional semantic recall, bounded relation expansion, reranking, explainability, and scope-aware retrieval.

Current anchors:

- [retrieval/search.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)
- [retrieval/engine.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/engine.py)
- [retrieval/contract.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/contract.py)

### `hygiene`

Owns conflict detection, taxonomy cleanup, rebuild flows, lifecycle/decay, consolidation, and storage hygiene.

Current anchors:

- [hygiene/engine.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/engine.py)
- [hygiene/transitions.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/hygiene/transitions.py)
- [conflict/core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/conflict/core.py)

### `profiles`

Owns constitution-like invariants, long-lived preferences, identity, and style/profile memory.

Current anchors:

- [preferences/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/preferences/manager.py)
- [preferences/extractor.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/preferences/extractor.py)

Note: the repo still uses `preferences/` as the current directory name for most profile behavior.

### `storage`

Owns schema, repositories, backup/archive, indexes, and future durable relation storage.

Current anchors:

- [storage/schema.sql](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql)
- [storage/manager.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py)
- [operations.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/operations.py)

### `integration`

Owns external entrypoints and adapters while preserving Python-owned semantics.

Current anchors:

- [app.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/app.py)
- [surface.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/surface.py)
- [cli.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cli.py)
- [mcp/server.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/mcp/server.py)

## Beast Mapping

| # | Beast | Module | Ownership Status | Current / Target Notes |
|---|---|---|---|---|
| 1 | Constitution Beast | `profiles` | `partial` | Enforced mostly through repo constitution and runtime discipline; no dedicated Python module yet. |
| 2 | Identity Beast | `profiles` | `current` | Long-lived preference and style behavior lives primarily in `preferences/`. |
| 3 | Guardian Beast | `integration` + `retrieval` | `partial` | Boundary protection exists through scope-aware retrieval and Python-owned surfaces, but not as one dedicated module. |
| 4 | Scribe Beast | `memory` | `current` | Raw ingest and write-path capture live in `memory/ingest.py` and `memory/core.py`. |
| 5 | Extractor Beast | `memory` | `partial` | Extraction exists, but can be made more explicit as structured memory extraction evolves. |
| 6 | Normalizer Beast | `memory` | `active` | Semantic normalization and intent-based canonicalization are now active. |
| 7 | Classifier Beast | `memory` | `partial` | Lane assignment exists conceptually; stronger explicit classification is still target-state. |
| 8 | Scorer Beast | `memory` | `partial` | Write-time salience/confidence scoring is still relatively light and not yet isolated. |
| 9 | Scout Beast | `retrieval` | `current` | Lexical-first recall is live through FTS-backed search. |
| 10 | Oracle Beast | `retrieval` | `active` | Optional semantic recall via query expansion; implemented in `035-semantic-recall-core`. |
| 11 | Navigator Beast | `retrieval` | `partial` | Bounded relationship expansion exists via Mammoth context-pack subject expansion, not a full graph engine. |
| 12 | Reranker Beast | `retrieval` | `current` | Result shaping and retrieval ordering are active differentiators in the Python-owned retrieval path. |
| 13 | Explainer Beast | `retrieval` | `current` | Explainable retrieval payloads, provenance, conflict visibility, and retrieval-stage tags are live. |
| 14 | Scope Beast | `retrieval` | `current` | Scope-aware search and anti-leak behavior are part of the core engine contract. |
| 15 | Meerkat | `hygiene` | `current` | Conflict detection and contradiction-oriented flows exist today. |
| 16 | Axolotl | `hygiene` | `partial` | Rebuild flows exist, but durable derived-link regeneration is still only partial. |
| 17 | Bowerbird | `hygiene` | `current` | Taxonomy cleanup and relabel-oriented maintenance are present. |
| 18 | Decay Beast | `hygiene` | `partial` | Lifecycle and bounded-memory behavior exist, but richer retention policy remains incremental work. |
| 19 | Consolidator Beast | `hygiene` | `active` | Semantic consolidation logic is operational in the hygiene pass. |
| 20 | Nutcracker | `hygiene` + `storage` | `partial` | Storage hygiene and maintenance exist in practical form, but not yet as a broad fragmentation subsystem. |
| 21 | Weaver Beast | `storage` + `retrieval` | `active` | Equivalence linking and relationship expansion are fully operational; implemented in `036-meaning-equivalence-merge`. |
| 22 | Archivist Beast | `storage` | `current` | Backup, restore, manifests, export discipline, and retention-friendly workflows are active. |
| 23 | Librarian Beast | `storage` | `active` | Manages semantic consolidation and knowledge-base merging; implemented in `036-meaning-equivalence-merge`. |

## Smart Compression Strategy

The 23 beasts are worth keeping as internal design vocabulary, but they are not worth shipping as 23 peer runtime subsystems.

Use this rule:

- a beast is a capability boundary first
- a beast becomes a standalone module only when it has distinct state, algorithms, tests, and lifecycle pressure
- otherwise it should remain compressed into one of the six runtime modules

This keeps the engine small without discarding the design power of the beast model.

## Compressed Runtime Mapping

### `memory`

Keep these beasts compressed into the write path:

- Constitution Beast as write-time invariants and acceptance rules
- Scribe Beast for raw capture
- Extractor Beast for structured memory shaping
- Normalizer Beast for canonicalization
- Classifier Beast for lane assignment
- Scorer Beast for salience and confidence assignment

Do not split these into separate packages unless extraction/classification/scoring become independently benchmarked pipelines.

### `retrieval`

Keep these beasts compressed into one retrieval pipeline:

- Guardian Beast for boundary preservation at retrieval time
- Scout Beast for lexical recall
- Oracle Beast as optional semantic recall
- Navigator Beast for bounded relation and subject expansion
- Reranker Beast for result shaping
- Explainer Beast for provenance and reasoning output
- Scope Beast for anti-leak filtering and prioritization

The retrieval moat comes from composition quality, not from turning each stage into its own public subsystem.

### `hygiene`

Keep these beasts compressed into maintenance flows:

- Meerkat for contradiction detection
- Axolotl for rebuild/regeneration
- Bowerbird for taxonomy cleanup
- Decay Beast for retention and cooling
- Consolidator Beast for suggest-first consolidation
- Nutcracker for storage hygiene and maintenance

Split only the parts that develop expensive jobs, durable queues, or operator-facing controls.

### `profiles`

Keep these beasts close together:

- Constitution Beast for policy discipline
- Identity Beast for long-lived preference/profile state
- Guardian Beast for sensitive-boundary policy overlays

These are policy-heavy and should stay narrow until the repo needs a real policy engine.

### `storage`

Keep these beasts as durable data capabilities:

- Weaver Beast for explicit links and bounded graph structure
- Archivist Beast for backup/export/restore/sync artifacts
- Librarian Beast for indexing, stats, and stable organization

Storage should own durable state, not behavioral orchestration.

### `integration`

This is not a beast bucket. It is the narrow adapter layer that exposes Python-owned semantics through:

- `app.py`
- `surface.py`
- `cli.py`
- `mcp/server.py`

## Recommended Build Order

Build beasts in this order to maximize value without creating architecture drag.

### Tier 1: Core Moat

These deserve the strongest implementation effort first:

1. Scope Beast
2. Scout Beast
3. Reranker Beast
4. Explainer Beast
5. Meerkat
6. Archivist Beast
7. Weaver Beast
8. Identity Beast

Reason:

- they directly improve recall quality
- they preserve safety and trust
- they create clear user-visible differentiation

### Tier 2: High-Leverage Support

These should be implemented, but kept bounded:

1. Extractor Beast
2. Normalizer Beast
3. Classifier Beast
4. Scorer Beast
5. Navigator Beast
6. Bowerbird
7. Decay Beast
8. Guardian Beast
9. Librarian Beast

Reason:

- they improve quality and maintainability
- but they should not outrun the core recall loop

### Tier 3: Optional / Incremental Depth

These should only expand when benchmarks or operator pain justify them:

1. Oracle Beast
2. Axolotl
3. Consolidator Beast
4. Nutcracker
5. Constitution Beast as a dedicated policy subsystem

Reason:

- they add real power
- but they also add algorithmic and operational cost fast

## Execution Tranches For Partial Beasts

Use these tranches to deepen the remaining `partial` beasts without opening too many fronts at once.

### Tranche A: Ingest Precision

Beasts:

- Extractor Beast
- Normalizer Beast
- Classifier Beast
- Scorer Beast

Primary modules:

- `memory`
- `profiles` for policy hooks only if needed

Why this tranche exists:

- it improves write quality before adding more retrieval or hygiene complexity
- it reduces bad memory shape at the source instead of compensating later

Entry gates:

- repeated ingest produces noisy or weakly typed memories
- retrieval quality is being limited by poor subjects, summaries, or type assignment
- contributors need benchmarkable write-path precision improvements

Recommended sub-order:

1. Extractor Beast
2. Normalizer Beast
3. Classifier Beast
4. Scorer Beast

Per-beast deliverables and opening gates:

- Extractor Beast
  - deliverables: stable subject extraction, lightweight summary shaping, clearer candidate memory boundaries
  - opening gates: repeated manual fixes for missing subjects or weak summaries; retrieval misses rooted in poor source shaping
- Normalizer Beast
  - deliverables: canonical subject and entity normalization, alias cleanup, punctuation-safe subject shaping
  - opening gates: duplicate or fragmented memory clusters caused by naming drift or alias variance
- Classifier Beast
  - deliverables: more explicit lane assignment across `working`, `episodic`, `semantic`, and `procedural`
  - opening gates: memory type drift begins harming lifecycle behavior or retrieval ranking
- Scorer Beast
  - deliverables: bounded write-time salience and confidence shaping that remains explainable
  - opening gates: useful memories are consistently under-ranked because the write path lacks enough importance signal

### Tranche B: Retrieval Expansion Discipline

Beasts:

- Guardian Beast
- Navigator Beast

Primary modules:

- `retrieval`
- `integration` only for contract shaping if needed

Why this tranche exists:

- it deepens relationship expansion and boundary control without forcing semantic retrieval
- it improves recall reach while keeping anti-leak guarantees explicit

Entry gates:

- lexical-first retrieval is missing relevant neighbors that already exist locally
- maintainers observe boundary ambiguity or expansion behavior that needs stronger contracts
- context-pack recall quality stalls without bounded expansion improvements

### Tranche C: Lifecycle And Maintenance Depth

Beasts:

- Axolotl
- Decay Beast
- Consolidator Beast
- Nutcracker

Primary modules:

- `hygiene`
- `storage`

Why this tranche exists:

- it matures runtime maintenance only after the write and retrieval paths are stable enough to justify deeper lifecycle automation
- it keeps consolidation and cleanup suggest-first instead of destructive

Entry gates:

- maintenance passes become too manual or too slow
- stale, weak, or duplicate memories begin degrading retrieval quality materially
- rebuild flows need stronger derived-state regeneration than the current lightweight pass

### Tranche D: Policy And Knowledge Organization

Beasts:

- Constitution Beast
- Librarian Beast

Primary modules:

- `profiles`
- `storage`

Why this tranche exists:

- it formalizes policy and stable knowledge organization only after the core engine surfaces are trusted
- it avoids overbuilding governance and library semantics before enough operating evidence exists

Entry gates:

- maintainers need explicit invariant enforcement beyond current discipline and review practice
- operators need stronger stats, organization, or knowledge curation surfaces
- repeated implementation choices show that informal policy is no longer sufficient

## Post-034 Product Roadmap

Use this sequence after `034-axolotl-derived-rebuild-hardening` when the product goal is “remember meaning better, stay correct longer, and remain simple for non-technical users.”

Recommended slice order:

1. [x] `035-semantic-recall-core`
2. [x] `036-meaning-equivalence-merge`
3. [x] `037-correction-first-memory-flow`
4. [x] `038-simple-user-surface`
5. `039-memory-trust-shaping`
6. `040-long-term-consolidation`
7. `041-semantic-evaluation-harness`

Per-slice outcomes, primary capability, and opening gates:

- `035-semantic-recall-core`
  - product outcome: Aegis can recall related meaning even when wording changes materially
  - primary capability: `Oracle Beast` kept bounded inside `retrieval` as optional semantic recall over local memory
  - opening gates: lexical-first retrieval starts missing obviously similar memories; users repeat the same idea with different wording and recall quality stalls
- `036-meaning-equivalence-merge`
  - product outcome: Aegis stops storing multiple isolated memories that mean the same thing
  - primary capability: `Normalizer Beast` + `Weaver Beast` + `Librarian Beast` for equivalence grouping and duplicate reduction
  - opening gates: memory clusters fragment around paraphrases, aliases, or near-duplicate semantic facts
- `037-correction-first-memory-flow`
  - product outcome: Newer correct information can supersede or amend older memory without leaving both active ambiguously
  - primary capability: `Meerkat`, `Consolidator Beast`, and `Constitution Beast` policies for correction-first updates
  - opening gates: users need to say “that old memory is wrong; use this now” and the engine cannot represent that cleanly
- `038-simple-user-surface`
  - product outcome: Non-technical users can interact with memory through a tiny set of actions like remember, recall, correct, and forget
  - primary capability: `Guardian Beast` + `integration` contract shaping over existing `app`, `cli`, and MCP surfaces
  - opening gates: the engine is capable enough internally, but the public surface remains too technical to use comfortably
- `039-memory-trust-shaping`
  - product outcome: Aegis can express which memories are strong, weak, uncertain, or in tension
  - primary capability: `Scorer Beast`, `Explainer Beast`, and `Constitution Beast` for trust-oriented scoring and user-facing certainty shaping
  - opening gates: recall is correct often enough, but users cannot tell what to trust when multiple candidates exist
- `040-long-term-consolidation`
  - product outcome: Short-lived notes are gradually compressed into more durable knowledge without broad destructive automation
  - primary capability: `Consolidator Beast`, `Decay Beast`, and `Axolotl` maintenance flows in `hygiene`
  - opening gates: long-running use produces too many overlapping episodic notes and maintenance remains mostly manual
- `041-semantic-evaluation-harness`
  - product outcome: Aegis can be judged on meaning-level recall and correction quality instead of only keyword retrieval metrics
  - primary capability: benchmark and regression harnesses across `retrieval`, `memory`, and `hygiene`
  - opening gates: semantic and correction features begin landing and need a harder correctness contract than ad hoc examples

Roadmap guardrails:

- keep the runtime in the six-module model
- open only one roadmap slice at a time
- prefer stronger memory quality over more public tools
- keep user-facing language simple even when internal capabilities deepen

## Split / No-Split Rules

Do not create a separate runtime subsystem for a beast unless at least two of these are true:

- it has durable state or schema the rest of the module should not own
- it has algorithms that need independent benchmarking
- it has operator-facing controls or failure modes
- it has tests that naturally form an isolated contract
- it must evolve on a different cadence than its parent module

Default posture:

- keep beasts as roles
- keep runtime as six modules
- keep public APIs small
- move complexity into pipelines and contracts, not into sprawling package trees

## Internal-Only Beasts

These beasts should remain internal vocabulary and should not become public tool names:

- Constitution Beast
- Guardian Beast
- Scope Beast
- Bowerbird
- Axolotl
- Nutcracker
- Weaver Beast
- Librarian Beast

## Highest-Signal Beasts For Future Refactors

If a future feature needs to retain beast language in internal docs, the strongest candidates are:

- Constitution Beast
- Meerkat
- Axolotl
- Bowerbird
- Nutcracker
- Explainer Beast
- Reranker Beast
- Archivist Beast

These represent the most distinctive parts of Aegis:

- discipline
- contradiction handling
- rebuild and taxonomy hygiene
- storage hygiene
- explainable retrieval
- stable archival behavior
