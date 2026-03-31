# Implementation Plan: Semantic Recall Core

**Branch**: `035-semantic-recall-core` | **Date**: 2026-03-24 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/035-semantic-recall-core/spec.md)
**Input**: Feature specification from `/specs/035-semantic-recall-core/spec.md`

## Summary

Implement the `Oracle Beast` as a role in the `retrieval` module to provide optional semantic recall. The approach uses an LLM-based query expansion to identify related concepts, synonyms, and intent, which are then used to perform a broader lexical search over local memory. This ensures "meaning-based" recall while maintaining the local-first baseline.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: `aegis_py/retrieval`, `AegisApp`, `fastmcp` (for tool definition)  
**Storage**: SQLite (existing `memory_aegis.db` with FTS5)  
**Testing**: `pytest` for expansion logic and integration  
**Performance Goals**: < 2s for semantic expansion stage  
**Constraints**: Must be optional (toggleable), must remain bounded within `retrieval` module

## Constitution Check

- `Local-First Memory Engine`: Pass. Semantic expansion is an optional enhancement; local lexical search remains the baseline.
- `Explainable Retrieval Is Non-Negotiable`: Pass. Results will be tagged with `semantic_recall` and expansion reasons.
- `Safe Memory Mutation By Default`: Pass. Retrieval only.
- `Measured Simplicity`: Pass. `Oracle Beast` is a role, not a new subsystem.

## Project Structure

### Documentation

```text
specs/035-semantic-recall-core/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
aegis_py/retrieval/
├── oracle.py           # NEW: Oracle Beast role and expansion logic
├── engine.py           # UPDATED: Support for semantic search stage
├── search.py           # UPDATED: Integration of OracleBeast into pipeline
└── models.py           # UPDATED: SearchQuery and SearchResult updates
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Optional LLM dependency | Semantic recall requires understanding "meaning" which local FTS cannot do alone. | Hardcoded synonyms would be too brittle and not truly "semantic". |

## Implementation Steps

### Phase 1: Models & Interface
1. Update `SearchQuery` to include `semantic: bool` and `semantic_model: str | None`.
2. Update `CanonicalSearchResult` and `SearchResult` to support `semantic_recall` stage.

### Phase 2: Oracle Beast Implementation
1. Create `aegis_py/retrieval/oracle.py`.
2. Implement `OracleBeast` with a `expand_query(query: str) -> List[str]` method.
3. For the first version, use a "pseudo-semantic" expansion or a lightweight LLM call if an API key is available.

### Phase 3: Pipeline Integration
1. Update `SearchPipeline.search_with_expansion` to include the `OracleBeast` stage if `semantic` is enabled.
2. Ensure semantic results are blended and ranked correctly.

### Phase 4: Validation
1. Add unit tests for `OracleBeast`.
2. Add integration tests for `search_with_expansion` with the semantic flag.
3. Verify that `lexical` results still take precedence or are blended fairly.
