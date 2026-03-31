from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from .contract import blend_retrieval_score, build_reason_tags
from .v8_dynamics import compute_v8_core_signals, dynamic_reason_tags, dynamic_score_bonus
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
    v8_core_signals: dict[str, Any] | None = None


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

    if fts_query:
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
    else:
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

    rows = db.fetch_all(sql, (*params, limit))
    
    # Fallback for natural language: if AND search yielded nothing, try OR search
    if not rows and fallback_to_or and fts_query and " " in fts_query:
        or_query = " OR ".join(fts_query.split())
        or_params = list(params)
        # Find the index of the first param which is the fts_query
        for i, p in enumerate(or_params):
            if p == fts_query:
                or_params[i] = or_query
                break
        rows = db.fetch_all(sql, (*or_params, limit))

    results: list[CanonicalSearchResult] = []
    
    # --- BATCH PREFETCHING O(1) ---
    memory_ids = [str(dict(r)["id"]) for r in rows]
    evidence_map = db.batch_count_evidence(memory_ids) if memory_ids and hasattr(db, 'batch_count_evidence') else {}
    support_map = db.batch_support_weight(memory_ids) if memory_ids and hasattr(db, 'batch_support_weight') else {}
    conflict_map = db.batch_conflict_weight(memory_ids) if memory_ids and hasattr(db, 'batch_conflict_weight') else {}

    for row in rows:
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
        
        v8_core_signals = compute_v8_core_signals(
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
        score = blend_retrieval_score(float(payload["lexical_score"]), float(payload["activation_score"]), score_profile)
        score = round(score + dynamic_score_bonus(v8_core_signals), 6)
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
        reasons.extend(dynamic_reason_tags(v8_core_signals))
        results.append(
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
                v8_core_signals=v8_core_signals,
            )
        )

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
