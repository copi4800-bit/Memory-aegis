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

class SearchPipeline:
    """Orchestrates FTS5 search -> Normalization -> Reranking -> Explanation."""

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

    def search(self, query: SearchQuery) -> List[SearchResult]:
        # 1. Recall Candidates (v8 logic)
        canonical = run_scoped_search(
            self.storage,
            query.query,
            scope_type=query.scope_type,
            scope_id=query.scope_id,
            limit=query.limit,
            include_global=query.include_global,
            fallback_to_or=query.fallback_to_or,
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

        # 3. Materialize & Rerank via v9 Residual Judgment Engine
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
        results: list[SearchResult] = []
        suppressed: list[dict[str, Any]] = []

        for result in canonical:
            memory = self.storage.get_memory(result.id)
            if memory is None:
                continue

            # Why-not: Superseded
            if memory.status == "superseded":
                suppressed.append({
                    "id": result.id,
                    "content": memory.content[:50],
                    "reason": "Đã bị thay thế bởi bản ghi mới hơn (Superseded)"
                })
                continue

            # --- Aegis v9 Residual Judgment Engine Ranking ---
            # We map current context to query signals for v9 using the dedicated builder
            context = {"intent": getattr(query_obj, "intent", "normal_recall") if query_obj else "normal_recall"}
            query_signals = build_v9_query_signals(result, query_text, self.storage, context=context)
            
            v9_record = map_to_v9_record(memory, self.storage)
            v9_trace = self.v9_scorer.score(v9_record, query_signals, intent=context["intent"])
            v9_final_score = v9_trace.factors["final_score"]
            
            # --- End v9 Ranking ---

            # Filter by min_score (v9 is now the primary gatekeeper)
            if v9_final_score < min_score:
                suppressed.append({
                    "id": result.id,
                    "content": memory.content[:50],
                    "reason": f"Độ khớp v9 quá thấp ({v9_final_score:.2f} < {min_score})"
                })
                continue
            
            if len(results) < limit * 2: # Keep a larger pool for final v9 sorting
                sr = SearchResult(
                    memory=memory,
                    score=result.score,
                    reasons=result.reasons,
                    source_kind=result.source_kind,
                    source_ref=result.source_ref,
                    scope_type=result.scope_type,
                    scope_id=result.scope_id,
                    conflict_status=result.conflict_status,
                    admission_state=getattr(result, "admission_state", "validated"),
                    retrieval_stage=result.retrieval_stage,
                    relation_via_link_metadata=getattr(result, "relation_via_link_metadata", None),
                    relation_via_subject=result.relation_via_subject,
                    relation_via_link_type=getattr(result, "relation_via_link_type", None),
                    relation_via_memory_id=getattr(result, "relation_via_memory_id", None),
                    relation_via_hops=getattr(result, "relation_via_hops", None),
                    v8_core_signals=getattr(result, "v8_core_signals", None),
                )
                # Inject v9 Data
                setattr(sr, "v9_trace", v9_trace)
                setattr(sr, "v9_score", v9_final_score)
                results.append(sr)
            else:
                suppressed.append({
                    "id": result.id,
                    "content": memory.content[:50],
                    "reason": "Bị loại bởi các kết quả có độ ưu tiên cao hơn"
                })

        # Final Rerank and Selection
        mode = getattr(query_obj, "scoring_mode", "v9_primary") if query_obj else "v9_primary"
        
        if mode == "v9_primary":
            results.sort(key=lambda x: getattr(x, "v9_score", 0.0), reverse=True)
            results = results[:limit]
        elif mode == "shadow_v9":
            # Keep v8 order but results contain v9 metadata
            results = results[:limit]
        else: # v8_primary
            results = results[:limit]

        if results and suppressed:
            results[0].suppressed_candidates = suppressed[:3]

        return results

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
        stage_counts = {"lexical": len(canonical)}
        
        if query.semantic and len(canonical) < query.limit:
            canonical = self._expand_semantic_oracle(
                canonical,
                query=query.query,
                scope_type=query.scope_type,
                scope_id=query.scope_id,
                limit=query.limit,
                stage_counts=stage_counts,
                model=query.semantic_model,
            )

        canonical = self._expand_related_context(
            canonical,
            scope_type=query.scope_type,
            scope_id=query.scope_id,
            limit=query.limit,
            stage_counts=stage_counts,
        )
        return self._materialize_results(canonical, min_score=query.min_score, query_text=query.query, query_obj=query)

    def _expand_semantic_oracle(self, canonical, *, query: str, scope_type: str, scope_id: str, limit: int, stage_counts: dict[str, int], model: str | None = None):
        if len(canonical) >= limit: return canonical
        expansion_terms = self.oracle.expand_query(query, model=model)
        if not expansion_terms: return canonical
        seen_ids = {result.id for result in canonical}
        expanded = list(canonical)
        for term in expansion_terms:
            if stage_counts.get("semantic_recall", 0) >= self.STAGE_BUDGETS["semantic_recall"]: break
            results = run_scoped_search(self.storage, term, scope_type=scope_type, scope_id=scope_id, limit=3, include_global=True)
            for res in results:
                if res.id in seen_ids: continue
                res.retrieval_stage = "semantic_recall"
                res.reasons.append(f"semantic_oracle_expansion:{term}")
                res.score = round(res.score * 0.85, 6)
                expanded.append(res)
                seen_ids.add(res.id)
                stage_counts["semantic_recall"] = stage_counts.get("semantic_recall", 0) + 1
                if len(expanded) >= limit: break
        return expanded

    def _expand_related_context(self, canonical, *, scope_type: str, scope_id: str, limit: int, stage_counts: dict[str, int]):
        if len(canonical) >= limit: return canonical[:limit]
        seen_ids = {result.id for result in canonical}
        expanded = self._expand_explicit_links(list(canonical), seen_ids=seen_ids, scope_type=scope_type, scope_id=scope_id, limit=limit, hop_depth=1, stage_counts=stage_counts)
        if len(expanded) >= limit: return expanded[:limit]
        expanded = self._expand_explicit_links(expanded, seen_ids=seen_ids, scope_type=scope_type, scope_id=scope_id, limit=limit, hop_depth=2, seed_stage="link_expansion", stage_counts=stage_counts)
        if len(expanded) >= limit: return expanded[:limit]
        expanded = self._expand_entity_neighbors(expanded, seen_ids=seen_ids, scope_type=scope_type, scope_id=scope_id, limit=limit, stage_counts=stage_counts)
        if len(expanded) >= limit: return expanded[:limit]
        subjects = [result.subject for result in canonical if getattr(result, "retrieval_stage", "lexical") == "lexical" if result.subject and result.subject != "general.untagged"]
        if not subjects: return expanded
        return self._expand_subject_neighbors(expanded, seen_ids=seen_ids, subjects=subjects, scope_type=scope_type, scope_id=scope_id, limit=limit, stage_counts=stage_counts)

    def _expand_explicit_links(self, canonical, *, seen_ids: set[str], scope_type: str, scope_id: str, limit: int, hop_depth: int, seed_stage: str = "lexical", stage_counts: dict[str, int]):
        if not canonical: return canonical
        seed_ids = [result.id for result in canonical if getattr(result, "retrieval_stage", "lexical") == seed_stage]
        if not seed_ids: return canonical
        neighbors = self.storage.list_link_expansions(seed_ids=seed_ids, scope_type=scope_type, scope_id=scope_id, limit=max(limit * 2, 10))
        expanded = list(canonical)
        seed_lookup = {result.id: result for result in canonical if getattr(result, "retrieval_stage", "lexical") == seed_stage}
        for row in neighbors:
            if row["id"] in seen_ids: continue
            source_seed = row["source_id"] if row["source_id"] in seed_lookup else row["target_id"]
            if source_seed not in seed_lookup: continue
            seed = seed_lookup[source_seed]
            retrieval_stage = "link_expansion" if hop_depth == 1 else "multi_hop_link_expansion"
            if stage_counts.get(retrieval_stage, 0) >= self.STAGE_BUDGETS[retrieval_stage]: continue
            expanded.append(type(canonical[0])(id=row["id"], type=row["type"], content=row["content"], summary=row["summary"], subject=row["subject"], score=score_link_expansion(link_weight=float(row["weight"]), hop_depth=hop_depth, link_type=row["link_type"], memory_type=row["type"]), reasons=["relationship_expansion", "explicit_link_neighbor", f"link_hops:{hop_depth}", f"link_type:{row['link_type']}", "lexical_seed_required", "scope_type_match", "scope_exact_match", "link_score_reranked"], source_kind=row["source_kind"], source_ref=row["source_ref"], scope_type=row["scope_type"], scope_id=row["scope_id"], conflict_status="none", retrieval_stage=retrieval_stage, relation_via_subject=seed.subject, relation_via_link_type=row["link_type"], relation_via_memory_id=source_seed, relation_via_link_metadata={"weight": row["weight"]}, relation_via_hops=hop_depth))
            seen_ids.add(row["id"])
            stage_counts[retrieval_stage] = stage_counts.get(retrieval_stage, 0) + 1
            if len(expanded) >= limit: break
        return expanded

    def _expand_entity_neighbors(self, expanded, *, seen_ids: set[str], scope_type: str, scope_id: str, limit: int, stage_counts: dict[str, int]):
        canonical = list(expanded)
        for seed in canonical:
            if getattr(seed, "retrieval_stage", "lexical") != "lexical": continue
            memory = self.storage.get_memory(seed.id)
            if memory is None: continue
            entities = (memory.metadata or {}).get("entities") or []
            if not entities: continue
            neighbors = self.storage.list_entity_peers(memory_id=seed.id, scope_type=scope_type, scope_id=scope_id, entities=entities, limit=max(limit * 2, 10))
            for row in neighbors:
                if row["id"] in seen_ids: continue
                if stage_counts.get("entity_expansion", 0) >= self.STAGE_BUDGETS["entity_expansion"]: return expanded[:limit]
                overlap = row.get("entity_overlap") or []
                expanded.append(type(canonical[0])(id=row["id"], type=row["type"], content=row["content"], summary=row["summary"], subject=row["subject"], score=round(min(0.22 + (0.04 * len(overlap)), 0.4), 6), reasons=["relationship_expansion", "entity_expansion", f"entity_overlap:{','.join(overlap)}", "lexical_seed_required", "scope_type_match", "scope_exact_match"], source_kind=row["source_kind"], source_ref=row["source_ref"], scope_type=row["scope_type"], scope_id=row["scope_id"], conflict_status="none", retrieval_stage="entity_expansion", relation_via_subject=seed.subject, relation_via_memory_id=seed.id, relation_via_link_metadata={"entities": overlap}))
                seen_ids.add(row["id"])
                stage_counts["entity_expansion"] = stage_counts.get("entity_expansion", 0) + 1
                if len(expanded) >= limit: return expanded[:limit]
        return expanded

    def _expand_subject_neighbors(self, expanded, *, seen_ids: set[str], subjects: list[str], scope_type: str, scope_id: str, limit: int, stage_counts: dict[str, int]):
        neighbors = self.storage.fetch_all(f"SELECT m.*, CASE WHEN EXISTS (SELECT 1 FROM conflicts WHERE status = 'open' AND (memory_a_id = m.id OR memory_b_id = m.id)) THEN 'open' ELSE 'none' END AS conflict_status FROM memories m WHERE m.status IN ({RETRIEVABLE_MEMORY_STATUS_SQL}) AND m.scope_type = ? AND m.scope_id = ? AND m.subject IN ({','.join('?' for _ in subjects)}) ORDER BY m.activation_score DESC, m.updated_at DESC LIMIT ?", (scope_type, scope_id, *subjects, max(limit * 2, 10)))
        seed_subjects = set(subjects)
        for row in neighbors:
            if row["id"] in seen_ids: continue
            if stage_counts.get("subject_expansion", 0) >= self.STAGE_BUDGETS["subject_expansion"]: break
            subject = row["subject"]
            reasons = ["relationship_expansion", f"subject_neighbor:{subject}", "lexical_seed_required", "scope_type_match", "scope_exact_match"]
            if row["type"] == "procedural": reasons.append("procedural_bonus")
            if float(row["activation_score"]) > 1.0: reasons.append("activation_boost")
            if row["type"] == "semantic": reasons.append("semantic_fact_match")
            if row["conflict_status"] != "none": reasons.append("conflict_visible")
            expanded.append(type(canonical[0])(id=row["id"], type=row["type"], content=row["content"], summary=row["summary"], subject=subject, score=round(float(row["activation_score"]) * 0.45, 6), reasons=reasons, source_kind=row["source_kind"], source_ref=row["source_ref"], scope_type=row["scope_type"], scope_id=row["scope_id"], conflict_status=row["conflict_status"], retrieval_stage="subject_expansion", relation_via_subject=subject if subject in seed_subjects else None))
            seen_ids.add(row["id"])
            stage_counts["subject_expansion"] = stage_counts.get("subject_expansion", 0) + 1
            if len(expanded) >= limit: break
        return expanded[:limit]
