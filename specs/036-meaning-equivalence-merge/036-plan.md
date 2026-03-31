# Implementation Plan: Meaning Equivalence Merge

**Branch**: `036-meaning-equivalence-merge` | **Date**: 2026-03-24 | **Spec**: [036-spec.md](036-spec.md)

## Summary

Implement semantic deduplication and grouping to prevent memory fragmentation. The approach involves enhancing the `IngestEngine` to perform a semantic similarity check against recent memories and introducing a `Librarian Beast` in the `hygiene` module to consolidate existing equivalent memories.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/memory`, `aegis_py/hygiene`, `aegis_py/storage`  
**Storage**: SQLite (`memory_aegis.db`)  
**Testing**: `pytest` with paraphrased content pairs  
**Performance Goals**: Deduplication check should add < 500ms to ingestion.  
**Constraints**: Avoid heavy re-indexing during ingest; leverage existing `SearchPipeline` for similarity lookups.

## Implementation Steps

### Phase 1: Semantic Normalization & Detection
1. Enhance `SubjectNormalizer` or create `SemanticNormalizer` to generate semantic hints (e.g., via lightweight LLM or keyword clusters).
2. Update `IngestEngine.ingest` to perform a "pre-ingest search" using the `SearchPipeline` with the `semantic` flag enabled.
3. If a high-confidence match (score > 0.85) is found in the same scope and subject, consider it a potential duplicate.

### Phase 2: The Weaver Beast (Equivalence Linking)
1. Implement `WeaverBeast` in `aegis_py/memory/weaver.py` (or as a role).
2. Add a `link_equivalence` method to create explicit `equivalence` links between memories with a high weight.
3. Update `StorageManager` to handle `equivalence` link types specifically.

### Phase 3: The Librarian Beast (Merging & Consolidation)
1. Implement `LibrarianBeast` in `aegis_py/hygiene/librarian.py`.
2. Implement a `consolidate_equivalents` task that scans for `equivalence` links or subject clusters.
3. Define the merge logic:
    - Choose a "Master" (usually the most recent or highest activation).
    - Transition redundant memories to `superseded` status.
    - Update Master metadata with `merged_from` IDs and combined activation/access counts.

### Phase 4: Integration & Hygiene
1. Hook the `LibrarianBeast` into the `HygieneEngine.run_maintenance` pass.
2. Update `AegisApp` to expose merge/deduplication stats.

### Phase 5: Validation
1. Create tests with paraphrased pairs (English and Vietnamese).
2. Verify that `superseded` memories are filtered out of regular search results but accessible via direct ID.
3. Verify metadata preservation.
