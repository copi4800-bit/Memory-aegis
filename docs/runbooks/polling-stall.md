# Polling Stall Runbook

## Symptoms

- Telegram stops receiving new messages
- service stays up but no new bot activity appears
- offsets stop moving

## First Checks

1. Check service health:
   `systemctl --user status openclaw-gateway.service`
2. Check recent logs around the suspected stall window.
3. Confirm whether the issue is polling only or full runtime failure.

## Recovery

1. If the service is wedged but not crashed, restart it:
   `systemctl --user restart openclaw-gateway.service`
2. Confirm `memory-aegis-v7 registered` after restart.
3. Send one Telegram sanity-check message.
4. Confirm offsets move again.

## Escalate If

- polling stalls recur in a short window
- restart does not restore message flow
- duplicate replies appear immediately after restart
