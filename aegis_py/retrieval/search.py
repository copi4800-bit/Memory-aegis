from typing import List, Any, Dict
from .contract import score_link_expansion
from .models import SearchQuery, SearchResult
from ..storage.models import RETRIEVABLE_MEMORY_STATUS_SQL
from .engine import run_scoped_search
from .oracle import OracleBeast
from ..memory.core import MemoryManager
from ..storage.manager import StorageManager

# Phase 2: Aegis v9 Core Integration
from ..v9.adapter import map_to_v9_record
from ..v9.scorer import ResidualScorer
from ..v9.query_signals import build_v9_query_signals

# Phase 3: Aegis v10 Governance Integration
from ..v10.engine import GovernanceEngineV10
from ..v10.truth_registry import TruthRegistryV10

class SearchPipeline:
    """Orchestrates FTS5 search -> Normalization -> Reranking -> Governance -> Explanation."""

    STAGE_BUDGETS = {
        "lexical": 5,
        "semantic_recall": 3,
        "link_expansion": 2,
        "multi_hop_link_expansion": 1,
        "entity_expansion": 2,
        "subject_expansion": 2,
    }
    
    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.manager = MemoryManager(storage)
        self.oracle = OracleBeast(storage)
        self.v9_scorer = ResidualScorer()
        self.v10_engine = GovernanceEngineV10(storage, scorer=self.v9_scorer)
        self.v10_registry = TruthRegistryV10(storage)

    def search(self, query: SearchQuery) -> List[SearchResult]:
        # 1. Recall Candidates (v8 logic)
        canonical = run_scoped_search(
            self.storage,
            query.query,
            scope_type=query.scope_type,
            scope_id=query.scope_id,
            limit=query.limit,
            include_global=query.include_global,
            fallback_to_or=True,
        )
        
        # 2. Find suppressed for Why-not
        sanitized_query = query.query.replace('"', '""')
        sanitized_query = f'"{sanitized_query}"'
        
        suppressed_raw = self.storage.fetch_all(
            f"""
            SELECT m.id, m.content, m.status FROM memories m
            JOIN memories_fts fts ON m.rowid = fts.rowid
            WHERE memories_fts MATCH ?
              AND m.status IN ('superseded', 'archived') 
              AND m.scope_type = ? AND m.scope_id = ?
            LIMIT 3
            """,
            (sanitized_query, query.scope_type, query.scope_id)
        )

        # 3. Materialize & Governance Selection
        results = self._materialize_results(
            canonical, 
            min_score=query.min_score, 
            limit=query.limit,
            query_text=query.query,
            query_obj=query
        )
        
        # 4. Attach suppressed Why-not
        if results and suppressed_raw:
            for row in suppressed_raw:
                reason = "Đã bị thay thế bởi bản ghi mới hơn (Superseded)" if row["status"] == "superseded" else "Đã được lưu trữ (Archived)"
                if not any(s["id"] == row["id"] for s in results[0].suppressed_candidates):
                    results[0].suppressed_candidates.append({
                        "id": row["id"],
                        "content": row["content"][:50],
                        "reason": reason
                    })

        return results

    def _materialize_results(self, canonical, *, min_score: float, limit: int = 10, query_text: str = "", query_obj: SearchQuery | None = None) -> List[SearchResult]:
        raw_candidates: list[SearchResult] = []
        suppressed: list[dict[str, Any]] = []

        for result in canonical:
            # Handle both object-like (CanonicalSearchResult) and dict-like results
            res_id = getattr(result, "id", None) or result.get("id")
            res_score = getattr(result, "score", None) or result.get("score") or result.get("vector_similarity", 0.0)
            
            if not res_id:
                # Some vector search results use memory_id instead of id
                res_id = result.get("memory_id")
                
            if not res_id:
                continue
                
            memory = self.storage.get_memory(res_id)
            if memory is None:
                continue

            # Why-not: Superseded (Primary filter)
            if memory.status == "superseded":
                suppressed.append({
                    "id": res_id,
                    "content": memory.content[:50],
                    "reason": "Đã bị thay thế bởi bản ghi mới hơn (Superseded)"
                })
                continue

            # --- Aegis v10 Governed Judgment Engine ---
            context = {"intent": getattr(query_obj, "intent", "normal_recall") if query_obj else "normal_recall"}
            
            # For v9 query signals, we need an object-like result
            # If it's a dict, we might need to wrap it or adapt build_v9_query_signals
            query_signals = build_v9_query_signals(result, query_text, self.storage, context=context)
            v9_record = map_to_v9_record(memory, self.storage)
            
            # v10 Decide
            decision = self.v10_engine.govern(v9_record, query_signals, intent=context["intent"])
            v9_trace = decision.score_trace
            v9_final_score = v9_trace.factors.get("final_score", 0.0)
            # --- End v10 Engine ---

            sr = SearchResult(
                memory=memory,
                score=float(res_score),
                reasons=getattr(result, "reasons", []) if not isinstance(result, dict) else result.get("reasons", []),
                source_kind=getattr(result, "source_kind", memory.source_kind),
                source_ref=getattr(result, "source_ref", memory.source_ref),
                scope_type=getattr(result, "scope_type", memory.scope_type),
                scope_id=getattr(result, "scope_id", memory.scope_id),
                conflict_status=getattr(result, "conflict_status", "none") if not isinstance(result, dict) else result.get("conflict_status", "none"),
                admission_state=getattr(result, "admission_state", "validated") if not isinstance(result, dict) else result.get("admission_state", "validated"),
                retrieval_stage=getattr(result, "retrieval_stage", "lexical") if not isinstance(result, dict) else result.get("retrieval_stage", "lexical"),
                relation_via_link_metadata=getattr(result, "relation_via_link_metadata", None),
                relation_via_subject=getattr(result, "relation_via_subject", None) if not isinstance(result, dict) else result.get("relation_via_subject"),
                relation_via_link_type=getattr(result, "relation_via_link_type", None),
                relation_via_memory_id=getattr(result, "relation_via_memory_id", None),
                relation_via_hops=getattr(result, "relation_via_hops", None),
                v8_core_signals=getattr(result, "v8_core_signals", None),
            )
            # Inject Audit Metadata
            setattr(sr, "v9_trace", v9_trace)
            setattr(sr, "v9_score", v9_final_score)
            setattr(sr, "v10_decision", decision)
            raw_candidates.append(sr)

        # Final Slot Resolution
        self.v10_registry.resolve_slot_ownership(raw_candidates, intent=getattr(query_obj, "intent", "normal_recall") if query_obj else "normal_recall")

        # --- v10 Final Admissibility Filtering ---
        final_results: List[SearchResult] = []
        for sr in raw_candidates:
            dec = sr.v10_decision
            if dec.admissible:
                final_results.append(sr)
            else:
                suppressed.append({
                    "id": sr.memory.id,
                    "content": sr.memory.content[:50],
                    "reason": f"Chặn bởi Policy: {', '.join(dec.policy_trace or dec.decision_reason)}"
                })

        # Selection and Sorting
        mode = getattr(query_obj, "scoring_mode", "v10_primary") if query_obj else "v10_primary"
        if mode in ["v10_primary", "v9_primary"]:
            final_results.sort(key=lambda x: getattr(x, "v9_score", 0.0), reverse=True)
            final_results = final_results[:limit]
        else:
            final_results = final_results[:limit]

        if final_results and suppressed:
            final_results[0].suppressed_candidates = suppressed[:3]

        return final_results

    def track_access(self, result: SearchResult):
        self.storage.reinforce_memory(result.memory.id)

    def search_with_expansion(self, query: SearchQuery) -> List[SearchResult]:
        canonical = run_scoped_search(
            self.storage,
            query.query,
            scope_type=query.scope_type,
            scope_id=query.scope_id,
            limit=query.limit,
            include_global=query.include_global,
        )
        return self._materialize_results(canonical, min_score=query.min_score, query_text=query.query, query_obj=query)
