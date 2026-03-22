# Memory Aegis v4 — Public Benchmark Pack

## Quick Start

```bash
# Run full benchmark suite
npx tsx benchmark/run-all.ts

# Output JSON report
npx tsx benchmark/run-all.ts --json --output report.json

# Run gate check (all tests)
bash scripts/gate-check.sh
```

## Metrics Explained

### Retrieval Quality

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Hit@5** | % of queries where at least 1 correct result appears in top 5 | ≥ 70% |
| **Recall@5** | Average fraction of relevant results found in top 5 | ≥ 40% |
| **MRR@10** | Mean Reciprocal Rank — how high the first correct result ranks | ≥ 0.4 |
| **nDCG@10** | Normalized Discounted Cumulative Gain — graded relevance quality | informational |
| **ScopeLeakRate@5** | % of top-5 results from wrong scope (cross-project contamination) | ≤ 20% |
| **ConflictLeakRate@10** | % of top-10 results that are expired/forbidden | ≤ 10% |
| **Latency p95** | 95th percentile query latency | ≤ 500ms |

### Layer Benchmarks

| Layer | What's tested | Pass criteria |
|-------|---------------|---------------|
| **Dragonfly** | Synonym expansion + trigram rescue when FTS5 misses | Rescue rate > 0% |
| **Bowerbird** | Taxonomy classification accuracy + confidence scoring | ≥ 80% classify rate, 0 stray labels |
| **Weaver Bird** | Fact vs procedure filtering, blueprint versioning | All checks pass |
| **Chameleon** | Zone 0 preservation, topK budget enforcement | Zone 0 never dropped |
| **Eagle** | Health score generation, summary report | Report generates successfully |

## Query Groups

The benchmark uses 20 ground-truth queries across 7 groups:

| Group | Count | Tests |
|-------|-------|-------|
| **lexical** | 2 | Direct FTS5 keyword matching |
| **entity** | 2 | Entity name resolution (@mentions) |
| **graph** | 2 | Spreading activation across linked nodes |
| **multiterm** | 2 | Multi-keyword conjunction |
| **anti-leak** | 2 | Scope isolation + expired node filtering |
| **cross-scope** | 4 | Same keywords, different project scopes |
| **near-topic** | 3 | Adjacent topics within same project |
| **temporal** | 3 | Current vs deprecated/expired content |

## Fixture Dataset

The benchmark uses a synthetic "StarProject" dataset with:
- 12 base nodes (backend, frontend, database, team, auth, ops, etc.)
- 11 extended nodes (cross-scope traps, near-topic traps, temporal traps)
- Scopes: `user`, `other_project`, `infra_project`, `another_project`
- Expired nodes for temporal correctness testing

## Architecture vs Competitors

See [COMPARISON.md](./COMPARISON.md) for positioning analysis.
