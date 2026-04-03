# TurboQuant for TruthKeep

## Executive Summary

TurboQuant-style ideas are potentially valuable for TruthKeep, but only in the **scale/performance substrate** of the system. They should **not** be allowed to replace or distort TruthKeep's truth-selection, governance, or correction logic.

The practical takeaway from the two public community repos is:

- `tonbistudio/turboquant-pytorch` is strongest as an **algorithmic cautionary reference**
- `0xSero/turboquant` is strongest as a **systems integration reference**

TruthKeep should borrow the parts that help compressed retrieval and long-horizon storage, while explicitly protecting its governed truth core.

## What the Two Repos Teach

### 1. Lessons from `tonbistudio/turboquant-pytorch`

This repo is the most useful source for understanding which parts of the original paper may or may not transfer to a practical memory system.

Key lessons:

- A proxy metric can look excellent while the final behavior still fails.
- QJL may be elegant mathematically but still be the wrong tradeoff in a softmax-driven or generation-driven path.
- Asymmetric precision matters.
- Residual windows and protected layers matter.

For TruthKeep, the most important lesson is this:

> Do not accept compressed-memory changes based only on similarity metrics.

Any future TruthKeep compression tier must be judged on:

- current-truth top-1 accuracy
- stale-fact rejection
- winner preservation
- governed recall behavior

### 2. Lessons from `0xSero/turboquant`

This repo is the best reference for system reality.

Key lessons:

- Compression savings depend heavily on where the real bottleneck lives.
- Not every model path is equally compressible.
- Freed memory does not automatically imply better total throughput.
- An honest audit is part of the implementation, not an optional afterthought.

For TruthKeep, the lesson is:

> A compression tier is only worth shipping if it reduces footprint or improves throughput without shifting the bottleneck into judged recall, governance, or reconstruction.

## Where TurboQuant-Style Compression Fits in TruthKeep

## Allowed Zones

These are promising integration zones:

### A. Cold Memory Vector Tier

Use compression for archived or long-horizon retrieval features.

Good fit:

- Mammoth
- Titanoboa
- Deinosuchus

Why:

- These paths benefit from lower footprint more than absolute precision.

### B. Candidate Prefilter Tier

Use compressed vectors to cheaply generate a bounded candidate set before full governed recall.

Good fit:

- Utahraptor
- Basilosaurus
- Pterodactyl

Why:

- This can reduce search cost while leaving final truth decisions untouched.

### C. Subject/Cluster Summaries

Use compressed summaries for dense topology or cluster heuristics.

Good fit:

- Megarachne
- Titanoboa
- Oviraptor

Why:

- These layers often need fast approximate structure, not exact final truth.

### D. Archive Footprint Reduction

Use bit-packed or tiered compression for older evidence and retrieval features.

Good fit:

- Mammoth
- Deinosuchus
- Librarian/Titanoboa surfaces

Why:

- This aligns naturally with long-horizon memory survival.

## Forbidden Zones

These layers must remain uncompressed or only consume compressed outputs indirectly:

### 1. Truth Registry

Do not compress:

- winner / contender / superseded state
- truth slot ownership
- correction lineage

### 2. Governance Engine

Do not let TurboQuant replace or override:

- policy invariants
- admission-state decisions
- contradiction review logic

### 3. Final Judged Recall Decision

Do not let compressed similarity become the final answer path.

Compressed tiers may propose candidates, but TruthKeep must still perform its full:

- scoring
- governance
- truth selection
- explanation

## Recommended Experimental Architecture

TruthKeep should use a **three-tier memory substrate**:

### Tier 1: Hot Truth Tier

Full precision, no compression.

Contains:

- active winners
- recent corrections
- policy-sensitive memories

### Tier 2: Warm Retrieval Tier

Moderate compression or lightweight approximation.

Contains:

- frequently recalled but not highly policy-sensitive memories
- rich retrieval features

### Tier 3: Cold Archive Tier

Aggressive compression.

Contains:

- archived memory vectors
- long-horizon subject clusters
- retrieval-only summaries

## What to Reuse Conceptually

TruthKeep should consider borrowing these ideas:

- asymmetric precision
- bit-packed storage
- compressed prefiltering
- protected high-importance tiers
- residual or partial full-precision windows for recent/high-value memory

TruthKeep should **not** assume that a paper-faithful TurboQuant path is automatically the best path for its retrieval substrate.

## Merge Gates for a Future Implementation

No TurboQuant-style feature should merge unless it proves all of the following:

### Accuracy Gates

- no regression in current-truth top-1
- no regression in stale-fact rejection
- no regression in winner preservation
- no regression in superseded exclusion

### Performance Gates

- lower memory footprint or storage footprint
- faster or cheaper candidate generation at meaningful scale
- no harmful shift of bottleneck into governed recall

### Reliability Gates

- explainability outputs remain stable
- spotlight/core_showcase still tell the same truth story
- long-horizon survival still passes

## Recommended Next Phase

The next sensible phase is not a full implementation. It is a bounded prototype:

### `116-compressed-candidate-tier-spike`

Goal:

- add a prototype compressed candidate prefilter
- only for archived/warm retrieval vectors
- benchmark it against TruthKeep’s governed recall

This would be the first phase where TurboQuant-style ideas touch running code.
