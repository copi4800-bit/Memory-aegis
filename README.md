# TruthKeep Memory

Truth-aware memory for AI agents.

TruthKeep Memory is a local-first AI memory engine for agents, MCP hosts, and long-running assistant systems. It does more than store and retrieve notes. It keeps track of which fact is current, which fact was superseded, why a result was selected, and why competing memories were suppressed.

If you are looking for an explainable memory layer for AI agents, a truth-aware retrieval engine, or a governed long-term memory system that can survive corrections over time, this is what TruthKeep Memory is built for.

The core idea is simple:

- retrieval should not be the final decision
- memory should protect current truth
- every important result should be explainable

## Why It Is Different

Most memory systems stop at search and ranking.

TruthKeep Memory adds a governed decision layer on top:

- `winner / contender / superseded` truth handling
- correction-first recall
- `why this` and `why not` explanations
- evidence and governance traces
- long-horizon hygiene and retention checks

This makes it useful for agent systems that need memory to stay correct over time, not just relevant in the moment.

## What It Can Do

- Store memories by scope and type
- Recall memories through lexical + semantic retrieval
- Protect corrected facts from stale fact leakage
- Surface the selected truth with explanation and suppressed candidates
- Run spotlight, benchmark, gate, and gauntlet flows
- Simulate long-horizon survival and DB hygiene behavior

## Use Cases

- Agent memory with correction-safe recall
- Local-first memory for MCP tools and OpenClaw-style hosts
- Long-term memory for assistants that need explainability
- Memory systems where stale facts must not leak back into answers
- Governance-first memory experiments and evaluations

## Quick Start

```bash
npm install
```

Or:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the MCP server:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 aegis_py/mcp/server.py
```

Run the test suite:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 -m pytest tests
```

## Best Demos

Core spotlight:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/demo_core_spotlight.py
```

Conflict spotlight:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/demo_conflict_spotlight.py
```

Full-core showcase:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/demo_core_showcase.py
```

Product-facing experience brief:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/demo_experience_brief.py
python3 scripts/render_experience_brief_html.py
```

Consumer shell:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/demo_consumer_shell.py
python3 scripts/render_consumer_shell_html.py
```

Dashboard shell:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/demo_dashboard_shell.py
python3 scripts/render_dashboard_shell_html.py
```

Polished HTML report:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/render_core_showcase_html.py
```

## Validation

Truth spotlight benchmark:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/benchmark_truth_spotlight.py
python3 scripts/check_truth_spotlight_gate.py
python3 scripts/render_truth_spotlight_report.py
```

Broader gauntlet:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/aegis_gauntlet.py
```

Long-horizon survival:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/long_horizon_memory_survival.py
```

Compressed tier closure:

```bash
export PYTHONPATH=$PYTHONPATH:.
python3 scripts/benchmark_compressed_candidate_tier.py
python3 scripts/check_compressed_tier_gate.py
python3 scripts/render_compressed_tier_report.py
python3 scripts/check_compressed_tier_completion.py
```

This verifies that:

- current truth survives after simulated long horizons
- stale archived and superseded rows are cleaned up
- dormant semantic memory does not grow forever without pressure

## Public Repo Layout

```text
aegis_py/     runtime, storage, retrieval, governance, MCP
scripts/      demos, benchmarks, gates, gauntlets
tests/        regression and stress validation
docs/         short public-facing explanation docs
```

## Important Files

- `aegis_py/app.py`
- `aegis_py/core_showcase_surface.py`
- `aegis_py/spotlight_surface.py`
- `scripts/aegis_gauntlet.py`
- `scripts/long_horizon_memory_survival.py`
- `docs/WHY_AEGIS_CORE_WINS.md`

## License

MIT
