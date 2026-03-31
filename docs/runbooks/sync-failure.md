# Sync Failure Runbook

## Symptoms

- sync export/import returns an error
- scope policy appears wrong
- sync preview shows unexpected mismatch

## First Checks

1. Confirm the scope policy:
   the target scope must be `sync_eligible`
2. Run sync preview before any import.
3. Confirm the envelope path and revision information are the expected ones.

## Recovery

1. If export fails, verify the scope policy and retry once.
2. If import fails, stop and inspect preview output before retrying.
3. If revision mismatch is unexpected, do not force the import blindly.
4. If the failure followed a release, use the rollback checklist first, then re-test sync on the last known good build.

## Escalate If

- sync failure persists after one clean retry
- preview output contradicts the expected scope contents
- import changes the wrong scope or shows leakage risk
