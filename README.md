# Memory Aegis v4 (Full Beast Architecture)

**Produced by Hali12**

**Version:** 4.0.0  
**Framework:** OpenClaw Plugin (Memory Slot)  
**Status:** Stable - System Verified

Memory Aegis v4 is a local-first, autonomic cognitive memory engine for OpenClaw. It provides a tiered memory structure using **22 specialized animal layers** to protect, evolve, and budget your AI's knowledge across pipelines—from simple storage to system-verified autonomy.

## 🐾 The 22 Cognitive Layers

### Phase 1: Core Storage & Safety Guard (v3.0)
1. **Elephant:** Long-term invariant memory. Essential facts that never change.
2. **Orca:** Semantic graph activation. Connects the dots between different topics.
3. **Dolphin:** Active working memory. Maintains context during your current session.
4. **Octopus:** Context splitting. Manages complex subgraphs and partitions.
5. **Sea Lion:** Logical inference. Inherits concepts and recognizes temporal patterns.
6. **Salmon:** Data Fingerprinting. De-duplicates information to keep DB clean.
7. **Nutcracker:** Micro-chunking. Breaks down large data and manages TTL hygiene.
8. **Tardigrade:** High-durability snapshots and exports.
9. **Planarian:** Deep restoration and memory rebuilding.

### Phase 2: Observability & Pruning (v3.5)
10. **Honeybee:** Telemetry and internal metric measurement.
11. **Viper:** Automatic backup rotation and interaction state caps.
12. **Leafcutter Ant:** Archives events > 90 days into compressed cold storage.
13. **Axolotl:** Regenerates derived knowledge links.
14. **EagleEye (Eagle):** Visual graph explorer generating whole-brain panorama reports.
15. **Chimpanzee:** Tool craft & Interaction trace capture for corrections.

### Phase 3: Autonomic Maturation (v4.0)
16. **Bowerbird:** Taxonomy classifier. Meticulously labels unclassified memory shards.
17. **Meerkat:** Conflict Sentinel. Scans the graph for contradictory facts.
18. **Zebra Finch:** Memory Consolidator. Resolves logic clashes via temporal superseding.
19. **Scrub Jay:** Episodic Grouping. Packages active memory traces into discrete episodes.
20. **Platypus:** Hybrid Semantic Rescue. In-memory cosine fallback for FTS lexical misses.
21. **Weaver Bird:** Procedural Extractor. Harvests tool execution blueprints quietly.
22. **Chameleon:** Zone Context Budgeting. Allocates context tokens to protect core persona from task overflow.

## 🛠 Available Tools
- `memory_stats`: View Honeybee telemetry.
- `memory_search`: Search deep memories using FTS5 (rescued by Platypus when necessary).
- `memory_store`: Persist specific facts.
- `memory_rebuild`: Manually trigger Axolotl regeneration.
- `memory_backup_upload`: Create snapshots (Tardigrade).
- `memory_backup_download`: Restore memory (Planarian).
- `memory_taxonomy_clean`: Trigger Bowerbird classification manually.

## 🚀 Quick Start for Beginners
Aegis v4 is designed to be fully autonomic. To set up the entire engine automatically, just run:

```shell
npm run setup
```

This one-click command will:
1. **Build** the biological cognitive layers.
2. **Initialize** the SQLite memory graph.
3. **Execute** a full health diagnostic (Aegis Doctor).
4. **Verify** storage and retrieval pipelines with a guided onboarding test.

Once finished, move this folder to `~/.openclaw/extensions/` and enable it in your configuration.

---
*Developed by Bim Bim & The OpenClaw Team.*
