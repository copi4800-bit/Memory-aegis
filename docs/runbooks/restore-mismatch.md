# Restore Mismatch Runbook

## Symptoms

- restore preview does not match the chosen snapshot
- restored records are missing or unexpected
- the operator is unsure which snapshot to trust

## First Checks

1. Run restore preview before any real restore.
2. Confirm snapshot path, timestamp, and intended scope.
3. Compare preview counts with the expected target scope.

## Recovery

1. Do not run a real restore if preview is surprising.
2. Pick a clearer snapshot or export and preview again.
3. If a bad restore already happened, use the rollback checklist and restore from the last known good snapshot.

## Escalate If

- preview data is internally inconsistent
- multiple snapshots disagree and none is clearly authoritative
- a restore changed data outside the intended scope
