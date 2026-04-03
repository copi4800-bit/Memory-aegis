from __future__ import annotations

import logging
from typing import Any
from ..storage.manager import StorageManager

logger = logging.getLogger(__name__)


class WeaverBeast:
    """
    The Weaver Beast is responsible for identifying and linking related memories.
    In the context of slice 036, it handles 'equivalence' links between
    memories that share the same semantic meaning.
    """

    def __init__(self, storage: StorageManager):
        self.storage = storage

    def link_equivalence(
        self,
        source_id: str,
        target_id: str,
        weight: float = 0.95,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Creates an explicit 'equivalence' link between two memories.
        This link indicates that both memories represent the same fact or intent.
        """
        logger.info(f"Weaving equivalence link: {source_id} <-> {target_id}")
        
        # Ensure metadata has the rule info
        final_metadata = metadata or {}
        if "rule" not in final_metadata:
            final_metadata["rule"] = "semantic_equivalence_detection"
        
        return self.storage.upsert_memory_link(
            source_id=source_id,
            target_id=target_id,
            link_type="equivalence",
            weight=weight,
            metadata=final_metadata,
        )

    def find_potential_duplicates(
        self,
        content: str,
        scope_type: str,
        scope_id: str,
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """
        Placeholder for a quick similarity check. 
        In a full implementation, this might call the SearchPipeline with the semantic flag.
        """
        # This will be integrated more deeply in the IngestEngine phase.
        return []

    def build_topology_report(self, memory_id: str, *, limit: int = 10) -> dict[str, object]:
        neighbors = self.storage.list_memory_neighbors(memory_id=memory_id, limit=limit)
        edge_count = len(neighbors)
        avg_weight = 0.0 if not neighbors else sum(float(item["link"]["weight"]) for item in neighbors) / edge_count
        unique_link_types = sorted({str(item["link"]["link_type"]) for item in neighbors})
        megarachne_topology_strength = min(
            0.99,
            0.26 + (min(edge_count, 6) * 0.08) + (min(avg_weight, 1.0) * 0.24) + (min(len(unique_link_types), 4) * 0.05),
        )
        return {
            "memory_id": memory_id,
            "edge_count": edge_count,
            "average_weight": round(avg_weight, 3),
            "link_types": unique_link_types,
            "megarachne_topology_strength": round(megarachne_topology_strength, 3),
        }
