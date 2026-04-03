from typing import List, Any, Dict
from .contract import score_link_expansion
from .models import SearchQuery, SearchResult
from ..storage.models import RETRIEVABLE_MEMORY_STATUS_SQL
from .engine import run_scoped_search
from .oracle import OracleBeast
from ..memory.core import MemoryManager
from ..memory.weaver import WeaverBeast
from ..storage.manager import StorageManager
from ..hygiene.librarian import LibrarianBeast
from ..hygiene.nutcracker import NutcrackerBeast
from ..preferences.manager import PreferenceManager

# Phase 2: Aegis v10 Core Integration
from ..v10_scoring.adapter import map_to_v10_record
from ..v10_scoring.scorer import ResidualScorer
from ..v10_scoring.query_signals import build_v10_query_signals

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
        self.weaver = WeaverBeast(storage)
        self.librarian = LibrarianBeast(storage)
        self.nutcracker = NutcrackerBeast(storage)
        self.preference_manager = PreferenceManager(storage)
        self.v10_scorer = ResidualScorer()
        self.v10_engine = GovernanceEngineV10(storage, scorer=self.v10_scorer)
        self.v10_registry = TruthRegistryV10(storage)

    def search(self, query: SearchQuery) -> List[SearchResult]:
        # 1. Recall Candidates (v10 logic)
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
            
            # For v10 query signals, we need an object-like result
            # If it's a dict, we might need to wrap it or adapt build_v10_query_signals
            query_signals = build_v10_query_signals(result, query_text, self.storage, context=context)
            v10_record = map_to_v10_record(memory, self.storage)
            
            # v10 Decide
            decision = self.v10_engine.govern(v10_record, query_signals, intent=context["intent"])
            v10_trace = decision.score_trace
            v10_final_score = v10_trace.factors.get("final_score", 0.0)
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
                v10_core_signals=getattr(result, "v10_core_signals", None),
            )
            # Inject Audit Metadata
            setattr(sr, "v10_trace", v10_trace)
            setattr(sr, "v10_score", v10_final_score)
            setattr(sr, "v10_decision", decision)
            raw_candidates.append(sr)

        # Final Slot Resolution
        self.v10_registry.resolve_slot_ownership(raw_candidates, intent=getattr(query_obj, "intent", "normal_recall") if query_obj else "normal_recall")
        self._apply_tyrannosaurus_dominance(raw_candidates)
        self._apply_prehistoric_judged_recall_pressure(raw_candidates, query_obj=query_obj)

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
        if mode in ["v10_primary", "v10_primary"]:
            final_results.sort(key=lambda x: getattr(x, "v10_score", 0.0), reverse=True)
            final_results = final_results[:limit]
        else:
            final_results = final_results[:limit]

        if final_results and suppressed:
            final_results[0].suppressed_candidates = suppressed[:3]

        return final_results

    def _apply_prehistoric_judged_recall_pressure(self, raw_candidates: list[SearchResult], *, query_obj: SearchQuery | None = None) -> None:
        scope_context = self._build_prehistoric_scope_context(query_obj)
        topology_cache: dict[str, dict[str, Any]] = {}
        subject_locality_cache: dict[str, dict[str, Any]] = {}
        for result in raw_candidates:
            decision = getattr(result, "v10_decision", None)
            trace = getattr(result, "v10_trace", None)
            if decision is None or trace is None or not decision.admissible:
                continue

            reasons = list(getattr(result, "reasons", []) or [])
            pressure = 0.0

            utah_ratio = self._extract_reason_float(reasons, "utahraptor_lexical_pursuit:")
            if utah_ratio >= 0.85:
                pressure += 0.03
                trace.factors["utahraptor_judged_pressure"] = round(0.03, 6)
                decision.decision_reason.append("utahraptor_judged_pressure")
            elif utah_ratio >= 0.55:
                pressure += 0.015
                trace.factors["utahraptor_judged_pressure"] = round(0.015, 6)
                decision.decision_reason.append("utahraptor_judged_pressure")

            basilosaurus_terms = self._extract_reason_terms(reasons, "basilosaurus_semantic_echo:")
            if len(basilosaurus_terms) >= 3:
                pressure += 0.025
                trace.factors["basilosaurus_judged_pressure"] = round(0.025, 6)
                decision.decision_reason.append("basilosaurus_judged_pressure")
            elif len(basilosaurus_terms) >= 1:
                pressure += 0.012
                trace.factors["basilosaurus_judged_pressure"] = round(0.012, 6)
                decision.decision_reason.append("basilosaurus_judged_pressure")

            if result.retrieval_stage == "link_expansion" and result.relation_via_link_type in {"supports", "procedural_supports_semantic"}:
                pterodactyl_boost = 0.02 if (result.relation_via_hops or 0) <= 1 else 0.01
                pressure += pterodactyl_boost
                trace.factors["pterodactyl_judged_pressure"] = round(pterodactyl_boost, 6)
                decision.decision_reason.append("pterodactyl_judged_pressure")

            if decision.policy_trace and decision.truth_role.value == "winner":
                pressure += 0.01
                trace.factors["paraceratherium_judged_pressure"] = round(0.01, 6)
                decision.decision_reason.append("paraceratherium_judged_pressure")

            if (
                query_obj is not None
                and getattr(query_obj, "scope_type", None)
                and getattr(query_obj, "scope_id", None)
                and result.memory.scope_type == getattr(query_obj, "scope_type", None)
                and result.memory.scope_id == getattr(query_obj, "scope_id", None)
            ):
                pressure += 0.008
                trace.factors["argentinosaurus_judged_pressure"] = round(0.008, 6)
                decision.decision_reason.append("argentinosaurus_judged_pressure")

            glyptodon_shell = float((result.memory.metadata or {}).get("glyptodon_consolidation_shell", 0.0) or 0.0)
            if glyptodon_shell >= 0.78:
                pressure += 0.018
                trace.factors["glyptodon_judged_pressure"] = round(0.018, 6)
                decision.decision_reason.append("glyptodon_judged_pressure")
            elif glyptodon_shell >= 0.55:
                pressure += 0.009
                trace.factors["glyptodon_judged_pressure"] = round(0.009, 6)
                decision.decision_reason.append("glyptodon_judged_pressure")

            topology = topology_cache.get(result.memory.id)
            if topology is None:
                topology = self.weaver.build_topology_report(result.memory.id)
                topology_cache[result.memory.id] = topology
            megarachne_strength = float(topology.get("megarachne_topology_strength", 0.0) or 0.0)
            if megarachne_strength >= 0.6:
                pressure += 0.014
                trace.factors["megarachne_judged_pressure"] = round(0.014, 6)
                decision.decision_reason.append("megarachne_judged_pressure")

            locality_key = f"{result.memory.scope_type}:{result.memory.scope_id}:{result.memory.subject or ''}"
            subject_locality = subject_locality_cache.get(locality_key)
            if subject_locality is None:
                subject_locality = self.librarian.build_subject_locality_report(
                    result.memory.scope_type,
                    result.memory.scope_id,
                    result.memory.subject,
                )
                subject_locality_cache[locality_key] = subject_locality
            titanoboa_locality = float(subject_locality.get("titanoboa_subject_locality", 0.0) or 0.0)
            if titanoboa_locality >= 0.55:
                pressure += 0.012
                trace.factors["titanoboa_judged_pressure"] = round(0.012, 6)
                decision.decision_reason.append("titanoboa_judged_pressure")

            dire_wolf_identity = float(scope_context.get("dire_wolf_identity_persistence", 0.0) or 0.0)
            if (
                dire_wolf_identity >= 0.72
                and query_obj is not None
                and result.memory.scope_type == getattr(query_obj, "scope_type", None)
                and result.memory.scope_id == getattr(query_obj, "scope_id", None)
            ):
                pressure += 0.01
                trace.factors["dire_wolf_judged_pressure"] = round(0.01, 6)
                decision.decision_reason.append("dire_wolf_judged_pressure")

            deinosuchus_pressure = float(scope_context.get("deinosuchus_compaction_pressure", 0.0) or 0.0)
            if deinosuchus_pressure >= 0.35:
                activation = float(result.memory.activation_score or 0.0)
                if activation >= 0.72:
                    pressure += 0.01
                    trace.factors["deinosuchus_judged_pressure"] = round(0.01, 6)
                    decision.decision_reason.append("deinosuchus_judged_pressure")
                elif activation < 0.35:
                    pressure -= 0.01
                    trace.factors["deinosuchus_judged_pressure"] = round(-0.01, 6)
                    decision.decision_reason.append("deinosuchus_judged_pressure")

            if pressure > 0.0:
                result.v10_score = round(float(getattr(result, "v10_score", 0.0) or 0.0) + pressure, 6)
                trace.factors["prehistoric_judged_recall_pressure"] = round(pressure, 6)
                trace.factors["final_score"] = round(result.v10_score, 6)
            elif pressure < 0.0:
                result.v10_score = round(float(getattr(result, "v10_score", 0.0) or 0.0) + pressure, 6)
                trace.factors["prehistoric_judged_recall_pressure"] = round(pressure, 6)
                trace.factors["final_score"] = round(result.v10_score, 6)

    def _build_prehistoric_scope_context(self, query_obj: SearchQuery | None) -> dict[str, Any]:
        if query_obj is None:
            return {}
        scope_type = getattr(query_obj, "scope_type", None)
        scope_id = getattr(query_obj, "scope_id", None)
        if not scope_type or not scope_id:
            return {}
        identity = self.preference_manager.build_identity_report(scope_id, scope_type)
        compaction = self.nutcracker.check_scope_health(scope_type, scope_id)
        return {
            "dire_wolf_identity_persistence": identity.get("dire_wolf_identity_persistence", 0.0),
            "deinosuchus_compaction_pressure": compaction.get("deinosuchus_compaction_pressure", 0.0),
        }

    def _extract_reason_float(self, reasons: list[str], prefix: str) -> float:
        for reason in reasons:
            if reason.startswith(prefix):
                try:
                    return float(reason.split(":", 1)[1])
                except (TypeError, ValueError):
                    return 0.0
        return 0.0

    def _extract_reason_terms(self, reasons: list[str], prefix: str) -> list[str]:
        for reason in reasons:
            if reason.startswith(prefix):
                return [item for item in reason.split(":", 1)[1].split(",") if item]
        return []

    def _apply_tyrannosaurus_dominance(self, raw_candidates: list[SearchResult]) -> None:
        groups: dict[str, list[SearchResult]] = {}
        for result in raw_candidates:
            group_key = result.memory.subject or result.memory.id
            groups.setdefault(group_key, []).append(result)

        for group_results in groups.values():
            if len(group_results) < 2:
                continue
            ordered = sorted(group_results, key=lambda item: getattr(item, "v10_score", 0.0), reverse=True)
            top = ordered[0]
            runner_up = ordered[1]
            top_decision = getattr(top, "v10_decision", None)
            if top_decision is None or top_decision.truth_role.value != "winner":
                continue

            base_top_score = float(getattr(top, "v10_score", 0.0) or 0.0)
            runner_up_score = float(getattr(runner_up, "v10_score", 0.0) or 0.0)
            margin = max(0.0, base_top_score - runner_up_score)
            dominance_boost = min(0.18, 0.05 + margin * 0.35)
            top.v10_score = round(base_top_score + dominance_boost, 6)
            if top.v10_trace is not None:
                top.v10_trace.factors["tyrannosaurus_margin"] = round(margin, 6)
                top.v10_trace.factors["tyrannosaurus_dominance_boost"] = round(dominance_boost, 6)
                top.v10_trace.factors["final_score"] = round(top.v10_score, 6)
            top.v10_decision.decision_reason.append("trex_dominance_boost")

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
