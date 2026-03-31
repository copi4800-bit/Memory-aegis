import logging
from typing import Any, List
from ..storage.manager import StorageManager

logger = logging.getLogger(__name__)

class GuardianBeast:
    """Enforces scope boundaries for retrieved memories."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage
        
    def enforce_scope(self, results: List[dict[str, Any]], scope_type: str, scope_id: str) -> List[dict[str, Any]]:
        """Strictly filters results to only those within the allowed scope or global."""
        filtered = []
        for result in results:
            # Result could be a dict or an object depending on caller
            rs_type = result.get("scope_type") if isinstance(result, dict) else getattr(result, "scope_type", None)
            rs_id = result.get("scope_id") if isinstance(result, dict) else getattr(result, "scope_id", None)
            
            if rs_type == "global":
                filtered.append(result)
            elif rs_type == scope_type and rs_id == scope_id:
                filtered.append(result)
            else:
                self.detect_scope_leak(result, scope_type, scope_id)
        return filtered

    def detect_scope_leak(self, memory: Any, allowed_type: str, allowed_id: str):
        """Logs boundary violations."""
        mem_id = memory.get("id") if isinstance(memory, dict) else getattr(memory, "id", "unknown")
        mem_type = memory.get("scope_type") if isinstance(memory, dict) else getattr(memory, "scope_type", "unknown")
        mem_scope = memory.get("scope_id") if isinstance(memory, dict) else getattr(memory, "scope_id", "unknown")
        logger.warning(
            f"SCOPE LEAK DETECTED: Memory {mem_id} ({mem_type}:{mem_scope}) "
            f"leaked into context for {allowed_type}:{allowed_id}!"
        )

    def apply_scope_policy(self, scope_type: str, scope_id: str) -> dict[str, Any]:
        """Reads policy matrix from DB."""
        return self.storage.get_scope_policy(scope_type, scope_id)
