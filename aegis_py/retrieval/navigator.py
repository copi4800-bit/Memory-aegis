from dataclasses import dataclass
from typing import Any, List
from ..storage.manager import StorageManager
from ..storage.models import RETRIEVABLE_MEMORY_STATUS_SQL

@dataclass
class ExpandedResult:
    memory: dict[str, Any]
    hop_depth: int
    relation_type: str

class NavigatorBeast:
    """Handles graph traversal to expand retrieval results."""

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def expand_via_subject(self, seed_ids: List[str], max_hops: int = 2) -> List[ExpandedResult]:
        """Expands results by finding memories with the same subject."""
        if not seed_ids:
            return []
        
        placeholders = ",".join("?" for _ in seed_ids)
        query = (
            f"SELECT id, subject, scope_type, scope_id FROM memories "
            f"WHERE id IN ({placeholders}) AND status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})"
        )
        seeds = self.storage.fetch_all(query, tuple(seed_ids))
        
        expanded = []
        for seed in seeds:
            if not seed["subject"]:
                continue
            peers = self.storage.find_same_subject_peers(
                memory_id=seed["id"],
                scope_type=seed["scope_type"],
                scope_id=seed["scope_id"],
                subject=seed["subject"],
                limit=10
            )
            for peer in peers:
                expanded.append(ExpandedResult(
                    memory=peer,
                    hop_depth=1,
                    relation_type="same_subject"
                ))
        return expanded

    def expand_via_links(self, seed_ids: List[str], max_hops: int = 2) -> List[ExpandedResult]:
        """Duyệt memory_links table để mở rộng kết quả."""
        if not seed_ids:
            return []
            
        expanded = []
        current_level_ids = set(seed_ids)
        visited = set(seed_ids)
        
        for hop in range(1, max_hops + 1):
            if not current_level_ids:
                break
                
            placeholders = ",".join("?" for _ in current_level_ids)
            query = f"""
                SELECT target_id, link_type FROM memory_links WHERE source_id IN ({placeholders})
                UNION
                SELECT source_id as target_id, link_type FROM memory_links WHERE target_id IN ({placeholders})
            """
            rows = self.storage.fetch_all(query, tuple(current_level_ids) * 2)
            
            next_level_ids = set()
            for row in rows:
                tid = row["target_id"]
                if tid not in visited:
                    visited.add(tid)
                    next_level_ids.add(tid)
                    
                    mem_row = self.storage.fetch_one(
                        f"SELECT * FROM memories WHERE id = ? AND status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})",
                        (tid,),
                    )
                    if mem_row:
                        expanded.append(ExpandedResult(
                            memory=dict(mem_row),
                            hop_depth=hop,
                            relation_type=row["link_type"]
                        ))
            current_level_ids = next_level_ids
            
        return expanded
