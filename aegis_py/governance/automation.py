import uuid
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from aegis_py.storage.db import DatabaseManager
from aegis_py.governance.policy import PolicyManager


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AutonomousAction:
    action_type: str  # 'resolve', 'archive', 'consolidate', 'escalate'
    entity_type: str  # 'memory', 'memory_link', etc.
    entity_id: str
    explanation: str
    confidence_score: Optional[float] = None
    details: Dict[str, Any] = None


class GovernanceException(Exception):
    """Raised when an autonomous action is blocked by policy or confidence gates."""
    pass


class AutonomousExecutor:
    """Executes automated mutations, enforcing policies, confidence gates, and audit trails."""

    def __init__(self, db: DatabaseManager, policy_manager: PolicyManager):
        self.db = db
        self.policy_manager = policy_manager
        
        # Define confidence gates for actions that require them
        self.confidence_gates = {
            'resolve': 0.90,
            'consolidate': 0.85
        }

    def _check_policy(self, scope_type: str, scope_id: str, action_type: str) -> bool:
        if action_type == 'resolve':
            return self.policy_manager.can_auto_resolve(scope_type, scope_id)
        elif action_type == 'archive':
            return self.policy_manager.can_auto_archive(scope_type, scope_id)
        elif action_type == 'consolidate':
            return self.policy_manager.can_auto_consolidate(scope_type, scope_id)
        elif action_type == 'escalate':
            # Not fully implemented policy yet, assume based on general config if needed
            policy = self.policy_manager.get_policy(scope_type, scope_id)
            return policy.auto_escalate
        return False

    def execute(self, 
                scope_type: str, 
                scope_id: str, 
                action: AutonomousAction, 
                mutation_fn: Callable[[DatabaseManager], None]) -> str:
        """
        Attempts to execute an autonomous mutation.
        
        1. Checks policy matrix to see if the action is allowed.
        2. Checks confidence gate (if applicable).
        3. Executes the mutation_fn within a transaction.
        4. Writes the explanation to autonomous_audit_log.
        
        Returns the audit_id of the executed action.
        Raises GovernanceException if blocked.
        """
        
        # 1. Policy Check
        if not self._check_policy(scope_type, scope_id, action.action_type):
            raise GovernanceException(f"Action '{action.action_type}' is disabled by policy for scope {scope_type}/{scope_id}")
            
        # 2. Confidence Gate
        gate = self.confidence_gates.get(action.action_type)
        if gate is not None:
            if action.confidence_score is None:
                raise GovernanceException(f"Action '{action.action_type}' requires a confidence score, but none was provided.")
            if action.confidence_score < gate:
                raise GovernanceException(
                    f"Action '{action.action_type}' blocked: confidence {action.confidence_score} is below the required gate {gate}."
                )

        audit_id = str(uuid.uuid4())
        
        # 3. Execution & Audit
        conn = self.db.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN TRANSACTION")
            
            # Execute the actual mutation (which will use the same connection/cursor if it uses self.db)
            mutation_fn(self.db)
            
            # Record audit
            cursor.execute(
                """
                INSERT INTO autonomous_audit_log (
                    id, action_type, entity_type, entity_id, explanation, 
                    confidence_score, applied_at, status, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'applied', ?)
                """,
                (
                    audit_id,
                    action.action_type,
                    action.entity_type,
                    action.entity_id,
                    action.explanation,
                    action.confidence_score,
                    _now_utc().isoformat(),
                    json.dumps(action.details or {})
                )
            )
            
            cursor.execute("COMMIT")
            return audit_id
        except Exception as e:
            cursor.execute("ROLLBACK")
            # We don't log failed attempts to execute here because they might be application bugs
            # rather than valid governed actions. But we could optionally log 'failed' status.
            raise e
