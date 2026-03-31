# Feature Spec: Apocalypse Runtime

**Feature Branch**: `073-apocalypse-runtime`  
**Status**: Draft

## Goal

Add one apocalypse-grade runtime harness that tests three production-danger seams together:

1. concurrent multi-host read/write pressure
2. corrupted snapshot / corrupted live-db detection
3. operator recovery from a clean snapshot with canary verification

## Scope

- Add one standalone Python harness under `scripts/`
- Emit one JSON report with explicit pass/fail checks
- Emit profile-specific latency and retry budgets in the report and evaluation
- Add one bounded test proving the harness catches corruption and validates recovery on a reduced profile

## Non-Goals

- Full chaos monkey coverage for every SQLite failure mode
- Cloud/distributed recovery orchestration
- Reopening broad capability or architecture scope

## Success Criteria

- Corrupted snapshot preview is rejected
- Corrupted live database cannot boot as healthy runtime
- Recovery from clean snapshot succeeds
- Recovered runtime reaches `HEALTHY` or `DEGRADED_SYNC`
- Canary recall succeeds after recovery
- Concurrency war finishes without unrecoverable operation errors on the bounded profile
- Profile-specific latency and retry budgets are evaluated explicitly for concurrency pressure
- Performance gates stay within the current optimized envelope:
- `quick`: write p95 <= 150ms, search p95 <= 100ms, context p95 <= 100ms, retries <= 5
- `apocalypse`: write p95 <= 800ms, search p95 <= 250ms, context p95 <= 300ms, retries <= 10
- `overload`: write p95 <= 1100ms, search p95 <= 300ms, context p95 <= 350ms, retries <= 20
