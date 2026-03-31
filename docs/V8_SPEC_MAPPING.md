# V8 Spec Mapping

This document maps the formal v8 theory notes to the current runtime implementation.

Reference notes:

- `/home/hali/.openclaw/7.md`
- `/home/hali/.openclaw/11.md`
- `/home/hali/.openclaw/12.md`

Status labels:

- `Exact`: the runtime has a direct, intentional implementation of the spec item.
- `Approx`: the runtime captures the behavior or intent, but not as a literal 1:1 implementation.
- `Missing`: the formal item is not yet represented as a first-class runtime concept.

## Summary

The current runtime is behaviorally aligned with the v8 model:

- evidence-aware memory admission
- state-aware retrieval and ranking
- conflict, trust, belief, decay, readiness, and feedback signals
- transition gates and benchmark-driven validation

The runtime is not yet a literal transcription of the full formal system. In particular, it does not persist the full continuous state vector and it does not maintain a global interacting field object as a first-class runtime structure.

## Mapping Table

| Spec item | Formal source | Runtime mapping | Status |
| --- | --- | --- | --- |
| Memory object `M_i(t) = (x_i, E_i, z_i(t), s_i(t), pi_i)` | `/home/hali/.openclaw/11.md` section 4 | `content`, `summary`, `subject`; evidence events/artifacts; dynamic signals; `memory_state` and `admission_state`; scope/policy surfaces | `Approx` |
| Semantic content `x_i` | `/home/hali/.openclaw/11.md` section 4.1 | Memory content fields plus summaries and subjects in the storage model and retrieval payloads | `Exact` |
| Evidence set `E_i` | `/home/hali/.openclaw/11.md` section 4.2 | Evidence events and artifacts in `aegis_py/storage/evidence.py`; ingest attaches evidence on write | `Exact` |
| Continuous state vector `z_i(t) = [c, u, d, kappa, r]^T` | `/home/hali/.openclaw/11.md` section 4.3 and `/home/hali/.openclaw/12.md` section 2.1 | Runtime computes `belief_score`, `usage_signal`, `decay_signal`, `conflict_signal`, `readiness_score` in `aegis_py/retrieval/v8_dynamics.py` | `Approx` |
| Discrete state set `{draft, validated, consolidated, hypothesized, invalidated, archived}` | `/home/hali/.openclaw/11.md` section 4.4 | `memory_state` and `admission_state`; state machine and transition history | `Exact` |
| Policy profile `pi_i` | `/home/hali/.openclaw/11.md` section 4.5 | Scope policy, validation policy gate, conflict resolution policy, sync policy | `Approx` |
| Interaction graph / matrix `A(t)` | `/home/hali/.openclaw/11.md` section 5 | Support and conflict weights, explicit links, graph expansion | `Approx` |
| Write operator `W(I_t)` | `/home/hali/.openclaw/12.md` section 3 | `AegisApp.put_memory()` and `IngestEngine.ingest()` | `Exact` |
| Initial belief from directness, specificity, reliability, completeness, noise | `/home/hali/.openclaw/12.md` section 3.2 | Write-time scoring profile and confidence/activation inference during ingest | `Approx` |
| Initial state `u(0)=0, d(0)=0, kappa(0)=0, r(0)=c(0)` | `/home/hali/.openclaw/12.md` section 3.4 | Runtime derives initial dynamics from confidence and metadata; not persisted as a literal initialized vector | `Approx` |
| Evidence quality function and bounded evidence signal | `/home/hali/.openclaw/12.md` section 4 | `_evidence_signal()` combines directness, specificity, reliability, completeness and applies `1 - exp(-x)` saturation | `Exact` |
| Support field `psi_i(t)` | `/home/hali/.openclaw/12.md` section 5 | `_support_signal()` from support weight | `Approx` |
| Conflict pressure `kappa_i(t)` | `/home/hali/.openclaw/12.md` section 5 | `_conflict_signal()` from conflict weight and direct conflict openness | `Approx` |
| Belief dynamics | `/home/hali/.openclaw/12.md` section 5 and later core equations | `_belief_score()` updates belief from evidence, support, usage, regret, decay, conflict | `Exact` |
| Trust aggregation `T_i(t)` | `/home/hali/.openclaw/12.md` trust section | `trust_score` derived from evidence, support, usage, stability, belief, regret, decay, conflict | `Exact` |
| Usage / regret / decay dynamics | `/home/hali/.openclaw/12.md` sections 6 and 19 | `_usage_signal()`, `_decay_signal()`, `apply_outcome_feedback()` | `Exact` |
| Retrieval readiness `r_i(t)` | `/home/hali/.openclaw/12.md` readiness section | `_readiness_score()` | `Exact` |
| Retrieval score `R_i(Q_t, t)` | `/home/hali/.openclaw/11.md` and `/home/hali/.openclaw/12.md` retrieval sections | lexical score blended with activation and v8 dynamic bonus in `aegis_py/retrieval/engine.py` | `Approx` |
| Retrieval probability / ranking | `/home/hali/.openclaw/12.md` retrieval probability | Ranked retrieval pipeline; not a literal persisted softmax probability contract | `Approx` |
| Transition operator `Tau` | `/home/hali/.openclaw/12.md` transition section | `_transition_gate()` and the v7 state machine | `Approx` |
| Outcome feedback and regret update | `/home/hali/.openclaw/11.md` regret and `/home/hali/.openclaw/12.md` feedback sections | `apply_outcome_feedback()` and `AegisApp.apply_v8_outcome_feedback()` | `Exact` |
| Global energy / objective | `/home/hali/.openclaw/7.md` and `/home/hali/.openclaw/12.md` energy/objective sections | `bundle_energy_snapshot()` computes bundle energy and objective losses | `Exact` |
| Benchmark gates for retrieval, transition, feedback | `/home/hali/.openclaw/7.md` and `/home/hali/.openclaw/12.md` research-to-simulator path | `tests/benchmarks/test_v8_dynamics_sli.py` | `Exact` |
| Global field state `Xi(t)` | `/home/hali/.openclaw/11.md` | No first-class runtime object for the whole memory field | `Missing` |
| Persistent first-class state vector per memory | `/home/hali/.openclaw/11.md` and `/home/hali/.openclaw/12.md` | Signals are partly derived and partly stored in metadata; not a normalized persisted vector contract | `Missing` |
| Literal continuous-time or explicit `t -> t+1` system update for all memories | `/home/hali/.openclaw/7.md` and `/home/hali/.openclaw/12.md` | Runtime is event-driven and operation-driven rather than global-step-driven | `Missing` |

## Key Runtime Anchors

- `aegis_py/app.py`: main orchestration surface
- `aegis_py/memory/ingest.py`: write path and evidence-backed admission
- `aegis_py/retrieval/engine.py`: retrieval score composition and state-aware gating
- `aegis_py/retrieval/v8_dynamics.py`: v8 dynamic signals, transition gate, feedback, energy, reason tags
- `aegis_py/v7/state_machine.py`: discrete state transitions
- `aegis_py/storage/evidence.py`: evidence events and artifacts
- `tests/benchmarks/test_v8_dynamics_sli.py`: benchmark gate for v8 behavior

## Practical Reading

The current codebase should be interpreted as:

- a practical v8 runtime with strong behavioral alignment
- a benchmarkable implementation of the core memory dynamics ideas
- not yet a literal 1:1 execution of the full formal mathematical system

If the project wants stronger formal fidelity later, the next step is not a rewrite. The next step is to define and persist a canonical v8 state contract per memory, then progressively migrate retrieval, hygiene, and governance to consume that contract directly.
