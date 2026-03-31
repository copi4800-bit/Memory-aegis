# Governance Automation Usage Guide

**Feature**: `043-governance-automation`
**Target Audience**: Aegis Operators and Maintainers

The governance automation module allows Aegis to perform specific tasks (like archiving old memories or resolving clear conflicts) automatically, while strictly enforcing operator-defined boundaries and maintaining full traceability.

## Policy Matrix

Every scope in Aegis (e.g., `global`, `user:123`) has a `PolicyMatrix` which explicitly controls what the engine is allowed to do autonomously.

By default, all autonomous actions are **disabled**.

Operators can toggle these flags:
- `auto_resolve`: Allow the engine to resolve concurrent edit conflicts if confidence > 0.90.
- `auto_archive`: Allow the engine to automatically archive memories past their expiration date.
- `auto_consolidate`: Allow the engine to merge highly similar memories (confidence > 0.85).
- `auto_escalate`: Allow the engine to proactively alert operators to systemic anomalies.

## Audit Logs

"Explainable mutation is non-negotiable." 

Every action taken autonomously is recorded in the `autonomous_audit_log` table. Each entry includes:
- `action_type` (e.g., 'consolidate')
- `entity_type` and `entity_id`
- `explanation` (Human-readable reason)
- `confidence_score` (The computed safety score for the action)
- `details_json` (A snapshot of the previous state, used for rollbacks)

## Rollbacks

Because all automated actions capture the `previous_state` in the audit log, any action can be completely reverted to its byte-for-byte exact previous state using the `RollbackManager`.

### Example (Python API)
```python
from aegis_py.storage.db import DatabaseManager
from aegis_py.governance.rollback import RollbackManager

db = DatabaseManager("memory_aegis.db")
rollback_mgr = RollbackManager(db)

# Revert a specific autonomous action
audit_id = "123e4567-e89b-12d3-a456-426614174000"
rollback_mgr.rollback(audit_id)
```
After a rollback, the audit entry is marked `rolled_back` to prevent duplicate rollback attempts.