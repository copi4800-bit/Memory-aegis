# TruthKeep Prehistoric Execution Priorities

This document decides which prehistoric beasts should become executable core behavior first.

## Selection Rule

Prioritize beasts that:

- strengthen the current moat directly
- fit the existing proof stack
- land with bounded risk

## First Five Beasts

1. **Dunkleosteus** (`Scorer`)
2. **Tyrannosaurus Rex** (`Reranker`)
3. **Thylacoleo** (`Meerkat`)
4. **Mammoth** (`Archivist`)
5. **Archelon** (`Constitution Beast`)

## Why These Five

### Dunkleosteus

- biological edge: crushing decisive bite
- math: salience clamp, confidence weighting, decisive thresholds
- landing zone:
  - `aegis_py/memory/scorer.py`
  - `aegis_py/memory/ingest.py`

### Tyrannosaurus Rex

- biological edge: apex dominance
- math: top-k dominance pressure, elimination margin
- landing zone:
  - `aegis_py/retrieval/search.py`
  - `aegis_py/v10_scoring/`
  - `aegis_py/v10/`

### Thylacoleo

- biological edge: hidden threat detection
- math: conflict sentinel score, contradiction early-warning threshold
- landing zone:
  - `aegis_py/conflict/`
  - `aegis_py/hygiene/`
  - `aegis_py/memory/ingest.py`

### Mammoth

- biological edge: cold-preserved endurance
- math: low-decay archival persistence, archive survivability
- landing zone:
  - `aegis_py/storage/`
  - `aegis_py/operations.py`
  - `scripts/long_horizon_memory_survival.py`

### Archelon

- biological edge: epoch-spanning endurance
- math: invariant constraints, hard floors, non-negotiable policy bounds
- landing zone:
  - `aegis_py/v10/policy.py`
  - `aegis_py/v10/engine.py`
  - future `profiles/` compatibility layer

## Rollout Order

### First

- Dunkleosteus
- Thylacoleo

### Second

- Tyrannosaurus Rex
- Archelon

### Third

- Mammoth

## Verification Rule

A prehistoric beast becomes real only when it survives:

- targeted tests
- `pytest -q tests`
- spotlight behavior where relevant
- gauntlet behavior where relevant
- long-horizon behavior where relevant

## Second Tranche

After the first five land cleanly, the next bounded tranche should prioritize:

1. **Meganeura** (`Scribe`)
2. **Ammonite** (`Normalizer`)
3. **Paraceratherium** (`Explainer`)

These three extend the same governing chain through:

- richer ingest capture
- stronger canonical subject stability
- more legible governed explanation output

## Third Tranche

After tranche two lands cleanly, the next bounded tranche should prioritize:

1. **Utahraptor** (`Scout`)
2. **Basilosaurus** (`Oracle`)
3. **Pterodactyl** (`Navigator`)

These three deepen retrieval through:

- lexical pursuit
- semantic echo
- bounded graph overview

## Fourth Tranche

After tranche three lands cleanly, the next bounded tranche should prioritize:

1. **Dimetrodon** (`Extractor`)
2. **Chalicotherium** (`Classifier`)
3. **Oviraptor** (`Bowerbird`)

These three deepen ingest and cleanup through:

- feature separation
- lane ecology fit
- taxonomy ordering

## Fifth Tranche

After tranche four lands cleanly, the next bounded tranche should prioritize:

1. **Diplocaulus** (`Axolotl`)
2. **Smilodon** (`Decay Beast`)
3. **Glyptodon** (`Consolidator`)

These three deepen hygiene through:

- regeneration confidence
- retirement pressure
- consolidation shell strength

## Sixth Tranche

After tranche five lands cleanly, the next bounded tranche should prioritize:

1. **Deinosuchus** (`Nutcracker`)
2. **Titanoboa** (`Librarian`)
3. **Megarachne** (`Weaver`)

These three deepen storage through:

- compaction pressure
- index locality
- topology strength

## Seventh Tranche

After tranche six lands cleanly, the final bounded tranche should prioritize:

1. **Argentinosaurus** (`Scope Beast`)
2. **Dire Wolf** (`Identity Beast`)
3. **Megatherium** (`Guardian Beast`)

These three complete the core through:

- scope geometry
- identity persistence
- boundary admissibility
