# Why Aegis Core Wins

This page is about one specific Aegis advantage:

**Aegis does not only retrieve memory. It judges which memory is still true.**

That matters most when:

- an older fact and a newer correction both exist
- multiple contenders compete for the same subject
- lexical overlap is not enough to decide which memory should be trusted

## The Core Claim

The Aegis core combines:

- retrieval
- residual judgment scoring
- truth-state handling
- governance filtering
- why-not visibility

This means the engine can do more than rank matching memories. It can:

- prefer current truth over stale truth
- suppress superseded records
- expose why another candidate lost
- show the governance state behind the result

## Fastest Proof

Run the spotlight demo:

```bash
export PYTHONPATH=.
python3 scripts/demo_core_spotlight.py
```

What it demonstrates:

1. seed an old fact
2. seed a correction
3. query the same subject
4. show:
   - selected result
   - human-readable explanation
   - truth/governance state
   - why-not for the older fact

## Benchmark Proof

Run the deterministic truth benchmark:

```bash
export PYTHONPATH=.
python3 scripts/benchmark_truth_spotlight.py
```

What it measures:

- `current_truth_top1_rate`
- `superseded_visibility_rate`
- `suppressed_visibility_rate`

These are not generic memory metrics. They are the metrics that show whether Aegis is succeeding at truth-aware memory selection.

## Runtime Surface

Aegis now exposes the same story through a spotlight surface:

- Python runtime: `AegisApp.spotlight(...)`
- MCP/runtime tool: `memory_spotlight`

The spotlight shape is intentionally compact:

- selected memory
- why this result won
- truth state
- why-not alternatives

## Example Interpretation

When the spotlight output shows:

- `truth_role = winner`
- `governance_status = active`
- a superseded older fact under `why_not`

it means Aegis did the job it was built to do:

it kept the current truth in front and made the losing memory legible instead of silently mixing both.

## Bottom Line

Many memory systems help an agent remember more.

Aegis is strongest when the problem is:

**Which memory should still be believed right now?**

That is the core distinction this repo should keep proving.
