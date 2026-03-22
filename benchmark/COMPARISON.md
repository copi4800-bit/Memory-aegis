# Memory Aegis v4 — Comparative Positioning

## Aegis vs Cloud Memory (e.g., Mem0, Zep)

| Dimension | Cloud Memory | Aegis v4 |
|-----------|-------------|----------|
| **Data location** | Cloud servers, vendor-controlled | 100% local SQLite — data never leaves machine |
| **Latency** | Network round-trip (50-200ms) | Local disk (1-10ms typical) |
| **Privacy** | Depends on vendor policy | Complete — no network calls, no telemetry |
| **Embedding model** | Cloud LLM (OpenAI, etc.) | None required — FTS5 + Dragonfly trigram/synonym |
| **Offline support** | No | Full offline operation |
| **Cost** | Per-API-call pricing | Zero marginal cost |
| **Conflict detection** | Typically none | Meerkat contradiction scanner + Zebra Finch auto-supersede |
| **Context budgeting** | Basic token counting | Chameleon zone-based allocation (trauma → identity → task) |

**When to choose cloud**: You need cross-device sync or team-shared memory.
**When to choose Aegis**: Privacy matters, offline use, or you want cognitive features beyond simple recall.

## Aegis vs Vector-First Memory (e.g., ChromaDB, Pinecone-based)

| Dimension | Vector-First | Aegis v4 |
|-----------|-------------|----------|
| **Search method** | Embedding cosine similarity | FTS5 lexical + graph activation + Dragonfly rescue |
| **Dependency** | Requires embedding model (local or API) | Zero external dependencies |
| **Graph structure** | Flat document store | Knowledge graph with edges, entities, episodes |
| **Memory lifecycle** | Store and retrieve | Volatile → stable → crystallized → superseded → archived |
| **Decay model** | None (all memories equal) | Spaced repetition with interference scoring |
| **Taxonomy** | None or manual tags | Bowerbird auto-classification (16 frozen categories) |
| **Deduplication** | Embedding distance threshold | Salmon multi-hash fingerprinting (raw + normalized + structural) |
| **Procedural memory** | Not supported | Weaver Bird blueprint extraction with versioning |
| **Maintenance** | Manual cleanup | Auto: Meerkat scan → Zebra Finch supersede → Bowerbird classify |

**When to choose vector**: You need semantic similarity across languages or very large corpora (100K+ docs).
**When to choose Aegis**: You want structured memory with lifecycle management, not just a search index.

## Aegis vs Simple Plugin Recall (e.g., built-in memory, basic RAG)

| Dimension | Simple Recall | Aegis v4 |
|-----------|--------------|----------|
| **Architecture** | Flat file/chunk store | 16-layer cognitive engine |
| **Retrieval** | Keyword match or basic embedding | 7-stage pipeline (FTS5 → Entity → Orca → Sea Lion → Salmon → Rerank → Packet) |
| **Safety** | No special handling | Elephant anti-regression + Chameleon zone fencing |
| **Contradictions** | Accumulate silently | Meerkat detects + Zebra Finch auto-resolves |
| **Observability** | None | Eagle summary + Honeybee telemetry + memory_debug tool |
| **Explainability** | "Here's what matched" | Full signal breakdown (lexical, rescue, graph, entity, episode, policy) |
| **User experience** | Store/recall only | Profile, onboarding, 12 tools, 7 slash commands |
| **Presets** | One-size-fits-all | 4 presets (minimal, balanced, local-safe, max-memory) |

**When to choose simple**: You want minimal setup and don't need memory lifecycle management.
**When to choose Aegis**: You want memory that gets smarter over time, handles contradictions, and explains its decisions.

## What Aegis Does NOT Claim

- **Not a vector database replacement**: Aegis is purpose-built for agent memory, not general similarity search.
- **Not multilingual-native**: Dragonfly rescue works best for English and Vietnamese. Other languages work via FTS5 but lack synonym expansion.
- **Not a team collaboration tool**: Aegis is single-user, local-first. No built-in sync or multi-user support.
- **Not tested at massive scale**: Benchmarked up to ~1000 nodes. Performance at 100K+ nodes is untested.
