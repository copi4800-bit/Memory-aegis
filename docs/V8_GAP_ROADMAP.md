# V8 Gap Roadmap

This roadmap focuses on the smallest set of changes that would move the runtime from strong behavioral alignment toward stronger formal fidelity with the v8 theory notes.

Reference:

- [V8_SPEC_MAPPING.md](/home/hali/.openclaw/extensions/memory-aegis-v7/docs/V8_SPEC_MAPPING.md)

## Priority 1

### 1. Persist a canonical v8 state contract per memory

Goal:

- make the runtime state explicit instead of partly derived and partly implicit

Add a normalized per-memory state contract, for example:

```json
{
  "belief_score": 0.0,
  "usage_signal": 0.0,
  "decay_signal": 0.0,
  "conflict_signal": 0.0,
  "readiness_score": 0.0,
  "trust_score": 0.0,
  "regret_signal": 0.0,
  "stability_signal": 0.0,
  "feedback_count": 0.0,
  "belief_delta": 0.0,
  "last_v8_update_at": "..."
}
```

Why first:

- this is the bridge between the formal model and the runtime
- it reduces hidden coupling between retrieval-time recomputation and stored memory behavior
- it makes debugging and audits much easier

Suggested implementation:

- define one canonical serializer/deserializer
- store under a single metadata key such as `v8_state`
- migrate current `v8_dynamics` metadata into that contract

### 2. Separate derived signals from persisted state

Goal:

- avoid mixing stored state with query-specific or runtime-only calculations

Persist:

- belief
- usage
- decay
- conflict
- readiness
- regret

Derive at retrieval time:

- query-conditioned retrieval score
- dynamic score bonus
- query-specific reason tags
- bundle objective over a selected result set

Why:

- the formal notes separate system state from retrieval-time decision logic
- this reduces ambiguity about what changed after feedback versus what changed only because of a new query

## Priority 2

### 3. Make the transition operator a first-class runtime surface

Goal:

- move from “transition logic exists” to a clear `Tau`-like contract

Add:

- one function or service that accepts current memory state and outputs transition decision
- explicit persistence of transition inputs and outputs
- a stable transition reason schema

Why:

- the notes treat transition as a core operator, not an incidental detail
- this improves explainability for `draft -> validated`, `validated -> hypothesized`, and later `validated -> consolidated`

### 4. Normalize support and conflict into explicit edge/state inputs

Goal:

- reduce the gap between the formal interaction field and the current ad hoc support/conflict weights

Add:

- a stable representation for support and conflict contributors
- explicit provenance for why support/conflict weights were computed
- optional cached aggregate values on each memory

Why:

- the current runtime captures the behavior, but not the structure of the interaction system
- this would make `A(t)` approximations much more inspectable

## Priority 3

### 5. Promote trust and readiness to first-class observable fields

Goal:

- stop treating them as mostly retrieval-side internals

Add:

- storage visibility for current trust/readiness snapshots
- operator surfaces to inspect them directly
- tests that assert trust/readiness stability across key workflows

Why:

- the notes make both quantities central
- product behavior already depends on them, so they should be inspectable without reading internal code

### 6. Add a formal field snapshot surface for `Xi(t)`

Goal:

- expose a coarse-grained whole-system snapshot without building a heavy simulation framework

Example payload:

```json
{
  "counts": {
    "draft": 0,
    "validated": 0,
    "consolidated": 0,
    "hypothesized": 0,
    "invalidated": 0,
    "archived": 0
  },
  "averages": {
    "belief_score": 0.0,
    "trust_score": 0.0,
    "readiness_score": 0.0,
    "conflict_signal": 0.0,
    "decay_signal": 0.0
  },
  "energy": {
    "bundle_energy_proxy": 0.0,
    "objective_proxy": 0.0
  }
}
```

Why:

- the theory is about a memory field, not only isolated memories
- this gives you practical observability without requiring full continuous-time simulation

## Priority 4

### 7. Tighten write-time belief initialization against the formal feature set

Goal:

- align initial confidence more explicitly with the formal write operator

Current runtime already uses write-time scoring. Strengthen it by making the feature mapping explicit:

- directness
- specificity
- source reliability
- evidence completeness
- ambiguity/noise

Why:

- this is one of the cleanest places to improve formal fidelity with low architectural risk

### 8. Expand benchmark gates from behavior to state fidelity

Goal:

- test not only outcomes, but also whether internal state evolves in expected directions

Add benchmark assertions such as:

- evidence gain should increase belief and trust
- repeated successful retrieval should increase usage and readiness
- persistent conflict should increase conflict and demotion pressure
- failure/override should increase regret and reduce effective trust/readiness

Why:

- this is the safest way to drive the runtime closer to the formal model without a rewrite

## Recommended order

1. Persist canonical `v8_state`
2. Separate persisted state from query-derived signals
3. Make transition a first-class operator surface
4. Normalize support/conflict inputs
5. Expose trust/readiness directly
6. Add `Xi(t)` snapshot surface
7. Tighten write-time initialization
8. Expand benchmark gates to internal state fidelity

## Non-goals for now

These would add cost quickly and should wait:

- full continuous-time simulation engine
- literal global interaction matrix materialization for every query
- full Bayesian graph update machinery
- forcing every formal variable into a dedicated SQL column immediately

## Practical target

If the team completes the first four items, the runtime would move from:

- behaviorally strong v8

to:

- behaviorally strong v8 with a credible explicit state model

That is the right threshold before attempting a deeper formalization pass.
