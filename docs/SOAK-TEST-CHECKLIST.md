# Soak Test Checklist

Use this after major runtime or host integration changes.

## Windows

- 30 minutes: pre-release confidence
- 6 hours: same-day stability
- 24 hours: production-shaped confidence

## Setup

1. Start from a green release gate.
2. Ensure observability snapshot and service logs are available.
3. Confirm backup/restore path is available before the soak begins.

## During The Soak

Track:

- service restarts
- Telegram polling stalls
- duplicate replies
- recall/remember latency spikes
- sync export/import failures
- DB lock errors
- abnormal DB growth

## Suggested Activity

- send periodic Telegram messages through normal usage paths
- exercise remember, recall, correct, forget
- run at least one backup preview and one restore preview
- if sync is in scope, run one export/preview/import cycle

## Abort Conditions

Stop the soak and switch to rollback/runbook mode if:

- the service enters a restart loop
- duplicate replies recur
- writes or recalls fail repeatedly
- DB lock errors repeat
- sync failures repeat after one retry

## Exit Criteria

Call the soak acceptable only if:

- no restart loop occurred
- no uninvestigated duplicate reply occurred
- no unresolved DB lock persisted
- the bot remained responsive for the full window
