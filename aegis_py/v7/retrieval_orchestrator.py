from __future__ import annotations

from dataclasses import dataclass

from ..retrieval.models import SearchQuery, SearchResult
from ..retrieval.search import SearchPipeline
from ..storage.manager import StorageManager
from .storage_surfaces import SpecializedStorageSurfaces


@dataclass
class RetrievalBundle:
    results: list[SearchResult]
    facts: list[SearchResult]
    procedures: list[SearchResult]
    preferences: list[SearchResult]
    graph_context: list[SearchResult]


class RetrievalOrchestrator:
    """Composes specialized retrievers into one ranked memory view."""

    ALLOWED_STATES = {"validated", "hypothesized", "consolidated"}

    def __init__(self, storage: StorageManager, search_pipeline: SearchPipeline):
        self.storage = storage
        self.search_pipeline = search_pipeline
        self.specialized_storage = SpecializedStorageSurfaces(storage)

    def retrieve(self, query: SearchQuery) -> RetrievalBundle:
        base_results = self.search_pipeline.search_with_expansion(query)
        vector_results = self._vector_results(query)
        merged: dict[str, SearchResult] = {result.memory.id: result for result in base_results}
        for result in vector_results:
            existing = merged.get(result.memory.id)
            if existing is None or result.score > existing.score:
                merged[result.memory.id] = result
            elif "vector_store_match" not in existing.reasons:
                existing.reasons.append("vector_store_match")
        filtered = [result for result in merged.values() if self._state_for(result) in self.ALLOWED_STATES]
        facts = [result for result in filtered if result.memory.type in {"semantic", "episodic", "working"}]
        procedures = [result for result in filtered if result.memory.type == "procedural"]
        preferences = [result for result in filtered if self._looks_like_preference(result)]
        graph_context = [result for result in filtered if result.retrieval_stage != "lexical"]
        ranked = sorted(filtered, key=self._sort_key, reverse=True)
        return RetrievalBundle(
            results=ranked,
            facts=facts,
            procedures=procedures,
            preferences=preferences,
            graph_context=graph_context,
        )

    def _vector_results(self, query: SearchQuery) -> list[SearchResult]:
        if not query.semantic:
            return []
        rows = self.specialized_storage.search_vector_store(
            query=query.query,
            scope_type=query.scope_type,
            scope_id=query.scope_id,
            include_global=query.include_global,
            limit=query.limit,
        )
        
        # Use SearchPipeline to materialize and GOVERN the vector results
        # This ensures v9 scoring and v10 governance are applied consistently
        return self.search_pipeline._materialize_results(
            rows, # raw_candidates
            min_score=query.min_score,
            limit=query.limit,
            query_text=query.query,
            query_obj=query
        )

    def _state_for(self, result: SearchResult) -> str:
        return getattr(result.memory, "memory_state", None) or result.admission_state

    def _looks_like_preference(self, result: SearchResult) -> bool:
        content = result.memory.content.lower()
        return any(token in content for token in ("prefer", "likes", "dislikes", "favorite", "thích"))

    def _sort_key(self, result: SearchResult) -> tuple[float, float, int]:
        profile = result.memory.metadata.get("score_profile", {}) if isinstance(result.memory.metadata, dict) else {}
        type_bonus = 0.08 if result.memory.type == "procedural" else 0.04 if result.memory.type == "semantic" else 0.0
        graph_penalty = -0.05 if result.retrieval_stage != "lexical" else 0.0
        profile_bonus = (
            (float(profile.get("directness", 0.0) or 0.0) * 0.06)
            + (float(profile.get("source_reliability", 0.0) or 0.0) * 0.05)
            - (float(profile.get("conflict_pressure", 0.0) or 0.0) * 0.08)
        )
        return (
            round(result.score + type_bonus + graph_penalty + profile_bonus, 6),
            float(result.memory.activation_score or 0.0),
            1 if self._looks_like_preference(result) else 0,
        )
