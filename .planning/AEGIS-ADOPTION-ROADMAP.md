# Aegis Adoption Roadmap

This file is a planning artifact. If it disagrees with `specs/*`, `specs/*` wins.

## Core Rule

Aegis should copy tactics, not strategy.

Borrow the parts that make strong memory systems easier to use, easier to love, and more obviously valuable.
Do not trade away the Aegis properties that make it disciplined and trustworthy.

## Aegis Invariants

These are not negotiable:

- scope isolation
- conflict-aware retrieval
- explainability
- hygiene and lifecycle discipline
- procedural memory
- local-first control

## The 12 Things Aegis Should Steal

### From Mem0

1. API surface that feels tiny and obvious
2. quickstart that reaches first value in minutes
3. onboarding that gets users to a successful first memory flow fast
4. integration story that is explicit and easy to follow

### From NeuralMemory

5. packaging that feels deliberate and polished
6. product storytelling that people can repeat after one read
7. benchmark and demo presentation that is visual and memorable
8. graph and association presentation that feels useful rather than academic

### From Strong RAG Systems

9. retrieval lanes that are visible and predictable
10. grounding and citations that make trust cheap
11. codebase and document access patterns that are easy to integrate
12. corpus/indexing discipline that keeps retrieval behavior legible

## Tranches

### Tranche A: Time To First Value

Goal: make Aegis feel usable immediately for a new person.

Items:

- tiny API/default surface
- quickstart in minutes
- fast onboarding success

Evidence targets:

- one short quickstart
- one “remember then recall” path that works in minutes
- one newcomer doc page with no operator jargon

Likely first feature slices:

- install/onboarding simplification
- beginner quickstart tightening
- examples focused on first success

### Tranche B: Product Love And Comprehension

Goal: make Aegis easier to understand, easier to demo, and easier to care about.

Items:

- packaging polish
- product storytelling
- benchmark/demo presentation
- graph/association presentation

Evidence targets:

- one polished product overview page
- one wow demo with scripted output
- one benchmark summary that non-specialists can read

Likely first feature slices:

- README/product narrative rewrite
- demo scripts and benchmark presentation
- graph insight views instead of raw dumps

### Tranche C: Grounded Retrieval UX

Goal: make trust and retrieval behavior legible without exposing internal chaos.

Items:

- retrieval lanes
- grounding/citations
- code/doc access patterns
- corpus/indexing discipline

Evidence targets:

- user-facing retrieval explanations that stay simple
- citations shown consistently where grounding matters
- one clear story for code/document memory access

Likely first feature slices:

- citation consistency
- retrieval-lane UX tightening
- code/document access guides and examples

### Tranche D: Integration And Adoption Story

Goal: make Aegis easy to plug in, evaluate, and recommend.

Items:

- explicit integration story
- developer-facing API examples
- benchmark comparability

Evidence targets:

- host integration guide
- stable examples for common embedding points
- one comparison-oriented benchmark summary

Likely first feature slices:

- SDK/examples cleanup
- host integration docs
- benchmark packaging

## Anti-Goals

Do not copy blindly:

- managed-only dependency
- graph cult complexity
- marketing claims beyond the current product truth
- complexity added only to look advanced

## Bottom Line

The target state is:

- easy to use like Mem0
- easy to love like NeuralMemory
- grounded like strong RAG systems

while still staying:

- disciplined
- correct
- explainable
- trustworthy
- local-first
