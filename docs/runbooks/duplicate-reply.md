# Duplicate Reply Runbook

## Symptoms

- Telegram receives two replies for one user message
- offsets move but response behavior is duplicated
- bot logic looks healthy except for duplicate send behavior

## First Checks

1. Capture the message timestamp and IDs.
2. Check whether the duplicate came from polling replay, service restart overlap, or app-level duplicate send.
3. Confirm whether the issue happened once or is recurring.

## Recovery

1. If duplicates started after a fresh release, use the rollback checklist.
2. If the service restarted around the same time, treat it as a possible replay artifact and verify whether it repeats.
3. Restart the service once if the issue appears active:
   `systemctl --user restart openclaw-gateway.service`
4. Send one new sanity-check message and observe whether duplication persists.

## Escalate If

- duplicates recur after rollback or clean restart
- duplicates appear without any restart/polling anomaly
- the same input is being processed twice in logs with no obvious replay cause
