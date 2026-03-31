from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from ..governance.rollback import RollbackManager
from ..memory.factory import MemoryFactory
from ..storage.db import DatabaseManager
from ..storage.manager import StorageManager


class GovernedBackgroundIntelligence:
    """Plans background proposals on working copies and records them for review."""

    def __init__(
        self,
        storage: StorageManager,
        *,
        signal_provider: Any | None = None,
        transition_applier: Any | None = None,
    ):
        self.storage = storage
        self.factory = MemoryFactory()
        self.signal_provider = signal_provider
        self.transition_applier = transition_applier

    def plan_scope(self, *, scope_type: str, scope_id: str) -> list[dict[str, Any]]:
        proposals: list[dict[str, Any]] = []
        proposals.extend(self._plan_condensation(scope_type=scope_type, scope_id=scope_id))
        proposals.extend(self._plan_staleness_review(scope_type=scope_type, scope_id=scope_id))
        proposals.extend(self._plan_graph_repair(scope_type=scope_type, scope_id=scope_id))
        proposals.extend(self._plan_v8_transition_review(scope_type=scope_type, scope_id=scope_id))
        for proposal in proposals:
            self.storage.record_background_intelligence_run(
                scope_type=scope_type,
                scope_id=scope_id,
                worker_kind=proposal["worker_kind"],
                proposal=proposal,
                mode="working_copy",
                status="planned",
            )
        return proposals

    def list_runs(self, *, scope_type: str, scope_id: str, status: str | None = None) -> list[dict[str, Any]]:
        return self.storage.list_background_intelligence_runs(
            scope_type=scope_type,
            scope_id=scope_id,
            status=status,
        )

    def shadow_run(self, run_id: str) -> dict[str, Any]:
        run = self.storage.get_background_intelligence_run(run_id)
        if run is None:
            return {"shadowed": False, "reason": "missing_run"}
        proposal = dict(run["proposal"])
        predicted = self._predict_mutations(run, proposal)
        result = {
            "shadowed": True,
            "worker_kind": run["worker_kind"],
            "run_id": run_id,
            "predicted_mutations": predicted,
        }
        self.storage.update_background_intelligence_run(
            run_id,
            status="shadowed",
            proposal={**proposal, "shadow_result": result},
        )
        self.storage.record_governance_event(
            event_kind="background_run_shadowed",
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            payload=result,
        )
        return result

    def apply_run(self, run_id: str, *, max_mutations: int = 5) -> dict[str, Any]:
        run = self.storage.get_background_intelligence_run(run_id)
        if run is None:
            return {"applied": False, "reason": "missing_run"}
        proposal = dict(run["proposal"])
        predicted = self._predict_mutations(run, proposal)
        if predicted > max_mutations:
            result = {
                "applied": False,
                "worker_kind": run["worker_kind"],
                "run_id": run_id,
                "reason": "blast_radius_exceeded",
                "predicted_mutations": predicted,
                "max_mutations": max_mutations,
            }
            self.storage.update_background_intelligence_run(
                run_id,
                status="discarded",
                proposal={**proposal, "apply_result": result},
            )
            self.storage.record_governance_event(
                event_kind="background_run_blocked",
                scope_type=run["scope_type"],
                scope_id=run["scope_id"],
                payload=result,
            )
            return result

        result = {"applied": False, "worker_kind": run["worker_kind"], "run_id": run_id, "audit_ids": []}
        if run["worker_kind"] == "graph_repair":
            applied, audit_ids = self._apply_graph_repair(run, proposal)
            result["applied"] = applied > 0
            result["links_added"] = applied
            result["audit_ids"] = audit_ids
        elif run["worker_kind"] == "condensation":
            applied, audit_ids = self._apply_condensation(run, proposal)
            result["applied"] = applied > 0
            result["archived"] = applied
            result["audit_ids"] = audit_ids
        elif run["worker_kind"] == "staleness_review":
            applied, audit_ids = self._apply_staleness_review(run, proposal)
            result["applied"] = applied
            result["audit_ids"] = audit_ids
        elif run["worker_kind"] == "v8_transition_review":
            applied, audit_ids = self._apply_v8_transition_review(run, proposal)
            result["applied"] = applied
            result["audit_ids"] = audit_ids
        self.storage.update_background_intelligence_run(
            run_id,
            status="applied" if result["applied"] else "discarded",
            proposal={**proposal, "apply_result": result},
        )
        self.storage.record_governance_event(
            event_kind="background_run_applied" if result["applied"] else "background_run_discarded",
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            payload=result,
        )
        return result

    def rollback_run(self, run_id: str) -> dict[str, Any]:
        run = self.storage.get_background_intelligence_run(run_id)
        if run is None:
            return {"rolled_back": False, "reason": "missing_run"}
        proposal = dict(run["proposal"])
        apply_result = proposal.get("apply_result", {})
        audit_ids = list(reversed(apply_result.get("audit_ids", [])))
        if not audit_ids:
            return {"rolled_back": False, "reason": "no_audit_entries", "run_id": run_id}
        rollback = RollbackManager(DatabaseManager(self.storage.db_path))
        for audit_id in audit_ids:
            rollback.rollback(audit_id)
        result = {"rolled_back": True, "run_id": run_id, "audit_ids": audit_ids}
        self.storage.update_background_intelligence_run(
            run_id,
            status="discarded",
            proposal={**proposal, "rollback_result": result},
        )
        self.storage.record_governance_event(
            event_kind="background_run_rolled_back",
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            payload=result,
        )
        return result

    def _plan_condensation(self, *, scope_type: str, scope_id: str) -> list[dict[str, Any]]:
        rows = self.storage.fetch_all(
            """
            SELECT subject, COUNT(*) AS count
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND status = 'active' AND subject IS NOT NULL
            GROUP BY subject
            HAVING COUNT(*) > 1
            ORDER BY count DESC, subject ASC
            LIMIT 5
            """,
            (scope_type, scope_id),
        )
        return [
            {
                "worker_kind": "condensation",
                "subject": row["subject"],
                "candidate_count": row["count"],
                "apply_mode": "shadow_only",
            }
            for row in rows
        ]

    def _plan_staleness_review(self, *, scope_type: str, scope_id: str) -> list[dict[str, Any]]:
        rows = self.storage.fetch_all(
            """
            SELECT id, subject, metadata_json
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND status = 'active'
            ORDER BY updated_at ASC
            LIMIT 20
            """,
            (scope_type, scope_id),
        )
        proposals: list[dict[str, Any]] = []
        for row in rows:
            metadata = self.storage._coerce_metadata(row["metadata_json"])
            if metadata.get("memory_state") != "hypothesized":
                continue
            proposals.append(
                {
                    "worker_kind": "staleness_review",
                    "memory_id": row["id"],
                    "subject": row["subject"],
                    "apply_mode": "shadow_only",
                }
            )
        return proposals

    def _plan_graph_repair(self, *, scope_type: str, scope_id: str) -> list[dict[str, Any]]:
        rows = self.storage.fetch_all(
            """
            SELECT id, subject
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND status = 'active' AND subject IS NOT NULL
            ORDER BY activation_score DESC, updated_at DESC
            LIMIT 20
            """,
            (scope_type, scope_id),
        )
        seen_subjects: set[str] = set()
        proposals: list[dict[str, Any]] = []
        for row in rows:
            subject = row["subject"]
            if not subject or subject in seen_subjects:
                continue
            seen_subjects.add(subject)
            proposals.append(
                {
                    "worker_kind": "graph_repair",
                    "subject": subject,
                    "seed_memory_id": row["id"],
                    "apply_mode": "shadow_only",
                }
            )
        return proposals[:5]

    def _plan_v8_transition_review(self, *, scope_type: str, scope_id: str) -> list[dict[str, Any]]:
        if self.signal_provider is None or self.transition_applier is None:
            return []
        rows = self.storage.fetch_all(
            """
            SELECT id, subject
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND status = 'active'
            ORDER BY activation_score DESC, updated_at DESC
            LIMIT 20
            """,
            (scope_type, scope_id),
        )
        proposals: list[dict[str, Any]] = []
        for row in rows:
            signals = self.signal_provider(row["id"])
            gate = signals["transition_gate"]
            if gate["current_state"] == gate["recommended_state"]:
                continue
            proposals.append(
                {
                    "worker_kind": "v8_transition_review",
                    "memory_id": row["id"],
                    "subject": row["subject"],
                    "current_state": gate["current_state"],
                    "recommended_state": gate["recommended_state"],
                    "trust_score": signals["trust_score"],
                    "readiness_score": signals["readiness_score"],
                    "conflict_signal": signals["conflict_signal"],
                    "apply_mode": "shadow_only",
                }
            )
        return proposals[:10]

    def _predict_mutations(self, run: dict[str, Any], proposal: dict[str, Any]) -> int:
        if run["worker_kind"] == "graph_repair":
            subject = proposal.get("subject")
            seed_memory_id = proposal.get("seed_memory_id")
            if not subject or not seed_memory_id:
                return 0
            return len(
                self.storage.find_same_subject_peers(
                    memory_id=seed_memory_id,
                    scope_type=run["scope_type"],
                    scope_id=run["scope_id"],
                    subject=subject,
                    limit=10,
                )
            )
        if run["worker_kind"] == "condensation":
            subject = proposal.get("subject")
            if not subject:
                return 0
            rows = self.storage.fetch_all(
                """
                SELECT id FROM memories
                WHERE scope_type = ? AND scope_id = ? AND status = 'active' AND subject = ?
                """,
                (run["scope_type"], run["scope_id"], subject),
            )
            return max(0, len(rows) - 1)
        if run["worker_kind"] == "staleness_review":
            return 1 if proposal.get("memory_id") else 0
        if run["worker_kind"] == "v8_transition_review":
            return 1 if proposal.get("memory_id") else 0
        return 0

    def _apply_graph_repair(self, run: dict[str, Any], proposal: dict[str, Any]) -> tuple[int, list[str]]:
        subject = proposal.get("subject")
        seed_memory_id = proposal.get("seed_memory_id")
        if not subject or not seed_memory_id:
            return 0, []
        peers = self.storage.find_same_subject_peers(
            memory_id=seed_memory_id,
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            subject=subject,
            limit=10,
        )
        added = 0
        audit_ids: list[str] = []
        for peer in peers:
            link = self.storage.upsert_memory_link(
                source_id=seed_memory_id,
                target_id=peer["id"],
                link_type="same_subject",
                weight=0.65,
                metadata={"auto": True, "worker_kind": "graph_repair", "subject": subject},
            )
            self.storage.record_evidence_artifact(
                artifact_kind="mutation_comparison",
                scope_type=run["scope_type"],
                scope_id=run["scope_id"],
                memory_id=seed_memory_id,
                payload={
                    "mutation_kind": "graph_repair",
                    "before": {"neighbors": []},
                    "after": {"link": link},
                    "run_id": run["id"],
                },
            )
            audit_ids.append(
                self._record_audit(
                    action_type="graph_repair",
                    entity_type="memory_link",
                    entity_id=link["id"],
                    explanation=f"Background graph repair linked same-subject memories for {subject}.",
                    details={"created_link": True, "run_id": run["id"], "previous_state": None},
                )
            )
            added += 1
        return added, audit_ids

    def _apply_condensation(self, run: dict[str, Any], proposal: dict[str, Any]) -> tuple[int, list[str]]:
        subject = proposal.get("subject")
        if not subject:
            return 0, []
        rows = self.storage.fetch_all(
            """
            SELECT *
            FROM memories
            WHERE scope_type = ? AND scope_id = ? AND status = 'active' AND subject = ?
            ORDER BY activation_score DESC, updated_at DESC
            """,
            (run["scope_type"], run["scope_id"], subject),
        )
        if len(rows) < 2:
            return 0, []
        keeper = rows[0]["id"]
        summary_memory = self._build_condensation_summary(run, subject, rows)
        archived = 0
        audit_ids: list[str] = []
        if summary_memory is not None:
            self.storage.put_memory(summary_memory)
            self.storage.record_evidence_artifact(
                artifact_kind="condensation_summary",
                scope_type=run["scope_type"],
                scope_id=run["scope_id"],
                memory_id=summary_memory.id,
                payload={
                    "summary_type": summary_memory.metadata["summary_object"]["summary_type"],
                    "derived_from": [row["id"] for row in rows],
                    "summary_text": summary_memory.content,
                    "summary_object": summary_memory.metadata["summary_object"],
                    "uncertainty": summary_memory.metadata["summary_object"]["uncertainty"],
                },
            )
            self.storage.record_evidence_artifact(
                artifact_kind="mutation_comparison",
                scope_type=run["scope_type"],
                scope_id=run["scope_id"],
                memory_id=summary_memory.id,
                payload={
                    "mutation_kind": "condensation_summary_create",
                    "before": None,
                    "after": {
                        "memory_id": summary_memory.id,
                        "summary_object": summary_memory.metadata["summary_object"],
                    },
                    "run_id": run["id"],
                },
            )
            audit_ids.append(
                self._record_audit(
                    action_type="consolidate",
                    entity_type="memory",
                    entity_id=summary_memory.id,
                    explanation=f"Background condensation created a lineage-preserving summary for {subject}.",
                    details={"created_memory": True, "run_id": run["id"]},
                )
            )
        for row in rows[1:]:
            previous_state = self._row_to_previous_state(row)
            self.storage._transition_memory(
                row["id"],
                status="archived",
                event="archived_by_background_condensation",
                details={"worker_kind": "condensation", "subject": subject, "keeper_id": keeper},
            )
            audit_ids.append(
                self._record_audit(
                    action_type="archive",
                    entity_type="memory",
                    entity_id=row["id"],
                    explanation=f"Background condensation archived duplicate subject memory for {subject}.",
                    details={"previous_state": previous_state, "run_id": run["id"]},
                )
            )
            self.storage.record_evidence_artifact(
                artifact_kind="mutation_comparison",
                scope_type=run["scope_type"],
                scope_id=run["scope_id"],
                memory_id=row["id"],
                payload={
                    "mutation_kind": "condensation_archive",
                    "before": previous_state,
                    "after": {"status": "archived", "keeper_id": keeper},
                    "run_id": run["id"],
                },
            )
            archived += 1
        return archived, audit_ids

    def _apply_staleness_review(self, run: dict[str, Any], proposal: dict[str, Any]) -> tuple[bool, list[str]]:
        memory_id = proposal.get("memory_id")
        if not memory_id:
            return False, []
        row = self.storage.fetch_one("SELECT * FROM memories WHERE id = ?", (memory_id,))
        if row is None:
            return False, []
        previous_state = self._row_to_previous_state(row)
        self.storage._transition_memory(
            memory_id,
            status="superseded",
            event="invalidated_by_background_review",
            details={"worker_kind": "staleness_review"},
        )
        self.storage.record_evidence_artifact(
            artifact_kind="mutation_comparison",
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            memory_id=memory_id,
            payload={
                "mutation_kind": "staleness_review",
                "before": previous_state,
                "after": {"status": "superseded"},
                "run_id": run["id"],
            },
        )
        audit_id = self._record_audit(
            action_type="invalidate",
            entity_type="memory",
            entity_id=memory_id,
            explanation="Background staleness review invalidated a hypothesized memory.",
            details={"previous_state": previous_state, "run_id": run["id"]},
        )
        return True, [audit_id]

    def _apply_v8_transition_review(self, run: dict[str, Any], proposal: dict[str, Any]) -> tuple[bool, list[str]]:
        if self.transition_applier is None:
            return False, []
        memory_id = proposal.get("memory_id")
        if not memory_id:
            return False, []
        row = self.storage.fetch_one("SELECT * FROM memories WHERE id = ?", (memory_id,))
        if row is None:
            return False, []
        previous_state = self._row_to_previous_state(row)
        payload = self.transition_applier(memory_id, actor="background_v8_transition_review")
        if not payload.get("applied"):
            return False, []
        updated = self.storage.fetch_one("SELECT metadata_json, status FROM memories WHERE id = ?", (memory_id,))
        after_metadata = self.storage._coerce_metadata(updated["metadata_json"]) if updated is not None else {}
        self.storage.record_evidence_artifact(
            artifact_kind="mutation_comparison",
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            memory_id=memory_id,
            payload={
                "mutation_kind": "v8_transition_review",
                "before": previous_state,
                "after": {
                    "status": updated["status"] if updated is not None else None,
                    "memory_state": after_metadata.get("memory_state"),
                    "admission_state": after_metadata.get("admission_state"),
                },
                "run_id": run["id"],
                "transition_result": payload,
            },
        )
        audit_id = self._record_audit(
            action_type="transition",
            entity_type="memory",
            entity_id=memory_id,
            explanation="Background v8 transition review applied a governed state transition.",
            details={
                "previous_state": previous_state,
                "run_id": run["id"],
                "from_state": payload.get("from_state"),
                "to_state": payload.get("to_state"),
            },
        )
        return True, [audit_id]

    def _record_audit(
        self,
        *,
        action_type: str,
        entity_type: str,
        entity_id: str,
        explanation: str,
        details: dict[str, Any],
    ) -> str:
        audit_id = str(uuid.uuid4())
        self.storage.execute(
            """
            INSERT INTO autonomous_audit_log (
                id, action_type, entity_type, entity_id, explanation,
                applied_at, status, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, 'applied', ?)
            """,
            (
                audit_id,
                action_type,
                entity_type,
                entity_id,
                explanation,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(details, ensure_ascii=True),
            ),
        )
        return audit_id

    def _build_condensation_summary(self, run: dict[str, Any], subject: str, rows: list[Any]):
        contents = [str(row["content"]).strip() for row in rows if row["content"]]
        if len(contents) < 2:
            return None
        summary_object = self._build_summary_object(subject, contents)
        summary_text = summary_object["summary_text"]
        metadata = {
            "memory_state": "consolidated",
            "admission_state": "consolidated",
            "derived_from": [row["id"] for row in rows],
            "worker_kind": "condensation",
            "lineage": {"derived_from": [row["id"] for row in rows], "preserves_raw_evidence": True},
            "summary_object": summary_object,
            "score_profile": {
                "source_reliability": 0.88,
                "recency": 0.72,
                "specificity": 0.82,
                "directness": 0.78,
                "frequency": 0.68,
                "conflict_pressure": 0.12,
            },
        }
        return self.factory.create(
            type="semantic",
            content=summary_text,
            scope_type=run["scope_type"],
            scope_id=run["scope_id"],
            source_kind="system",
            source_ref=f"background://{run['id']}",
            subject=subject,
            summary=f"Consolidated summary for {subject}",
            metadata=metadata,
            confidence=0.84,
            activation_score=1.05,
        )

    def _build_summary_object(self, subject: str, contents: list[str]) -> dict[str, Any]:
        contexts: list[dict[str, Any]] = []
        exceptions: list[dict[str, Any]] = []
        for content in contents[:6]:
            lowered = content.lower()
            context_label = "default"
            if "morning" in lowered or "buổi sáng" in lowered or "sáng" in lowered:
                context_label = "morning"
            elif "stress" in lowered or "stressed" in lowered or "căng" in lowered:
                context_label = "high_workload"
            elif "work" in lowered or "làm việc" in lowered:
                context_label = "work"
            entry = {"context": context_label, "statement": content}
            if context_label == "default":
                exceptions.append(entry)
            else:
                contexts.append(entry)

        contexts = list({item["statement"]: item for item in contexts}.values())
        exceptions = list({item["statement"]: item for item in exceptions}.values())
        if contexts:
            summary_text = " ".join(item["statement"] for item in contexts[:2])
        else:
            summary_text = " ".join(contents[:2])
        if exceptions:
            summary_text = f"{summary_text} Exceptions: " + " ".join(item["statement"] for item in exceptions[:1])

        summary_type = "preference_summary" if "preference" in subject or "drink" in subject else "condensed_summary"
        return {
            "summary_type": summary_type,
            "entity": subject,
            "contexts": contexts,
            "exceptions": exceptions,
            "summary_text": summary_text,
            "uncertainty": 0.12,
        }

    def _row_to_previous_state(self, row: Any) -> dict[str, Any]:
        payload = dict(row)
        metadata = payload.get("metadata_json")
        if isinstance(metadata, str):
            payload["metadata_json"] = json.loads(metadata)
        elif metadata is None:
            payload["metadata_json"] = {}
        return payload
