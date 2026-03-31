# Tasks: Meaning Equivalence Merge

**Input**: Design documents from `plans/036-spec.md`, `plans/036-plan.md`

## Phase 1: Semantic Detection (Foundational)

- [ ] T001 [P] [US1] Create `aegis_py/memory/weaver.py` and define `WeaverBeast` role.
- [ ] T002 [US1] Enhance `IngestEngine` in `aegis_py/memory/ingest.py` to accept an optional `SearchPipeline` (or use a lightweight similarity check).
- [ ] T003 [US1] Implement semantic similarity check in `IngestEngine.ingest` before creating a new memory record.
- [ ] T004 [US1] Define "High Confidence" match threshold (default 0.85) in `aegis_py/memory/models.py`.

**Checkpoint**: Ingest engine can now detect potential semantic duplicates.

---

## Phase 2: User Story 1 - Equivalence Linking (P1)

- [ ] T005 [US1] Implement `WeaverBeast.link_equivalence(source_id: str, target_id: str)` to create explicit equivalence links.
- [ ] T006 [US1] Update `StorageManager.put_memory` in `aegis_py/storage/manager.py` to optionally trigger a merge or link event if a semantic duplicate is detected.
- [ ] T007 [US1] Update `AegisApp.put_memory` to orchestrate the "detect and link" flow.

**Checkpoint**: Semantic duplicates are now linked or updated instead of just ignored.

---

## Phase 3: User Story 2 - Librarian Beast (P2)

- [ ] T008 [P] [US2] Create `aegis_py/hygiene/librarian.py` and define `LibrarianBeast` role.
- [ ] T009 [US2] Implement `LibrarianBeast.consolidate_equivalents(storage)` to scan for and merge equivalence clusters.
- [ ] T010 [US2] Define merge rules in `LibrarianBeast` (Master selection, score aggregation, metadata merging).
- [ ] T011 [US2] Hook `LibrarianBeast` into `HygieneEngine.run_maintenance`.

**Checkpoint**: Background consolidation is functional.

---

## Phase 4: User Story 3 - Explainable Merges (P2)

- [ ] T012 [US3] Implement `LibrarianBeast._merge_metadata` to include `merged_from` trace.
- [ ] T013 [US3] Ensure `superseded` status is correctly handled in all search and retrieval APIs (default filter).

**Checkpoint**: Merged memories show their history and why they were consolidated.

---

## Phase 5: Validation

- [ ] T014 [P] Unit test for `WeaverBeast` linking in `tests/memory/test_weaver.py`.
- [ ] T015 [P] Unit test for `LibrarianBeast` merge logic in `tests/hygiene/test_librarian.py`.
- [ ] T016 Integration test for end-to-end semantic deduplication in `tests/memory/test_semantic_dedupe.py`.

**Checkpoint**: Slice 036 is validated.
