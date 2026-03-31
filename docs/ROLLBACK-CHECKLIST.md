# Rollback Checklist

Target: recover from a bad release in under 5 minutes for the normal local-first deployment class.

## Use This When

- the service fails to stay up after restart
- Telegram replies are broken or duplicated
- recall/write behavior is clearly regressed
- sync import/export behavior is broken after a change

## Checklist

1. Stop making new code changes.
2. Identify the last known good artifact or commit.
3. Capture current evidence before changing anything:
   - `systemctl --user status openclaw-gateway.service`
   - current failure timestamp
   - relevant log excerpt
4. If memory integrity is in doubt, create a fresh backup before rollback.
5. Revert to the last known good artifact or code state.
6. Restart the service:
   `systemctl --user restart openclaw-gateway.service`
7. If the DB state itself is damaged, restore from the selected snapshot using the validated restore flow.
8. Verify recovery:
   - service is active
   - `memory-aegis-v7 registered` appears
   - one Telegram round-trip succeeds
   - no new critical log spam appears
9. Record what was rolled back and why.

## Stop Conditions

Stop and escalate if:

- the service still fails after rollback
- restore preview does not match the intended snapshot
- Telegram keeps duplicating replies after returning to the last known good build
