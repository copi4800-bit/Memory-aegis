# Roadmap: Memory Aegis v4 Evolution (Refined)

## Phase 1: Taxonomy Hardening
- [ ] Task 1.1: Expand technical taxonomy sub-labels in `core/models.ts` and update `Bowerbird.ts` classification rules.
- [ ] Task 1.2: Perform Audit-Trailed Migration & Reclassification for existing 3300+ nodes.
- [ ] Task 1.3: Refine classification confidence thresholds to minimize "technical.stack" bloat.
- [ ] Verification: Unlabeled count drops significantly; `technical.stack` distribution is balanced.

## Phase 2: Memory Hygiene & Consistency
- [ ] Task 2.1: Trace style conflict lineage using current system state.
- [ ] Task 2.2: Refine Meerkat/Zebra Finch logic for style supersede based on scope, provenance, and timestamp.
- [ ] Task 2.3: Consolidate overlapping persona/style rules while preserving scoped nodes and provenance.
- [ ] Verification: Known style conflicts are resolved or clearly explained in diagnostics.

## Phase 3: Linking & Graph Quality
- [ ] Task 3.1: Enrich edge generation in `Axolotl` (add family/episode/workflow edge types).
- [ ] Task 3.2: Improve `Eagle Eye` summaries for high-density graph support.
- [ ] Task 3.3: Audit edge quality to ensure graph density increases without adding noise.
- [ ] Verification: Graph density improves with clear semantic meaning; retrieval remains lightweight.

## Phase 4: Maintenance Automation
- [ ] Task 4.1: Verify `maintenanceCron` execution and stability.
- [ ] Task 4.2: Implement safe post-session maintenance pipeline.
- [ ] Task 4.3: Automate `Tardigrade` backups with restore verification and retention policy.
- [ ] Verification: Maintenance reports are integral; backup/restore cycles pass without lock/path regressions.

## Phase 5: Advanced Retrieval (Optional/Future)
- [ ] Task 5.1: Research Hop-based retrieval for graph-aware ranking.
- [ ] Task 5.2: Implement `Octopus` partitioning for thematic clustering.
- [ ] Verification: Benchmark retrieval quality; ensure no performance regression on default paths.
