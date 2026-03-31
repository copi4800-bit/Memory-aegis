# Production Excellence Roadmap

This file is a derivative execution note only.

- `.specify/memory/constitution.md` and future `specs/*` artifacts remain the source of truth.
- Use this note to sequence hardening work for the current Python-owned Aegis v7 runtime.
- The target is not "perfect". The governing target is: predictable, observable, recoverable.

## Current Baseline

Validated now:

- Telegram runtime integration is live.
- Everyday memory flows work in runtime and demo paths.
- Grounded recall publishes provenance and trust shape.
- Backup/list/preview flows work.
- Governance and background plan/shadow/apply/rollback work.
- Integration tests cover sync export/preview/import.

This means the next work should bias toward reliability discipline, not net-new capability sprawl.

## Phase 1: Hardening

Goal: core flows are provably correct and resistant to regression.

Definition of done:

- Every critical capability has unit, integration, and smoke coverage.
- Known historical failures have explicit regression tests.
- Mutating flows prove data-safety invariants.

Execution checklist:

- Lock acceptance coverage for:
  - remember
  - recall
  - correct
  - forget
  - backup
  - restore
  - sync
  - background apply
  - background rollback
- Add regression coverage for:
  - config/runtime mismatch
  - duplicate reply
  - polling stall
  - scope-policy drift
  - plugin/runtime warning regressions
- Define invariants:
  - no cross-scope leakage
  - no mutation during dry-run
  - rollback restores pre-apply state
  - restore preserves auditability
- Gate new capability changes on tests for the changed flow.

Suggested artifacts:

- `specs/070-production-hardening/`
- `tests/regression/`
- `scripts/smoke/`

## Phase 2: Observability

Goal: failures become obvious before they become dangerous.

Definition of done:

- Core runtime actions emit structured logs.
- Operators can answer "what failed, where, and how often" from logs and metrics.
- Health state is inspectable without reading raw SQLite tables.

Execution checklist:

- Standardize structured fields for:
  - `tool`
  - `scope_type`
  - `scope_id`
  - `session_id`
  - `latency_ms`
  - `result`
  - `error_code`
- Add counters/timers for:
  - remember success/failure
  - recall success/failure
  - sync export/preview/import
  - backup create/restore
  - background plan/apply/rollback
  - Telegram polling stalls
  - gateway restarts
- Keep `doctor` and startup probes aligned with the same health model.
- Define minimal alert conditions:
  - repeated polling stalls
  - repeated restart loops
  - elevated tool error rate
  - abnormal DB growth

Suggested artifacts:

- `specs/071-production-observability/`
- structured-log field contract
- operator alert thresholds

## Phase 3: Production Discipline

Goal: deployment behavior is controlled, reversible, and boring.

Definition of done:

- Every release passes a fixed release gate.
- Recovery is practiced, not assumed.
- Staging proves changes before production exposure.

Execution checklist:

- Maintain a staging environment that matches production shape.
- Define a release checklist:
  - build green
  - smoke green
  - integration green
  - Telegram live check green
  - backup/restore drill green
  - sync verification green
- Run soak tests at:
  - 30 minutes
  - 6 hours
  - 24 hours
- Write runbooks for:
  - polling stall
  - sync failure
  - DB lock
  - restore mismatch
  - duplicate reply
- Keep rollback under 5 minutes:
  - revert build
  - restart service
  - restore snapshot if needed

Suggested artifacts:

- `specs/072-production-discipline/`
- `docs/runbooks/`
- release gate checklist

## 80/20 Order

If only a small slice can land immediately, do this first:

1. Acceptance tests for critical flows.
2. Structured logs and minimal metrics.
3. Backup/restore drill against a separate DB.
4. 24h Telegram soak test.
5. Runbook and rollback checklist.

## Success Bar

The runtime may be called highly trustworthy for its current deployment class when:

- critical flows stay green across unit, integration, smoke, and soak layers
- failures are visible in logs/metrics without manual DB inspection
- recovery paths are rehearsed and fast
- no single operator mistake silently destroys memory integrity
