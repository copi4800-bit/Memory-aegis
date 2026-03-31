# Research: Aegis Python vNext Memory Engine

**Feature**: [`001-aegis-vnext-memory-engine`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/specs/001-aegis-vnext-memory-engine/spec.md)  
**Date**: 2026-03-23

## Scope

This research note captures the current brownfield findings that informed the initial implementation work for Phase 0, Phase 1, and the start of Phase 2.

## Key Findings

### 1. The codebase had two active storage contracts

There were two overlapping storage/domain lines:

- [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py) + [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py)
- [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) + [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py)

These lines disagreed on:

- model implementation style
- field naming and serialization
- retrieval result shape
- responsibility boundaries

### 2. `storage.models` and runtime environment were inconsistent

[`aegis_py/storage/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py) depended on `pydantic`, but the current environment does not have `pydantic` installed. This made `StorageManager`, ingestion, and retrieval/app paths fragile even before deeper refactor work.

Decision:

- Replace `pydantic` usage in storage/retrieval models with dataclass-based contracts that work in the current environment and keep the API surface simple.

### 3. Schema sources were drifting

[`aegis_py/storage/schema.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.py) and [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) had materially different definitions for:

- `style_signals`
- `style_profiles`

Decision:

- Treat [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) as the single SQL source of truth.
- Make [`aegis_py/storage/schema.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.py) load the SQL file directly.

### 4. Preference tracking and cognition used incompatible style-signal shapes

Preference code under:

- [`aegis_py/preferences/extractor.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/preferences/extractor.py)
- [`aegis_py/preferences/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/preferences/manager.py)

expected `session_id`, `scope_id`, `scope_type`, `signal_key`, and `signal_value`.

Meanwhile [`aegis_py/cognition/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/cognition/core.py) expected `agent_id` and `signal`.

Decision:

- Use a compatibility-friendly `style_signals` schema that supports both shapes instead of forcing an early product decision that would break one of the existing paths.

### 5. `StorageManager` had unstable persistence semantics

[`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) opened a new SQLite connection for each call. This broke `:memory:` behavior and made persistence semantics less explicit.

Decision:

- Reuse a single connection per `StorageManager` instance and add an explicit `close()` method.

### 6. Retrieval had two active result contracts

There were two retrieval result shapes:

- rich explainability in [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py) using `reasons`, scope fields, and `conflict_status`
- simpler app-facing results in [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) using `memory`, `score`, `reason`, and `provenance`

Decision:

- Move the retrieval path toward a richer canonical contract while preserving compatibility properties (`reason`, `provenance`) for current app/tests.

## Decisions Applied

The following implementation decisions have already been applied in the codebase:

- [`aegis_py/storage/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/models.py) converted to dataclass models
- [`aegis_py/retrieval/models.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/models.py) converted to dataclass models
- [`aegis_py/storage/schema.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.py) now loads [`schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql)
- [`aegis_py/storage/schema.sql`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/schema.sql) updated to support both preference and cognition signal shapes
- [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) updated for canonical serialization and connection reuse
- [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) now emits richer explanation data while remaining backward-compatible for app callers

## Verification Performed

Validated successfully:

- `python3 -m unittest tests/test_memory_core.py -v`
- `python3 -m unittest tests/test_memory_lifecycle.py -v`
- `python3 -m unittest tests/test_benchmark_core.py -v`
- smoke tests for `StorageManager`, `PreferenceManager`, retrieval scenarios, and `AegisApp`

Not yet validated in this environment:

- `pytest`-based test files such as [`tests/test_storage.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_storage.py), [`tests/test_retrieval.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py), and [`tests/test_preferences.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_preferences.py), because `pytest` is not installed here

## Remaining Gaps

- [`aegis_py/memory/core.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/memory/core.py) and [`aegis_py/retrieval/search.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/search.py) are still separate retrieval implementations
- [`aegis_py/storage/db.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/db.py) and [`aegis_py/storage/manager.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/storage/manager.py) still represent two persistence layers
- integration test coverage in [`tests/test_integration.py`](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_integration.py) has not yet been expanded to lock the new canonical contract

## Current Recommendation

Proceed next with retrieval unification:

1. choose one canonical search implementation for both benchmark and app usage
2. adapt the other path into a thin adapter or retire it
3. expand explainability and conflict-visibility regression coverage
