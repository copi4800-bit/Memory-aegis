from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any

from .contract import blend_retrieval_score, build_reason_tags, score_link_expansion, normalize_fts_rank
from .compressed_prefilter import CompressedCandidatePrefilter, CompressedSignature
from .compressed_tier import build_compressed_tier_payload
from .hybrid_governance import (
    classify_query_route,
    compute_governance_alignment,
    fuse_hybrid_signals,
    hybrid_reason_tags,
)
from .oracle import OracleBeast
from .v10_dynamics import compute_v10_core_signals, dynamic_reason_tags, dynamic_score_bonus
from ..storage.models import RETRIEVABLE_MEMORY_STATUS_SQL


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_fts_query(query: str) -> str:
    chars_to_strip = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    sanitized = query.translate(str.maketrans({char: " " for char in chars_to_strip}))
    return " ".join(sanitized.split())


@dataclass
class CanonicalSearchResult:
    id: str
    type: str
    content: str
    summary: str | None
    subject: str | None
    score: float
    reasons: list[str]
    source_kind: str
    source_ref: str | None
    scope_type: str
    scope_id: str
    conflict_status: str
    admission_state: str = "validated"
    score_profile: dict[str, float] | None = None
    retrieval_stage: str = "lexical"
    relation_via_subject: str | None = None
    relation_via_link_type: str | None = None
    relation_via_memory_id: str | None = None
    relation_via_link_metadata: dict[str, object] | None = None
    relation_via_hops: int | None = None
    v10_core_signals: dict[str, Any] | None = None
    hybrid_fusion: dict[str, Any] | None = None


def _lexical_tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if token]


def _utahraptor_lexical_pursuit(*, query: str, content: str | None, summary: str | None, subject: str | None) -> tuple[float, list[str]]:
    haystack = " ".join(filter(None, [content, summary, subject])).lower()
    query_tokens = [token for token in _lexical_tokens(query) if len(token) > 1]
    if not query_tokens:
        return 0.0, []
    matched = [token for token in query_tokens if token in haystack]
    ratio = len(set(matched)) / len(set(query_tokens))
    if ratio <= 0.0:
        return 0.0, []
    boost = round(min(0.16, 0.04 + ratio * 0.12), 6)
    reasons = [f"utahraptor_lexical_pursuit:{round(ratio, 3)}"]
    return boost, reasons


def _basilosaurus_semantic_echo(*, query: str, content: str | None, summary: str | None, subject: str | None, oracle: OracleBeast) -> tuple[float, list[str]]:
    haystack = " ".join(filter(None, [content, summary, subject])).lower()
    expansions = oracle.expand_query(query)
    matched_expansions = [item for item in expansions if item and item.lower() in haystack]
    if not matched_expansions:
        return 0.0, []
    density = len(set(matched_expansions)) / max(1, len(set(expansions)))
    boost = round(min(0.14, 0.05 + density * 0.18), 6)
    reasons = [f"basilosaurus_semantic_echo:{','.join(matched_expansions[:3])}"]
    return boost, reasons


def _merge_result(results_by_id: dict[str, CanonicalSearchResult], candidate: CanonicalSearchResult) -> None:
    existing = results_by_id.get(candidate.id)
    if existing is None:
        results_by_id[candidate.id] = candidate
        return
    if candidate.score > existing.score:
        winner, loser = candidate, existing
    else:
        winner, loser = existing, candidate
    merged_reasons = list(dict.fromkeys(winner.reasons + loser.reasons))
    winner.reasons = merged_reasons
    stage_priority = {
        "lexical": 4,
        "semantic_recall": 3,
        "link_expansion": 2,
        "compressed_prefilter": 1,
    }
    winner_stage_priority = stage_priority.get(winner.retrieval_stage, 0)
    loser_stage_priority = stage_priority.get(loser.retrieval_stage, 0)
    if loser_stage_priority > winner_stage_priority:
        winner.retrieval_stage = loser.retrieval_stage
    results_by_id[candidate.id] = winner


def _execute_scored_rows(
    db: Any,
    *,
    fts_query: str,
    where_sql: str,
    params: list[Any],
    limit: int,
) -> list[dict[str, Any]]:
    sql = f"""
        SELECT
            m.*,
            bm25(memories_fts) AS lexical_score,
            CASE
                WHEN EXISTS (
                    SELECT 1 FROM conflicts c
                    WHERE c.status = 'open'
                      AND (c.memory_a_id = m.id OR c.memory_b_id = m.id)
                ) THEN 'open'
                ELSE 'none'
            END AS conflict_status
        FROM memories_fts
        JOIN memories m ON m.rowid = memories_fts.rowid
        WHERE {where_sql}
        ORDER BY lexical_score ASC, m.activation_score DESC, m.updated_at DESC
        LIMIT ?
    """
    return [dict(row) for row in db.fetch_all(sql, (*params, limit))]


def run_scoped_search(
    db: Any,
    query: str,
    *,
    scope_type: str | None,
    scope_id: str | None,
    limit: int,
    include_global: bool = False,
    fallback_to_or: bool = False,
) -> list[CanonicalSearchResult]:
    fts_query = _sanitize_fts_query(query)
    oracle = OracleBeast(db)
    route_profile = classify_query_route(query)
    prefilter = CompressedCandidatePrefilter()
    where_clauses = [f"m.status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})"]
    params: list[Any] = []

    if fts_query:
        where_clauses.insert(0, "memories_fts MATCH ?")
        params.append(fts_query)

    if scope_type and scope_id:
        if include_global:
            where_clauses.append("((m.scope_type = ? AND m.scope_id = ?) OR m.scope_type = 'global')")
            params.extend([scope_type, scope_id])
        else:
            where_clauses.append("m.scope_type = ?")
            where_clauses.append("m.scope_id = ?")
            params.extend([scope_type, scope_id])
    elif scope_type:
        where_clauses.append("m.scope_type = ?")
        params.append(scope_type)
    elif scope_id:
        where_clauses.append("m.scope_id = ?")
        params.append(scope_id)

    where_sql = " AND ".join(where_clauses)

    if not fts_query:
        sql = f"""
            SELECT
                m.*,
                0.0 AS lexical_score,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM conflicts c
                        WHERE c.status = 'open'
                          AND (c.memory_a_id = m.id OR c.memory_b_id = m.id)
                    ) THEN 'open'
                    ELSE 'none'
                END AS conflict_status
            FROM memories m
            WHERE {where_sql}
            ORDER BY m.activation_score DESC, m.updated_at DESC
            LIMIT ?
        """

    if fts_query:
        rows = _execute_scored_rows(db, fts_query=fts_query, where_sql=where_sql, params=params, limit=limit)
    else:
        rows = [dict(row) for row in db.fetch_all(sql, (*params, limit))]
    
    # Fallback for natural language: if AND search yielded nothing, try OR search
    if not rows and fallback_to_or and fts_query and " " in fts_query:
        or_query = " OR ".join(fts_query.split())
        or_params = [or_query if p == fts_query else p for p in params]
        rows = _execute_scored_rows(db, fts_query=or_query, where_sql=where_sql, params=or_params, limit=limit)

    semantic_rows: list[dict[str, Any]] = []
    if fts_query:
        semantic_expansions = [item for item in oracle.expand_query(query) if item and _sanitize_fts_query(item)]
        semantic_terms = list(dict.fromkeys(_sanitize_fts_query(item) for item in semantic_expansions if _sanitize_fts_query(item)))[:4]
        if semantic_terms:
            semantic_query = " OR ".join(semantic_terms)
            semantic_params = [semantic_query if p == fts_query else p for p in params]
            semantic_rows = _execute_scored_rows(
                db,
                fts_query=semantic_query,
                where_sql=where_sql,
                params=semantic_params,
                limit=max(3, min(limit, 6)),
            )

    lexical_ids = {row["id"] for row in rows}
    semantic_ids = {row["id"] for row in semantic_rows}

    compressed_rows: list[dict[str, Any]] = []
    if scope_type and scope_id:
        query_signature = prefilter.build_signature(
            query,
            semantic_terms=oracle.expand_query(query),
        )
        compressed_rows = _run_compressed_candidate_stage(
            db,
            query=query,
            query_signature=query_signature,
            scope_type=scope_type,
            scope_id=scope_id,
            limit=max(2, min(limit, 4)),
            exclude_ids=set(lexical_ids | semantic_ids),
            include_global=include_global,
            prefilter=prefilter,
        )

    results_by_id: dict[str, CanonicalSearchResult] = {}
    
    # --- BATCH PREFETCHING O(1) ---
    combined_rows = rows + [row for row in semantic_rows if row["id"] not in {item["id"] for item in rows}]
    combined_rows.extend([row for row in compressed_rows if row["id"] not in {item["id"] for item in combined_rows}])
    memory_ids = [str(dict(r)["id"]) for r in combined_rows]
    evidence_map = db.batch_count_evidence(memory_ids) if memory_ids and hasattr(db, 'batch_count_evidence') else {}
    support_map = db.batch_support_weight(memory_ids) if memory_ids and hasattr(db, 'batch_support_weight') else {}
    conflict_map = db.batch_conflict_weight(memory_ids) if memory_ids and hasattr(db, 'batch_conflict_weight') else {}
    compressed_ids = {row["id"] for row in compressed_rows}

    for row in combined_rows:
        payload = dict(row)
        metadata = _coerce_metadata(payload.get("metadata_json"))
        score_profile = metadata.get("score_profile", {}) if isinstance(metadata, dict) else {}
        admission_state = _derive_admission_state(payload["status"], metadata)
        if admission_state in {"draft", "invalidated"}:
            continue
            
        evidence_count = evidence_map.get(payload["id"], 0) if hasattr(db, 'batch_count_evidence') else _count_evidence_for_memory(db, payload["id"])
        support_weight = support_map.get(payload["id"], 0.0) if hasattr(db, 'batch_support_weight') else _support_weight_for_memory(db, payload["id"])
        cw_tuple = conflict_map.get(payload["id"], (0.0, False)) if hasattr(db, 'batch_conflict_weight') else _conflict_weight_for_memory(db, payload["id"])
        conflict_weight, direct_conflict_open = cw_tuple
        
        v10_core_signals = compute_v10_core_signals(
            row={
                "confidence": payload["confidence"],
                "activation_score": payload["activation_score"],
                "access_count": payload.get("access_count", 0),
                "metadata": metadata,
            },
            admission_state=admission_state,
            evidence_count=evidence_count,
            support_weight=support_weight,
            conflict_weight=conflict_weight,
            direct_conflict_open=direct_conflict_open,
        )
        normalized_rank = normalize_fts_rank(float(payload["lexical_score"]))
        score = blend_retrieval_score(float(payload["lexical_score"]), float(payload["activation_score"]), score_profile)
        utahraptor_boost, utahraptor_reasons = _utahraptor_lexical_pursuit(
            query=query,
            content=payload.get("content"),
            summary=payload.get("summary"),
            subject=payload.get("subject"),
        )
        score += utahraptor_boost
        basilosaurus_boost = 0.0
        basilosaurus_reasons: list[str] = []
        if payload["id"] in semantic_ids:
            basilosaurus_boost, basilosaurus_reasons = _basilosaurus_semantic_echo(
                query=query,
                content=payload.get("content"),
                summary=payload.get("summary"),
                subject=payload.get("subject"),
                oracle=oracle,
            )
            score += basilosaurus_boost
        compressed_stage_score = 0.0
        if payload["id"] in compressed_ids:
            compressed_score = float(payload.get("compressed_prefilter_score") or 0.0)
            compressed_stage_score = round(min(0.1, compressed_score * 0.16), 6)
            score += compressed_stage_score
        scope_signal = 1.0 if (payload["scope_type"] == scope_type and payload["scope_id"] == scope_id) else 0.72 if payload["scope_type"] == "global" else 0.44
        semantic_signal = 0.0
        if payload["id"] in semantic_ids:
            semantic_signal = min(1.0, basilosaurus_boost * 4.5)
        lexical_signal = min(1.0, (normalized_rank * 0.72) + (utahraptor_boost * 3.0))
        compressed_signal = min(1.0, float(payload.get("compressed_prefilter_score") or 0.0))
        activation_signal = min(1.0, float(payload["activation_score"]))
        hybrid_fusion = fuse_hybrid_signals(
            route_profile=route_profile,
            signals={
                "lexical": lexical_signal,
                "semantic": semantic_signal,
                "graph": 0.0,
                "compressed": compressed_signal,
                "scope": scope_signal,
                "activation": activation_signal,
            },
            governance_alignment=compute_governance_alignment(
                admission_state=admission_state,
                conflict_status=payload["conflict_status"],
            ),
        )
        score += round(hybrid_fusion.fused_score * 0.08, 6)
        score = round(score + dynamic_score_bonus(v10_core_signals), 6)
        if admission_state == "hypothesized":
            score = round(score * 0.88, 6)
        elif admission_state == "consolidated":
            score = round(score * 0.94, 6)
        elif admission_state == "archived":
            score = round(score * 0.72, 6)
        reasons = build_reason_tags(
            query=query,
            content=payload.get("content"),
            summary=payload.get("summary"),
            subject=payload.get("subject"),
            memory_type=payload["type"],
            scope_type=payload["scope_type"],
            scope_id=payload["scope_id"],
            requested_scope_type=scope_type,
            requested_scope_id=scope_id,
            include_global=include_global,
            activation_score=float(payload["activation_score"]),
            conflict_status=payload["conflict_status"],
            admission_state=admission_state,
            score_profile=score_profile,
        )
        reasons.extend(utahraptor_reasons)
        reasons.extend(basilosaurus_reasons)
        if payload["id"] in compressed_ids:
            reasons.append(f"turboquant_candidate_tier:{payload.get('compressed_prefilter_tier', 'warm')}")
            reasons.append(f"turboquant_prefilter_band:{payload.get('compressed_prefilter_band', 'light')}")
            reasons.append(f"turboquant_prefilter_score:{round(float(payload.get('compressed_prefilter_score') or 0.0), 3)}")
        reasons.extend(hybrid_reason_tags(hybrid_fusion))
        reasons.extend(dynamic_reason_tags(v10_core_signals))
        retrieval_stage = "semantic_recall" if payload["id"] in semantic_ids and payload["id"] not in lexical_ids else "lexical"
        if payload["id"] in compressed_ids and payload["id"] not in lexical_ids and payload["id"] not in semantic_ids:
            retrieval_stage = "compressed_prefilter"
        _merge_result(
            results_by_id,
            CanonicalSearchResult(
                id=payload["id"],
                type=payload["type"],
                content=payload["content"],
                summary=payload["summary"],
                subject=payload["subject"],
                score=score,
                reasons=reasons,
                source_kind=payload["source_kind"],
                source_ref=payload["source_ref"],
                scope_type=payload["scope_type"],
                scope_id=payload["scope_id"],
                conflict_status=payload["conflict_status"],
                admission_state=admission_state,
                score_profile=score_profile,
                retrieval_stage=retrieval_stage,
                v10_core_signals=v10_core_signals,
                hybrid_fusion=hybrid_fusion.to_payload(),
            ),
        )

    if lexical_ids and hasattr(db, "list_link_expansions") and scope_type and scope_id:
        seed_ids = [item.id for item in sorted(results_by_id.values(), key=lambda item: item.score, reverse=True)[: min(3, len(results_by_id))]]
        for row in db.list_link_expansions(
            seed_ids=seed_ids,
            scope_type=scope_type,
            scope_id=scope_id,
            limit=max(2, min(limit, 5)),
        ):
            payload = dict(row)
            metadata = _coerce_metadata(payload.get("metadata_json"))
            score_profile = metadata.get("score_profile", {}) if isinstance(metadata, dict) else {}
            admission_state = _derive_admission_state(payload["status"], metadata)
            if admission_state in {"draft", "invalidated"}:
                continue
            graph_score = score_link_expansion(
                link_weight=float(payload.get("weight") or 0.0),
                hop_depth=1,
                link_type=payload.get("link_type") or "supports",
                memory_type=payload["type"],
            )
            reasons = build_reason_tags(
                query=query,
                content=payload.get("content"),
                summary=payload.get("summary"),
                subject=payload.get("subject"),
                memory_type=payload["type"],
                scope_type=payload["scope_type"],
                scope_id=payload["scope_id"],
                requested_scope_type=scope_type,
                requested_scope_id=scope_id,
                include_global=include_global,
                activation_score=float(payload["activation_score"]),
                conflict_status=payload.get("conflict_status", "none"),
                admission_state=admission_state,
                score_profile=score_profile,
            )
            reasons.append(f"pterodactyl_graph_overview:{payload.get('link_type')}")
            v10_core_signals = compute_v10_core_signals(
                row={
                    "confidence": payload["confidence"],
                    "activation_score": payload["activation_score"],
                    "access_count": payload.get("access_count", 0),
                    "metadata": metadata,
                },
                admission_state=admission_state,
                evidence_count=evidence_map.get(payload["id"], 0),
                support_weight=support_map.get(payload["id"], 0.0),
                conflict_weight=conflict_map.get(payload["id"], (0.0, False))[0],
                direct_conflict_open=conflict_map.get(payload["id"], (0.0, False))[1],
            )
            scope_signal = 1.0 if (payload["scope_type"] == scope_type and payload["scope_id"] == scope_id) else 0.72 if payload["scope_type"] == "global" else 0.44
            hybrid_fusion = fuse_hybrid_signals(
                route_profile=route_profile,
                signals={
                    "lexical": 0.0,
                    "semantic": 0.0,
                    "graph": min(1.0, graph_score),
                    "compressed": 0.0,
                    "scope": scope_signal,
                    "activation": min(1.0, float(payload["activation_score"])),
                },
                governance_alignment=compute_governance_alignment(
                    admission_state=admission_state,
                    conflict_status=payload.get("conflict_status", "none"),
                ),
            )
            reasons.extend(hybrid_reason_tags(hybrid_fusion))
            reasons.extend(dynamic_reason_tags(v10_core_signals))
            _merge_result(
                results_by_id,
                CanonicalSearchResult(
                    id=payload["id"],
                    type=payload["type"],
                    content=payload["content"],
                    summary=payload["summary"],
                    subject=payload["subject"],
                    score=round(graph_score + (hybrid_fusion.fused_score * 0.08) + dynamic_score_bonus(v10_core_signals), 6),
                    reasons=reasons,
                    source_kind=payload["source_kind"],
                    source_ref=payload["source_ref"],
                    scope_type=payload["scope_type"],
                    scope_id=payload["scope_id"],
                    conflict_status=payload.get("conflict_status", "none"),
                    admission_state=admission_state,
                    score_profile=score_profile,
                    retrieval_stage="link_expansion",
                    relation_via_link_type=payload.get("link_type"),
                    relation_via_memory_id=payload.get("source_id"),
                    relation_via_hops=1,
                    v10_core_signals=v10_core_signals,
                    hybrid_fusion=hybrid_fusion.to_payload(),
                ),
            )

    results = list(results_by_id.values())
    results.sort(key=lambda item: item.score, reverse=True)
    return results


def _coerce_metadata(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    return dict(raw)


def _derive_admission_state(status: str, metadata: dict[str, Any]) -> str:
    memory_state = metadata.get("memory_state")
    if isinstance(memory_state, str) and memory_state.strip():
        return memory_state
    admission_state = metadata.get("admission_state")
    if isinstance(admission_state, str) and admission_state.strip():
        return admission_state
    promotion = metadata.get("promotion")
    reasons = promotion.get("reasons", []) if isinstance(promotion, dict) else []
    if status == "superseded":
        return "invalidated"
    if status in {"archived", "expired"}:
        return "consolidated"
    if isinstance(promotion, dict) and promotion.get("promotable") is False:
        return "draft"
    if "review_contradiction_risk" in reasons or "contradiction_risk_detected" in reasons:
        return "hypothesized"
    return "validated"


def _run_compressed_candidate_stage(
    db: Any,
    *,
    query: str,
    query_signature: CompressedSignature,
    scope_type: str,
    scope_id: str,
    limit: int,
    exclude_ids: set[str],
    include_global: bool,
    prefilter: CompressedCandidatePrefilter,
) -> list[dict[str, Any]]:
    where_clauses = [f"status IN ({RETRIEVABLE_MEMORY_STATUS_SQL})"]
    params: list[Any] = []
    if include_global:
        where_clauses.append("((scope_type = ? AND scope_id = ?) OR scope_type = 'global')")
        params.extend([scope_type, scope_id])
    else:
        where_clauses.append("scope_type = ?")
        where_clauses.append("scope_id = ?")
        params.extend([scope_type, scope_id])
    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        where_clauses.append(f"id NOT IN ({placeholders})")
        params.extend(sorted(exclude_ids))
    sql = f"""
        SELECT *
        FROM memories
        WHERE {' AND '.join(where_clauses)}
        ORDER BY activation_score DESC, updated_at DESC
        LIMIT 32
    """
    rows = [dict(row) for row in db.fetch_all(sql, params)]
    matched: list[dict[str, Any]] = []
    for row in rows:
        metadata = _coerce_metadata(row.get("metadata_json"))
        compressed_payload = metadata.get("compressed_tier") if isinstance(metadata, dict) else None
        candidate_signature = prefilter.signature_from_payload(compressed_payload)
        if candidate_signature is None:
            compressed_payload = build_compressed_tier_payload(
                content=row.get("content"),
                summary=row.get("summary"),
                subject=row.get("subject"),
                status=str(row.get("status") or "active"),
                activation_score=float(row.get("activation_score") or 0.0),
                metadata=metadata,
                prefilter=prefilter,
            )
            candidate_signature = prefilter.signature_from_payload(compressed_payload)
        tier = str((compressed_payload or {}).get("tier") or "warm")
        if candidate_signature is None:
            continue
        match = prefilter.match(query_signature, candidate_signature, tier=tier)
        if match.score < 0.34:
            continue
        row["compressed_prefilter_score"] = match.score
        row["compressed_prefilter_lexical_overlap"] = match.lexical_overlap
        row["compressed_prefilter_semantic_overlap"] = match.semantic_overlap
        row["compressed_prefilter_band"] = match.band
        row["compressed_prefilter_tier"] = match.tier
        row["compressed_tier"] = compressed_payload
        row["lexical_score"] = row.get("lexical_score", 0.0)
        row["conflict_status"] = "none"
        matched.append(row)
    matched.sort(
        key=lambda item: (
            float(item.get("compressed_prefilter_score") or 0.0),
            float(item.get("activation_score") or 0.0),
        ),
        reverse=True,
    )
    return matched[:limit]


def _count_evidence_for_memory(db: Any, memory_id: str) -> int:
    row = db.fetch_one(
        "SELECT COUNT(*) AS count FROM evidence_events WHERE memory_id = ?",
        (memory_id,),
    )
    return int(row["count"] if row else 0)


def _support_weight_for_memory(db: Any, memory_id: str) -> float:
    row = db.fetch_one(
        """
        SELECT COALESCE(SUM(CASE
            WHEN link_type IN ('same_subject', 'supports', 'extends', 'procedural_supports_semantic')
            THEN weight
            ELSE 0
        END), 0) AS total
        FROM memory_links
        WHERE source_id = ? OR target_id = ?
        """,
        (memory_id, memory_id),
    )
    return float(row["total"] if row else 0.0)


def _conflict_weight_for_memory(db: Any, memory_id: str) -> tuple[float, bool]:
    rows = db.fetch_all(
        """
        SELECT
            CASE
                WHEN c.memory_a_id = ? THEN c.memory_b_id
                ELSE c.memory_a_id
            END AS peer_id
        FROM conflicts c
        WHERE c.status = 'open'
          AND (c.memory_a_id = ? OR c.memory_b_id = ?)
        """,
        (memory_id, memory_id, memory_id),
    )
    if not rows:
        return 0.0, False
    weight = 0.0
    for row in rows:
        peer = db.fetch_one("SELECT confidence FROM memories WHERE id = ?", (row["peer_id"],))
        if peer is None:
            continue
        weight += max(0.0, float(peer["confidence"] or 0.0))
    return weight, True
