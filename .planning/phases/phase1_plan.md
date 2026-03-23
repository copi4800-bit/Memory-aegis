# Phase 1 Plan: Diagnostics & Taxonomy Refinement

## Analysis Findings
1. **Unlabeled Gap:** 686 nodes are currently unlabeled, mostly stemming from automated session captures and legacy drift events.
2. **Technical Overload:** The `technical.stack` category is acting as a "catch-all" bucket for everything from code snippets to infrastructure logs.
3. **Drift Contradictions:** High severity drift events are cluttering the database, likely from the v3 -> v4 transition.

## Proposed New Taxonomy
- `technical.infra`: Docker, ENV, Proxy, Network configs.
- `technical.logic`: Core algorithms, business logic, function definitions.
- `technical.memory`: Aegis specific layers, node management, database schemas.
- `technical.media`: M3U, asset links, metadata.
- `identity.drift`: Automated logs of memory changes and contradictions.

## Action Tasks
1. [ ] Create a migration script to re-classify `technical.stack` into smaller sub-categories.
2. [ ] Update `Bowerbird` classifier rules to use the new taxonomy.
3. [ ] Perform a batch update on the 686 unlabeled nodes based on source path and keyword matching.
4. [ ] Run a test search to verify retrieval quality improvements.
