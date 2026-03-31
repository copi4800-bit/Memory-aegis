from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, List
from ..hygiene.transitions import append_lifecycle_event, transition_memory, coerce_metadata
from ..memory.factory import MemoryFactory


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConflictManager:
    """Detects and logs contradiction candidates conservatively."""

    USER_RESOLUTION_ACTIONS = (
        "keep_newer",
        "keep_older",
        "keep_both_scope_split",
        "mark_exception",
    )

    def __init__(self, db_manager):
        self.db = db_manager
        self.factory = MemoryFactory()

    def scan_conflicts(self, subject: str) -> List[tuple[str, str]]:
        memories = self.db.fetch_all(
            """
            SELECT id, content, activation_score, confidence, subject, metadata_json, created_at, scope_type, scope_id
            FROM memories
            WHERE subject = ? AND status = 'active'
            """,
            (subject,),
        )
        conflicts_found: List[tuple[str, str]] = []
        if len(memories) < 2:
            return conflicts_found

        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                mem_a = memories[i]
                mem_b = memories[j]
                if mem_a["scope_type"] != mem_b["scope_type"] or mem_a["scope_id"] != mem_b["scope_id"]:
                    continue
                
                # Detect contradiction
                is_contradiction = self._detect_contradiction(mem_a["content"], mem_b["content"])
                contextual_pair = self._contextual_candidate(mem_a["content"], mem_b["content"])
                
                # Check for correction metadata
                meta_a = json.loads(mem_a["metadata_json"]) if isinstance(mem_a["metadata_json"], str) else (mem_a["metadata_json"] or {})
                meta_b = json.loads(mem_b["metadata_json"]) if isinstance(mem_b["metadata_json"], str) else (mem_b["metadata_json"] or {})
                
                is_correction_a = meta_a.get("is_correction", False)
                is_correction_b = meta_b.get("is_correction", False)

                # If one is an explicit correction, we treat high overlap as a conflict candidate
                if not is_contradiction and (is_correction_a or is_correction_b):
                    overlap = self._score_pair(mem_a["content"], mem_b["content"])
                    if overlap > 0.2: # Lower threshold for corrections in same subject
                        is_contradiction = True

                if is_contradiction or contextual_pair:
                    score = self._score_pair(mem_a["content"], mem_b["content"])
                    if self._conflict_exists(mem_a["id"], mem_b["id"]):
                        continue
                    
                    reason = "Potential logical contradiction"
                    if is_correction_a or is_correction_b:
                        reason = "Correction candidate"
                    elif contextual_pair:
                        reason = "Contextual coexistence candidate"
                    
                    conflict_id = self._log_conflict(
                        mem_a["id"],
                        mem_b["id"],
                        mem_a["subject"],
                        score,
                        reason,
                    )
                    self.db.record_evidence_artifact(
                        artifact_kind="conflict_comparison",
                        scope_type=mem_a["scope_type"],
                        scope_id=mem_a["scope_id"],
                        memory_id=mem_a["id"],
                        payload={
                            "conflict_id": conflict_id,
                            "memory_a_id": mem_a["id"],
                            "memory_b_id": mem_b["id"],
                            "score": score,
                            "reason": reason,
                            "content_a": mem_a["content"],
                            "content_b": mem_b["content"],
                        },
                    )
                    append_lifecycle_event(self.db, mem_a["id"], "conflict_detected", details={"conflict_id": conflict_id})
                    append_lifecycle_event(self.db, mem_b["id"], "conflict_detected", details={"conflict_id": conflict_id})
                    conflicts_found.append((mem_a["id"], mem_b["id"]))
        return conflicts_found

    def get_resolution_prompt(self, conflict_id: str) -> dict[str, Any] | None:
        payload = self._build_conflict_payload(conflict_id)
        if payload is None or payload["classification"] not in {
            "user_resolution_required",
            "weak_conflict_candidate",
            "contextual_coexistence",
        }:
            return None
        return payload

    def list_resolution_prompts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        subject: str | None = None,
    ) -> list[dict[str, Any]]:
        query = [
            """
            SELECT id
            FROM conflicts
            WHERE status IN ('open', 'suggested')
            """
        ]
        params: list[Any] = []
        if subject is not None:
            query.append("AND subject_key = ?")
            params.append(subject)
        if scope_type is not None and scope_id is not None:
            query.append(
                """
                AND EXISTS (
                    SELECT 1
                    FROM memories m
                    WHERE m.id = conflicts.memory_a_id
                      AND m.scope_type = ?
                      AND m.scope_id = ?
                )
                """
            )
            params.extend([scope_type, scope_id])
        query.append("ORDER BY created_at ASC")
        rows = self.db.fetch_all("\n".join(query), tuple(params))
        prompts: list[dict[str, Any]] = []
        for row in rows:
            payload = self.get_resolution_prompt(row["id"])
            if payload is not None:
                prompts.append(payload)
        return prompts

    def auto_resolve(self, conflict_id: str) -> bool:
        payload = self._build_conflict_payload(conflict_id)
        if payload is None:
            return False

        if payload["classification"] == "user_resolution_required":
            return self.suggest_resolution(conflict_id, "user_resolution_required")

        memories = payload["memories"]
        score_gap = abs(float(memories["older"]["activation_score"]) - float(memories["newer"]["activation_score"]))
        if score_gap < 0.5:
            return self.suggest_resolution(conflict_id, "manual_review_required")

        to_supersede = memories["older"]["id"]
        winner_id = memories["newer"]["id"]
        if memories["older"]["activation_score"] >= memories["newer"]["activation_score"]:
            to_supersede = memories["newer"]["id"]
            winner_id = memories["older"]["id"]
        self._mark_superseded(to_supersede, conflict_id, winner_id)
        self.db.execute("UPDATE memories SET status = 'superseded' WHERE id = ?", (to_supersede,))
        self.db.execute(
            "UPDATE conflicts SET status = 'resolved', resolution = ?, resolved_at = ? WHERE id = ?",
            ("safe_score_supersede", _now_iso(), conflict_id),
        )
        return True

    def resolve_with_user_decision(
        self,
        conflict_id: str,
        *,
        action: str,
        rationale: str | None = None,
    ) -> dict[str, Any]:
        if action not in self.USER_RESOLUTION_ACTIONS:
            raise ValueError(f"Unsupported conflict resolution action: {action}")
        payload = self._build_conflict_payload(conflict_id)
        if payload is None:
            raise ValueError(f"Conflict not found or not open: {conflict_id}")

        older = payload["memories"]["older"]
        newer = payload["memories"]["newer"]
        timestamp = _now_iso()
        details = {
            "conflict_id": conflict_id,
            "action": action,
            "rationale": rationale,
            "resolved_at": timestamp,
        }

        if action == "keep_newer":
            self._mark_superseded(older["id"], conflict_id, newer["id"])
            append_lifecycle_event(
                self.db,
                newer["id"],
                "confirmed_by_user_conflict_resolution",
                details={"conflict_id": conflict_id, "kept": True, "rationale": rationale},
                at=timestamp,
            )
            resolution = "resolved_by_user_keep_newer"
            summary = "Kept the newer memory and superseded the older one."
        elif action == "keep_older":
            self._mark_superseded(newer["id"], conflict_id, older["id"])
            append_lifecycle_event(
                self.db,
                older["id"],
                "confirmed_by_user_conflict_resolution",
                details={"conflict_id": conflict_id, "kept": True, "rationale": rationale},
                at=timestamp,
            )
            resolution = "resolved_by_user_keep_older"
            summary = "Kept the older memory and superseded the newer one."
        elif action == "keep_both_scope_split":
            append_lifecycle_event(
                self.db,
                older["id"],
                "scope_split_confirmed_by_user",
                details=details,
                at=timestamp,
            )
            append_lifecycle_event(
                self.db,
                newer["id"],
                "scope_split_confirmed_by_user",
                details=details,
                at=timestamp,
            )
            self._record_coexistence_summary(
                older=older,
                newer=newer,
                conflict_id=conflict_id,
                resolution="scope_split",
            )
            resolution = "resolved_by_user_scope_split"
            summary = "Kept both memories and marked the pair as scope-separated."
        else:
            append_lifecycle_event(
                self.db,
                older["id"],
                "exception_confirmed_by_user",
                details=details,
                at=timestamp,
            )
            append_lifecycle_event(
                self.db,
                newer["id"],
                "exception_confirmed_by_user",
                details=details,
                at=timestamp,
            )
            self._record_coexistence_summary(
                older=older,
                newer=newer,
                conflict_id=conflict_id,
                resolution="exception",
            )
            resolution = "resolved_by_user_exception"
            summary = "Kept both memories and marked the pair as an explicit exception."

        self.db.execute(
            """
            UPDATE conflicts
            SET status = 'resolved',
                resolution = ?,
                resolved_at = ?
            WHERE id = ?
            """,
            (resolution, timestamp, conflict_id),
        )
        return {
            "conflict_id": conflict_id,
            "action": action,
            "resolution": resolution,
            "summary": summary,
            "rationale": rationale,
            "resolved_at": timestamp,
            "classification": payload["classification"],
        }

    def suggest_resolution(self, conflict_id: str, resolution: str = "manual_review_required") -> bool:
        row = self.db.fetch_one(
            "SELECT id FROM conflicts WHERE id = ? AND status = 'open'",
            (conflict_id,),
        )
        if row is None:
            return False
        self.db.execute(
            """
            UPDATE conflicts
            SET status = 'suggested',
                resolution = ?,
                resolved_at = ?
            WHERE id = ?
            """,
            (resolution, _now_iso(), conflict_id),
        )
        return True

    def _detect_contradiction(self, text_a: str, text_b: str) -> bool:
        keywords_a = self._tokenize(text_a)
        keywords_b = self._tokenize(text_b)
        if not keywords_a or not keywords_b:
            return False
        common = keywords_a.intersection(keywords_b)
        overlap = len(common) / max(len(keywords_a), len(keywords_b))
        
        # Enhanced negation detection for both English and Vietnamese
        negation_words = {"not", "never", "no", "cannot", "không", "chưa", "hết", "chẳng"}
        has_neg_a = any(w in negation_words for w in keywords_a)
        has_neg_b = any(w in negation_words for w in keywords_b)
        
        if self._context_markers(text_a) and self._context_markers(text_b) and self._context_markers(text_a) != self._context_markers(text_b):
            return False
            
        # If one has negation and the other doesn't, and they overlap significantly
        return overlap > 0.4 and has_neg_a != has_neg_b

    def _score_pair(self, text_a: str, text_b: str) -> float:
        keywords_a = self._tokenize(text_a)
        keywords_b = self._tokenize(text_b)
        if not keywords_a or not keywords_b:
            return 0.0
        common = keywords_a.intersection(keywords_b)
        return len(common) / max(len(keywords_a), len(keywords_b))

    def _tokenize(self, text: str) -> set[str]:
        return {token for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if token}

    def _contextual_candidate(self, text_a: str, text_b: str) -> bool:
        overlap = self._score_pair(text_a, text_b)
        markers_a = self._context_markers(text_a)
        markers_b = self._context_markers(text_b)
        return overlap >= 0.15 and bool(markers_a) and bool(markers_b) and markers_a != markers_b

    def _log_conflict(self, a_id: str, b_id: str, subject_key: str | None, score: float, reason: str) -> str:
        conflict_id = str(uuid.uuid4())
        self.db.execute(
            """
            INSERT INTO conflicts (
                id, memory_a_id, memory_b_id, subject_key, score, reason, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (conflict_id, a_id, b_id, subject_key, score, reason, _now_iso()),
        )
        return conflict_id

    def _conflict_exists(self, a_id: str, b_id: str) -> bool:
        row = self.db.fetch_one(
            """
            SELECT id
            FROM conflicts
            WHERE (memory_a_id = ? AND memory_b_id = ?)
               OR (memory_a_id = ? AND memory_b_id = ?)
            LIMIT 1
            """,
            (a_id, b_id, b_id, a_id),
        )
        return row is not None

    def _mark_superseded(self, memory_id: str, conflict_id: str, winner_id: str) -> None:
        transition_memory(
            self.db,
            memory_id,
            status="superseded",
            event="superseded_by_conflict",
            details={"conflict_id": conflict_id, "winner_id": winner_id},
        )

    def _build_conflict_payload(self, conflict_id: str) -> dict[str, Any] | None:
        row = self.db.fetch_one(
            """
            SELECT
                c.id,
                c.subject_key,
                c.score,
                c.reason,
                c.status,
                c.resolution,
                c.created_at AS conflict_created_at,
                c.resolved_at,
                m_a.id AS id_a,
                m_a.content AS content_a,
                m_a.subject AS subject_a,
                m_a.scope_type AS scope_type_a,
                m_a.scope_id AS scope_id_a,
                m_a.activation_score AS score_a,
                m_a.confidence AS confidence_a,
                m_a.created_at AS created_at_a,
                m_a.metadata_json AS metadata_a,
                m_b.id AS id_b,
                m_b.content AS content_b,
                m_b.subject AS subject_b,
                m_b.scope_type AS scope_type_b,
                m_b.scope_id AS scope_id_b,
                m_b.activation_score AS score_b,
                m_b.confidence AS confidence_b,
                m_b.created_at AS created_at_b,
                m_b.metadata_json AS metadata_b
            FROM conflicts c
            JOIN memories m_a ON c.memory_a_id = m_a.id
            JOIN memories m_b ON c.memory_b_id = m_b.id
            WHERE c.id = ?
            """,
            (conflict_id,),
        )
        if row is None:
            return None

        mem_a = self._build_memory_view(row, suffix="a")
        mem_b = self._build_memory_view(row, suffix="b")
        older, newer = sorted([mem_a, mem_b], key=lambda item: item["created_at"])
        classification = self._classify_pair(mem_a, mem_b, row["reason"], float(row["score"] or 0))
        decision = self._decision_for(classification, mem_a, mem_b)
        return {
            "conflict_id": row["id"],
            "classification": classification,
            "conflict_type": "hard_conflict" if classification == "user_resolution_required" else "deterministic_conflict",
            "subject": row["subject_key"],
            "score": float(row["score"] or 0),
            "reason": row["reason"],
            "status": row["status"],
            "resolution": row["resolution"],
            "created_at": row["conflict_created_at"],
            "resolved_at": row["resolved_at"],
            "same_scope": mem_a["scope_type"] == mem_b["scope_type"] and mem_a["scope_id"] == mem_b["scope_id"],
            "memories": {"older": older, "newer": newer},
            "recommended_action": self._recommended_action_for(classification, older, newer),
            "decision": decision["decision"],
            "decision_reason": decision["reason"],
            "decision_policy": decision["policy"],
            "actions": self._build_actions(),
        }

    def _build_memory_view(self, row: Any, *, suffix: str) -> dict[str, Any]:
        metadata = self._coerce_metadata(row[f"metadata_{suffix}"])
        confidence = float(row[f"confidence_{suffix}"] or 1.0)
        activation_score = float(row[f"score_{suffix}"] or 0)
        return {
            "id": row[f"id_{suffix}"],
            "content": row[f"content_{suffix}"],
            "subject": row[f"subject_{suffix}"],
            "scope_type": row[f"scope_type_{suffix}"],
            "scope_id": row[f"scope_id_{suffix}"],
            "activation_score": activation_score,
            "confidence": confidence,
            "created_at": row[f"created_at_{suffix}"],
            "metadata": metadata,
            "score_profile": metadata.get("score_profile", {}),
            "context_markers": sorted(self._context_markers(row[f"content_{suffix}"])),
        }

    def _classify_pair(self, mem_a: dict[str, Any], mem_b: dict[str, Any], reason: str | None, score: float) -> str:
        if mem_a["scope_type"] != mem_b["scope_type"] or mem_a["scope_id"] != mem_b["scope_id"]:
            return "cross_scope_candidate"
        if self._contextual_coexistence(mem_a, mem_b):
            return "contextual_coexistence"
        if mem_a["metadata"].get("is_correction") or mem_b["metadata"].get("is_correction"):
            return "deterministic_resolution_candidate"
        if reason == "Correction candidate":
            return "deterministic_resolution_candidate"
        if score < 0.3:
            return "weak_conflict_candidate"
        if min(mem_a["confidence"], mem_b["confidence"]) < 0.75:
            return "weak_conflict_candidate"
        if abs(mem_a["activation_score"] - mem_b["activation_score"]) >= 0.5:
            return "deterministic_resolution_candidate"
        return "user_resolution_required"

    def _recommended_action_for(self, classification: str, older: dict[str, Any], newer: dict[str, Any]) -> str | None:
        if classification == "contextual_coexistence":
            return "mark_exception"
        if classification != "user_resolution_required":
            return None
        return "keep_newer"

    def _build_actions(self) -> list[dict[str, str]]:
        return [
            {"id": "keep_newer", "label": "Keep newer", "description": "Supersede the older memory and keep the newer memory active."},
            {"id": "keep_older", "label": "Keep older", "description": "Supersede the newer memory and keep the older memory active."},
            {"id": "keep_both_scope_split", "label": "Scope split", "description": "Keep both memories and treat the difference as scope-specific."},
            {"id": "mark_exception", "label": "Mark exception", "description": "Keep both memories active as an explicit exception pair."},
        ]

    def _coerce_metadata(self, raw) -> dict:
        return coerce_metadata(raw)

    def _record_coexistence_summary(
        self,
        *,
        older: dict[str, Any],
        newer: dict[str, Any],
        conflict_id: str,
        resolution: str,
    ) -> None:
        subject = older.get("subject") or newer.get("subject") or "conflict.coexistence"
        coexistence = {
            "entity": subject,
            "states": [
                {
                    "value": older["content"],
                    "context": older.get("context_markers", []),
                    "status": "validated",
                },
                {
                    "value": newer["content"],
                    "context": newer.get("context_markers", []),
                    "status": "validated",
                },
            ],
            "policy": "contextual_preference_coexistence",
            "resolution": resolution,
        }
        memory = self.factory.create(
            type="semantic",
            content=f"Contextual coexistence recorded for {subject}.",
            scope_type=older["scope_type"],
            scope_id=older["scope_id"],
            source_kind="system",
            source_ref=f"conflict://{conflict_id}",
            subject=subject,
            summary="Contextual coexistence summary",
            metadata={
                "memory_state": "consolidated",
                "admission_state": "consolidated",
                "derived_from": [older["id"], newer["id"]],
                "coexistence_summary": coexistence,
                "lineage": {"derived_from": [older["id"], newer["id"]], "preserves_raw_evidence": True},
                "score_profile": {
                    "source_reliability": 0.86,
                    "recency": 0.7,
                    "specificity": 0.84,
                    "directness": 0.8,
                    "frequency": 0.55,
                    "conflict_pressure": 0.18,
                },
            },
            confidence=0.83,
            activation_score=0.98,
        )
        self.db.put_memory(memory)
        self.db.record_evidence_artifact(
            artifact_kind="coexistence_summary",
            scope_type=older["scope_type"],
            scope_id=older["scope_id"],
            memory_id=memory.id,
            payload={
                "conflict_id": conflict_id,
                "derived_from": [older["id"], newer["id"]],
                "coexistence_summary": coexistence,
            },
        )

    def _contextual_coexistence(self, mem_a: dict[str, Any], mem_b: dict[str, Any]) -> bool:
        markers_a = set(mem_a.get("context_markers", []))
        markers_b = set(mem_b.get("context_markers", []))
        if not markers_a or not markers_b:
            return False
        if markers_a == markers_b:
            return False
        return bool(markers_a.symmetric_difference(markers_b))

    def _decision_for(self, classification: str, mem_a: dict[str, Any], mem_b: dict[str, Any]) -> dict[str, Any]:
        if classification == "contextual_coexistence":
            return {
                "decision": "coexist",
                "reason": [
                    "Both records can coexist after contextualization.",
                    f"Context A: {', '.join(mem_a.get('context_markers', [])) or 'none'}",
                    f"Context B: {', '.join(mem_b.get('context_markers', [])) or 'none'}",
                ],
                "policy": "contextual_preference_coexistence",
            }
        if classification == "deterministic_resolution_candidate":
            return {
                "decision": "supersede_candidate",
                "reason": ["Confidence or correction signals allow deterministic resolution."],
                "policy": "safe_supersede",
            }
        if classification == "weak_conflict_candidate":
            return {
                "decision": "review",
                "reason": ["Evidence is too weak for deterministic resolution."],
                "policy": "weak_conflict_review",
            }
        return {
            "decision": "user_resolution_required",
            "reason": ["Conflict remains ambiguous and requires explicit resolution."],
            "policy": "human_in_loop",
        }

    def _context_markers(self, text: str) -> set[str]:
        lowered = text.lower()
        markers: set[str] = set()
        mapping = {
            "morning": ("morning", "buổi sáng", "sáng"),
            "evening": ("evening", "night", "buổi tối", "tối"),
            "stress": ("stressed", "stress", "high_workload", "căng", "căng thẳng", "áp lực"),
            "work": ("work", "working", "làm việc", "công việc"),
            "weekend": ("weekend", "cuối tuần"),
        }
        for canonical, variants in mapping.items():
            if any(term in lowered for term in variants):
                markers.add(canonical)
        return markers
