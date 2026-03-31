# DB Lock Runbook

## Symptoms

- SQLite reports `database is locked`
- writes fail intermittently
- backup or restore collides with live operations

## First Checks

1. Capture the exact failing command and timestamp.
2. Check whether a backup, restore, or sync import was running at the same time.
3. Confirm whether the lock is transient or repeating.

## Recovery

1. Stop concurrent heavy operations.
2. Retry the operation once.
3. If the lock persists, restart the service:
   `systemctl --user restart openclaw-gateway.service`
4. Re-run only the smallest verification step needed.

## Escalate If

- the lock returns after restart
- restore or import leaves the DB in a partial-looking state
- multiple operator actions compete for the same DB repeatedly
