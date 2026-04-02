import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
import sqlite3
from .storage.manager import StorageManager
from .memory.ingest import IngestEngine
from .retrieval.search import SearchPipeline
from .retrieval.models import SearchQuery, SearchResult
from .retrieval.contract import ExplainerBeast
from .retrieval.v10_dynamics import (
    LEGACY_V10_DYNAMICS_METADATA_KEY,
    V10_STATE_METADATA_KEY,
    apply_outcome_feedback,
    build_persisted_v10_state,
    bundle_energy_snapshot,
    compute_v10_core_signals,
)
from .hygiene.engine import HygieneEngine
from .preferences.manager import PreferenceManager
from .preferences.extractor import SignalExtractor
from .cognition.core import StyleTracker
from .conflict.core import ConflictManager
from .graph_analysis import summarize_local_graph
from .backup_surface import AegisBackupSurface
from .health_surface import AegisHealthSurface
from .governed_background_surface import AegisGovernedBackgroundSurface
from .operations import AegisOperationalService
from .operator_surface import AegisOperatorSurface
from .sync_surface import AegisSyncSurface
from .surface import (
    build_context_pack,
    build_public_surface,
    normalize_retrieval_mode,
    serialize_conflict_prompt,
    serialize_search_result,
    serialize_search_results,
)
from .spotlight_surface import build_spotlight_response, summarize_spotlight_results
from .core_showcase_surface import build_core_showcase_payload, build_core_showcase_response
from .hygiene.transitions import transition_memory
from .ux.telemetry import AegisTelemetry
from .ux.i18n import get_text
from .ux.health import MemoryHealthSnapshot
from .observability import (
    ObservedOperation,
    get_global_runtime_observability,
)
from .v10_base import (
    GovernedBackgroundIntelligence,
    MemoryStateMachine,
    RetrievalOrchestrator,
    SpecializedStorageSurfaces,
)
from .v10.engine import GovernanceEngineV10
from .v10.truth_registry import TruthRegistryV10
from .v10.models import GovernanceStatus as V10GovernanceStatus, RetrievableMode as V10RetrievableMode

RUNTIME_VERSION = "8.0.0"
DEFAULT_CONSUMER_SCOPE_TYPE = "agent"
DEFAULT_CONSUMER_SCOPE_ID = "default"
DEFAULT_CONSUMER_SOURCE_KIND = "conversation"
DEFAULT_CONSUMER_SOURCE_REF = "consumer://default"

class AegisApp:
    """Unified orchestrator for the Aegis v10 Python runtime."""
    
    def __init__(self, db_path: Optional[str] = None, locale: str = "vi"):
        self.db_path = db_path or os.environ.get("AEGIS_DB_PATH") or os.path.expanduser("~/.openclaw/aegis_v4.db")
        self.telemetry = AegisTelemetry()
        self.locale = locale
        
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._bind_runtime()

    def memory_health_snapshot(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        locale: str | None = None,
    ) -> Dict[str, Any]:
        """Provides a diagnostic snapshot of memory health (6.md compliant)."""
        st, sid = scope_type, scope_id
        if st is None or sid is None:
            st, sid = self._default_consumer_scope()
        
        doctor = MemoryHealthSnapshot(self.storage, locale=locale or self.locale)
        return doctor.diagnose(scope_type=st, scope_id=sid)

    def memory_health_summary(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        locale: str | None = None,
    ) -> str:
        """Returns a formatted human-readable memory health report (Debt 3 Fix)."""
        current_locale = locale or self.locale
        st, sid = scope_type, scope_id
        if st is None or sid is None:
            st, sid = self._default_consumer_scope()

        doctor = MemoryHealthSnapshot(self.storage, locale=current_locale)
        diagnosis = doctor.diagnose(scope_type=st, scope_id=sid)

        h = self._get_honorifics()
        level = diagnosis["health_level"]
        total = diagnosis["total_active"]
        conflicts = diagnosis["num_conflicts"]
        stale = diagnosis["num_stale"]

        # 1. Header & Status
        status_label = get_text(f"health_status_{level}", locale=current_locale)
        lines = [f"## 🩺 Báo cáo Sức khỏe Bộ nhớ: {status_label}", ""]

        # 2. Narrative Summary
        summary = get_text(f"health_summary_{level}", locale=current_locale).format(
            total=total, conflicts=conflicts, stale=stale, **h
        )
        lines.append(summary)
        lines.append("")

        # 3. Detailed Issues & Actions
        if conflicts > 0:
            lines.append(f"⚠️ **{get_text('health_issue_conflict', locale=current_locale).format(count=conflicts)}**")
            lines.append(f"   └─ {get_text('health_action_clean', locale=current_locale)}")

        if stale > 0:
            lines.append(f"📦 **{get_text('health_issue_stale', locale=current_locale).format(count=stale)}**")
            lines.append(f"   └─ {get_text('health_action_archive', locale=current_locale)}")

        if level == "perfect" or level == "good":
            u_label = h.get("h_user", "").strip()
            if u_label:
                lines.append(f"\n🌈 Mọi thứ đang rất tuyệt vời, {u_label} cứ yên tâm làm việc nhé!")
            else:
                lines.append("\n🌈 Mọi thứ đang rất tuyệt vời, cứ yên tâm làm việc nhé!")

        return "\n".join(lines)
    def memory_conflict_prompts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        locale: str | None = None,
    ) -> str:
        """Surfaces proactive conflict resolution prompts (6.md compliant)."""
        current_locale = locale or self.locale
        st, sid = scope_type, scope_id
        if st is None or sid is None:
            st, sid = self._default_consumer_scope()

        prompts = self.conflict_manager.list_resolution_prompts(scope_type=st, scope_id=sid)
        if not prompts:
            return "" 

        honorific = self._get_honorifics().get("h_user", "")
        lines = []

        for p in prompts:
            subject = p.get("subject", "chung")
            mem_a = p["memories"]["older"]
            mem_b = p["memories"]["newer"]

            # Header & Subject
            header = get_text("conflict_prompt_header", locale=current_locale).format(honorific=honorific, subject=subject)
            lines.append(f"### {header}")

            # Reasons (Humanized)
            reason_key = "conflict_reason_contradiction" if p.get("classification") == "user_resolution_required" else "conflict_reason_correction"
            lines.append(f"💡 *{get_text(reason_key, locale=current_locale)}*")

            # Options
            lines.append(f"\n1️⃣ **{get_text('conflict_choice_newer', locale=current_locale).format(time=mem_b['created_at'][:16])}**")
            lines.append(f"   └─ \"{mem_b['content']}\"")
            lines.append(f"\n2️⃣ **{get_text('conflict_choice_older', locale=current_locale).format(time=mem_a['created_at'][:16])}**")
            lines.append(f"   └─ \"{mem_a['content']}\"")

            # Split choice (if applicable)
            if p.get("classification") == "contextual_coexistence":
                lines.append(f"\n3️⃣ **{get_text('conflict_choice_both', locale=current_locale)}**")

            # Footer
            lines.append(f"\n{get_text('conflict_footer', locale=current_locale)}")
            lines.append("\n" + "---" * 5)

        return "\n".join(lines)
    def _bind_runtime(self) -> None:
        from .retrieval.navigator import NavigatorBeast
        from .retrieval.guardian import GuardianBeast
        from .retrieval.oracle import OracleBeast

        self.storage = StorageManager(self.db_path)
        self.search_pipeline = SearchPipeline(self.storage)
        self.ingest_engine = IngestEngine(self.storage, search_pipeline=self.search_pipeline)
        self.hygiene_engine = HygieneEngine(self.storage)
        self.pref_manager = PreferenceManager(self.storage)
        self.pref_extractor = SignalExtractor()
        self.style_tracker = StyleTracker(self.storage)
        self.conflict_manager = ConflictManager(self.storage)
        self.operations = AegisOperationalService(self)
        self.backup_surface = AegisBackupSurface(self)
        self.health_surface = AegisHealthSurface(self)
        self.operator_surface = AegisOperatorSurface(self)
        self.sync_surface = AegisSyncSurface(self)
        self.governed_background_surface = AegisGovernedBackgroundSurface(self)
        self.memory_state_machine = MemoryStateMachine(self.storage)
        self.specialized_storage = SpecializedStorageSurfaces(self.storage)
        self.background_intelligence = GovernedBackgroundIntelligence(
            self.storage,
            signal_provider=self.compute_v10_core_signals,
            transition_applier=self.apply_v10_transition_gate,
        )
        self.retrieval_orchestrator = RetrievalOrchestrator(self.storage, self.search_pipeline)
        self.observability = get_global_runtime_observability()
        
        self.navigator_beast = NavigatorBeast(self.storage)
        self.guardian_beast = GuardianBeast(self.storage)
        self.oracle_beast = OracleBeast(self.storage)
        self.explainer_beast = ExplainerBeast()

        # V10 Governance Engine (Constitutional Memory)
        self.v10_engine = GovernanceEngineV10(self.storage)
        self.v10_truth_registry = TruthRegistryV10(self.storage)

    def put_memory(self, content: str, type: str | None = None, scope_type: str = "session", scope_id: str = "default", session_id: Optional[str] = None, **kwargs):
        """Ingests a memory and extracts style signals."""
        observation = ObservedOperation(
            self.observability,
            tool="put_memory",
            scope_type=scope_type,
            scope_id=scope_id,
            session_id=session_id,
        )
        try:
            mem = self.ingest_engine.ingest(
                content=content,
                type=type,
                scope_type=scope_type,
                scope_id=scope_id,
                session_id=session_id,
                **kwargs
            )

            if session_id:
                signals = self.pref_extractor.extract_signals(content, session_id, scope_id, scope_type)
                for sig in signals:
                    self.storage.put_signal(sig)
                
                # Immediate consolidation for 'Style Learning' UX (Sprint 2)
                if signals:
                    self.pref_manager.consolidate_session(session_id, scope_id, scope_type)

            if mem is not None:
                self._auto_link_same_subject(mem.id)
                self._auto_link_procedural_semantic(mem.id)
                observation.finish(result="success", details={"memory_id": mem.id, "memory_type": mem.type})
                # Telemetry Outcome
                self.telemetry.track_outcome("memory_ingested", {"memory_id": mem.id, "type": mem.type})
            else:
                observation.finish(result="no_op", details={"reason": "ingest_rejected"})
            return mem
        except Exception as exc:
            observation.finish(result="error", error_code=exc.__class__.__name__)
            raise

    def diagnose_ingest_attempt(
        self,
        content: str,
        *,
        type: str | None = None,
        scope_type: str = "session",
        scope_id: str = "default",
        source_kind: str = "message",
        **kwargs,
    ) -> Dict[str, Any]:
        """Explains whether an ingest attempt would admit, deduplicate, or be blocked."""
        engine = self.ingest_engine
        if not engine.filter.is_worthy(content):
            return {
                "outcome": "not_worthy",
                "reason_code": "filtered_not_worthy",
                "reasons": ["filtered_not_worthy"],
                "scope_type": scope_type,
                "scope_id": scope_id,
                "subject": kwargs.get("subject"),
                "promotable": False,
                "target_state": None,
            }

        metadata = dict(kwargs.get("metadata", {}) or {})
        if engine.correction_detector.is_correction(content):
            metadata["is_correction"] = True

        existing_exact = self.storage.fetch_one(
            "SELECT id FROM memories WHERE content = ? AND scope_id = ? AND scope_type = ? LIMIT 1",
            (content, scope_id, scope_type),
        )
        if existing_exact:
            return {
                "outcome": "exact_dedup",
                "reason_code": "exact_content_scope_match",
                "reasons": ["exact_content_scope_match"],
                "scope_type": scope_type,
                "scope_id": scope_id,
                "subject": kwargs.get("subject"),
                "exact_duplicate_id": existing_exact["id"],
                "promotable": True,
                "target_state": "validated",
            }

        resolved_type = type
        if resolved_type is None:
            resolved_type = engine.lane_classifier.infer(
                content=content,
                session_id=kwargs.get("session_id"),
                source_kind=source_kind,
            )

        subject = kwargs.get("subject") or engine.content_extractor.derive_subject(content)
        summary = kwargs.get("summary") or engine.content_extractor.derive_summary(content)
        subject = engine.subject_normalizer.normalize(subject)

        confidence = kwargs.get("confidence")
        activation_score = kwargs.get("activation_score")
        if confidence is None or activation_score is None:
            score_profile = engine.write_time_scorer.build_profile(
                content=content,
                memory_type=resolved_type,
                source_kind=source_kind,
            )
            inferred_confidence, inferred_activation = engine.write_time_scorer.infer(
                content=content,
                memory_type=resolved_type,
                source_kind=source_kind,
            )
            if confidence is None:
                confidence = inferred_confidence
            if activation_score is None:
                activation_score = inferred_activation
        else:
            score_profile = engine.write_time_scorer.build_profile(
                content=content,
                memory_type=resolved_type,
                source_kind=source_kind,
            )

        diagnostic_metadata = dict(metadata)
        diagnostic_metadata["score_profile"] = score_profile
        entities = engine.entity_extractor.extract(content=content, subject=subject)
        if entities:
            diagnostic_metadata["entities"] = entities
        diagnostic_metadata.setdefault(
            "evidence",
            {
                "event_id": "diagnostic://synthetic-evidence",
                "kind": "synthetic_diagnostic",
                "source_kind": source_kind,
                "source_ref": kwargs.get("source_ref"),
                "captured_at": "diagnostic",
            },
        )

        memory = engine.factory.create(
            type=resolved_type,
            content=content,
            scope_type=scope_type,
            scope_id=scope_id,
            source_kind=source_kind,
            metadata=diagnostic_metadata,
            subject=subject,
            summary=summary,
            confidence=confidence,
            activation_score=activation_score,
            session_id=kwargs.get("session_id"),
            source_ref=kwargs.get("source_ref"),
        )
        candidate = engine.build_candidate(memory)
        decision = engine.evaluate_candidate(candidate)
        blocked_reasons = [reason for reason in decision.reasons if reason.startswith("blocked_")]

        return {
            "outcome": "admit" if decision.promotable else "policy_block",
            "reason_code": blocked_reasons[0] if blocked_reasons else "promotion_allowed",
            "reasons": list(decision.reasons),
            "scope_type": scope_type,
            "scope_id": scope_id,
            "subject": subject,
            "promotable": decision.promotable,
            "target_state": decision.target_state,
            "confidence": float(confidence or 0.0),
            "activation_score": float(activation_score or 0.0),
            "contradiction_risk": candidate.contradiction_risk,
            "policy_name": decision.policy_name,
            "score_profile": score_profile,
        }

    def search(
        self,
        query: str,
        scope_id: str,
        scope_type: str = "session",
        limit: int = 10,
        include_global: bool = True,
        semantic: bool = True,
        semantic_model: str | None = None,
        fallback_to_or: bool = False,
    ) -> List[SearchResult]:
        """Search across memories with scoped filtering."""
        observation = ObservedOperation(
            self.observability,
            tool="search",
            scope_type=scope_type,
            scope_id=scope_id,
        )
        s_query = SearchQuery(
            query=query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
            fallback_to_or=fallback_to_or,
        )
        try:
            if semantic:
                results = self.retrieval_orchestrator.retrieve(s_query).results
            else:
                results = self.search_pipeline.search(s_query)
            observation.finish(
                result="success" if results else "empty",
                details={"result_count": len(results), "semantic": semantic},
            )
            # Telemetry Exposure
            self.telemetry.track_exposure("recall_decision_trace", "compact", {
                "query": query,
                "result_count": len(results),
                "has_suppressed": len(results[0].suppressed_candidates) > 0 if results else False
            })
            return results
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__, details={"semantic": semantic})
            raise

    def get_preferences(self, scope_id: str, scope_type: str) -> Optional[Dict[str, Any]]:
        """Retrieves learned style preferences for a scope."""
        profile = self.storage.get_profile(scope_id, scope_type)
        return profile.preferences_json if profile else None

    def reinforce(self, memory_id: str):
        """Manually reinforce a memory's importance."""
        self.storage.reinforce_memory(memory_id)

    def maintenance(self):
        """Run system-wide hygiene."""
        self.hygiene_engine.run_maintenance()

    def clean(self, subject: str | None = None) -> Dict[str, Any]:
        """Run maintenance and optionally scan conflicts for a subject."""
        self.hygiene_engine.run_maintenance()
        conflicts = self.conflict_manager.scan_conflicts(subject) if subject else []
        return {"conflicts_detected": len(conflicts)}

    def doctor(self, workspace_dir: str | None = None) -> Dict[str, Any]:
        """Return a lightweight health report for the Python-owned runtime."""
        return self.health_surface.doctor(workspace_dir=workspace_dir)

    def taxonomy_clean(self) -> Dict[str, Any]:
        """Normalize missing subjects into a stable fallback taxonomy bucket."""
        unlabeled = self.storage.fetch_all(
            """
            SELECT id FROM memories
            WHERE status = 'active' AND (subject IS NULL OR TRIM(subject) = '')
            """
        )
        migrated = 0
        for row in unlabeled:
            self.storage.execute(
                "UPDATE memories SET subject = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                ("general.untagged", row["id"]),
            )
            migrated += 1

        stats_rows = self.storage.fetch_all(
            """
            SELECT COALESCE(subject, '(unlabeled)') AS subject, COUNT(*) AS count
            FROM memories
            WHERE status = 'active'
            GROUP BY COALESCE(subject, '(unlabeled)')
            ORDER BY count DESC
            """
        )
        return {
            "backend": "python",
            "migrated": migrated,
            "taxonomy": [dict(row) for row in stats_rows],
        }

    def rebuild(self) -> Dict[str, Any]:
        """Run a conservative non-destructive rebuild/backfill pass."""
        before = self.storage.fetch_one("SELECT COUNT(*) AS count FROM conflicts")
        links_before = self.storage.count_links_by_type(link_type="same_subject")
        typed_links_before = self.storage.count_links_by_type(link_type="procedural_supports_semantic")

        # Rebuild should harden derived fields and restore bounded structure without
        # merging or superseding memories as a side effect.
        self.storage.archive_expired()
        evidence_backfilled = self._backfill_missing_evidence()
        derived_hardened = self._backfill_missing_derived_fields()
        self._scan_active_subject_conflicts()
        linked = self._backfill_same_subject_links()
        typed_linked = self._backfill_procedural_semantic_links()
        after = self.storage.fetch_one("SELECT COUNT(*) AS count FROM conflicts")
        links_after = self.storage.count_links_by_type(link_type="same_subject")
        typed_links_after = self.storage.count_links_by_type(link_type="procedural_supports_semantic")
        return {
            "backend": "python",
            "rebuilt": True,
            "conflicts_before": before["count"] if before else 0,
            "conflicts_after": after["count"] if after else 0,
            "evidence_backfilled": evidence_backfilled,
            "derived_fields_hardened": derived_hardened,
            "same_subject_links_before": links_before,
            "same_subject_links_after": links_after,
            "same_subject_links_added": linked,
            "procedural_semantic_links_before": typed_links_before,
            "procedural_semantic_links_after": typed_links_after,
            "procedural_semantic_links_added": typed_linked,
        }

    def scan(self) -> Dict[str, Any]:
        """Scan all active subjects for conflicts through the Python runtime."""
        scanned, conflicts_detected, touched = self._scan_active_subject_conflicts()
        prompts = self.conflict_manager.list_resolution_prompts()
        return {
            "backend": "python",
            "subjects_scanned": scanned,
            "conflicts_detected": conflicts_detected,
            "conflict_subjects": touched,
            "resolution_prompt_count": len(prompts),
        }

    def plan_background_intelligence(
        self,
        *,
        scope_type: str,
        scope_id: str,
    ) -> dict[str, Any]:
        return self.governed_background_surface.plan_background_intelligence(
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def apply_background_intelligence_run(self, run_id: str, *, max_mutations: int = 5) -> dict[str, Any]:
        return self.governed_background_surface.apply_background_intelligence_run(
            run_id,
            max_mutations=max_mutations,
        )

    def shadow_background_intelligence_run(self, run_id: str) -> dict[str, Any]:
        return self.governed_background_surface.shadow_background_intelligence_run(run_id)

    def rollback_background_intelligence_run(self, run_id: str) -> dict[str, Any]:
        return self.governed_background_surface.rollback_background_intelligence_run(run_id)

    def inspect_vector_store(
        self,
        *,
        query: str,
        scope_type: str,
        scope_id: str,
        include_global: bool = False,
        limit: int = 10,
    ) -> dict[str, Any]:
        matches = self.specialized_storage.search_vector_store(
            query=query,
            scope_type=scope_type,
            scope_id=scope_id,
            include_global=include_global,
            limit=limit,
        )
        return {
            "backend": "python",
            "query": query,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "matches": matches,
        }

    def inspect_governance(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return self.operator_surface.inspect_governance(
            scope_type=scope_type,
            scope_id=scope_id,
            memory_id=memory_id,
            limit=limit,
        )

    def evidence_artifacts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        return self.operator_surface.evidence_artifacts(
            scope_type=scope_type,
            scope_id=scope_id,
            memory_id=memory_id,
            limit=limit,
        )

    def conflict_resolution_prompts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        subject: str | None = None,
    ) -> dict[str, Any]:
        prompts = self.conflict_manager.list_resolution_prompts(
            scope_type=scope_type,
            scope_id=scope_id,
            subject=subject,
        )
        return {
            "backend": "python",
            "count": len(prompts),
            "prompts": [serialize_conflict_prompt(prompt) for prompt in prompts],
        }

    def resolve_conflict(
        self,
        conflict_id: str,
        *,
        action: str,
        rationale: str | None = None,
    ) -> dict[str, Any]:
        result = self.conflict_manager.resolve_with_user_decision(
            conflict_id,
            action=action,
            rationale=rationale,
        )
        return {"backend": "python", **result}

    def _scan_active_subject_conflicts(self) -> tuple[int, int, list[str]]:
        """Scan all active subjects without applying destructive maintenance."""
        subjects = self.storage.fetch_all(
            """
            SELECT DISTINCT subject
            FROM memories
            WHERE status = 'active' AND subject IS NOT NULL AND TRIM(subject) != ''
            """
        )
        scanned = 0
        conflicts_detected = 0
        touched: list[str] = []
        for row in subjects:
            subject = row["subject"]
            scanned += 1
            conflicts = self.conflict_manager.scan_conflicts(subject)
            if conflicts:
                conflicts_detected += len(conflicts)
                touched.append(subject)
        return scanned, conflicts_detected, touched

    def visualize(self, limit: int = 1000, *, include_analysis: bool = False) -> Dict[str, Any]:
        """Return a compact graph snapshot built from Python-owned storage."""
        nodes = self.storage.fetch_all(
            """
            SELECT id, type, status, subject, content, activation_score
            FROM memories
            WHERE status IN ('active', 'superseded')
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        node_ids = {row["id"] for row in nodes}
        conflicts = self.storage.fetch_all(
            """
            SELECT memory_a_id, memory_b_id, subject_key, status
            FROM conflicts
            WHERE status IN ('open', 'suggested', 'resolved')
            """
        )
        explicit_links = self.storage.fetch_all(
            """
            SELECT source_id, target_id, link_type, weight
            FROM memory_links
            """
        )
        payload = {
            "backend": "python",
            "graph_boundary": {
                "source_of_truth": "sqlite_memory_links",
                "analysis_mode": "local_only_optional",
                "authoritative_analysis": False,
                "graph_database": None,
            },
            "nodes": [
                {
                    "id": row["id"],
                    "label": (row["content"] or "")[:50],
                    "subject": row["subject"],
                    "type": row["type"],
                    "status": row["status"],
                    "importance": row["activation_score"],
                }
                for row in nodes
            ],
            "links": [
                {
                    "source": row["memory_a_id"],
                    "target": row["memory_b_id"],
                    "type": "contradiction",
                    "subject": row["subject_key"],
                    "status": row["status"],
                }
                for row in conflicts
                if row["memory_a_id"] in node_ids and row["memory_b_id"] in node_ids
            ]
            + [
                {
                    "source": row["source_id"],
                    "target": row["target_id"],
                    "type": row["link_type"],
                    "weight": row["weight"],
                    "status": "explicit_link",
                }
                for row in explicit_links
                if row["source_id"] in node_ids and row["target_id"] in node_ids
            ],
        }
        if include_analysis:
            payload["analysis"] = summarize_local_graph(
                nodes=payload["nodes"],
                links=payload["links"],
            )
        return payload

    def end_session(self, session_id: str, scope_id: str, scope_type: str):
        """Clean up session working memory and consolidate preferences."""
        self.hygiene_engine.on_session_end(session_id)
        self.pref_manager.consolidate_session(session_id, scope_id, scope_type)

    def status(self) -> Dict[str, Any]:
        """Return engine status and high-level counters."""
        return self.health_surface.status()

    def storage_footprint(self) -> dict[str, Any]:
        return self.operator_surface.storage_footprint()

    def _safe_storage_footprint(self) -> dict[str, Any]:
        return self.health_surface.safe_storage_footprint()

    def storage_compaction_policy(self) -> dict[str, int]:
        return self.operator_surface.storage_compaction_policy()

    def compact_storage(
        self,
        *,
        archived_memory_days: int = 30,
        superseded_memory_days: int = 14,
        evidence_days: int = 30,
        governance_days: int = 30,
        replication_days: int = 14,
        background_days: int = 14,
        vacuum: bool = True,
    ) -> dict[str, Any]:
        return self.operator_surface.compact_storage(
            archived_memory_days=archived_memory_days,
            superseded_memory_days=superseded_memory_days,
            evidence_days=evidence_days,
            governance_days=governance_days,
            replication_days=replication_days,
            background_days=background_days,
            vacuum=vacuum,
        )

    def get_memory_evidence(self, memory_id: str) -> list[dict[str, Any]]:
        return self.operator_surface.get_memory_evidence(memory_id)

    def evidence_coverage(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> Dict[str, Any]:
        return self.storage.summarize_evidence_coverage(
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def memory_state(self, memory_id: str) -> Dict[str, Any] | None:
        return self.storage.get_memory_state(memory_id)

    def memory_state_summary(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> Dict[str, Any]:
        return self.storage.summarize_memory_states(
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def v10_field_snapshot(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> Dict[str, Any]:
        return self.operator_surface.v10_field_snapshot(
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def compute_v10_core_signals(self, memory_id: str) -> Dict[str, Any]:
        memory = self.storage.get_memory(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found: {memory_id}")
        evidence = self.storage.get_linked_evidence_for_memory(memory_id)
        neighbors = self.storage.list_memory_neighbors(memory_id=memory_id, limit=20)
        open_conflicts = self.storage.get_open_conflict_peers(memory_id)

        support_weight = 0.0
        support_contributors: list[dict[str, Any]] = []
        for neighbor in neighbors:
            link = neighbor["link"]
            if str(link.get("link_type")) in {"same_subject", "supports", "extends", "procedural_supports_semantic"}:
                weight = float(link.get("weight", 0.0) or 0.0)
                support_weight += max(0.0, weight)
                support_contributors.append(
                    {
                        "memory_id": neighbor["memory"]["id"],
                        "weight": round(max(0.0, weight), 6),
                        "link_type": link.get("link_type"),
                        "reason": "support_link",
                    }
                )

        conflict_weight = 0.0
        conflict_contributors: list[dict[str, Any]] = []
        for item in open_conflicts:
            peer = self.storage.get_memory(item["peer_id"])
            if peer is None:
                continue
            peer_weight = max(0.0, float(peer.confidence or 0.0))
            conflict_weight += peer_weight
            conflict_contributors.append(
                {
                    "memory_id": peer.id,
                    "weight": round(peer_weight, 6),
                    "reason": item.get("reason"),
                    "conflict_score": round(float(item.get("score", 0.0) or 0.0), 6),
                    "subject_key": item.get("subject_key"),
                }
            )

        admission_state = self.storage.get_memory_state(memory_id)
        current_state = admission_state["memory_state"] if admission_state else memory.status

        signals = compute_v10_core_signals(
            row={
                "confidence": memory.confidence,
                "activation_score": memory.activation_score,
                "access_count": memory.access_count,
                "metadata": memory.metadata,
            },
            admission_state=current_state,
            evidence_count=len(evidence),
            support_weight=support_weight,
            conflict_weight=conflict_weight,
            direct_conflict_open=bool(open_conflicts),
        )
        interaction_inputs = {
            "support": {
                "aggregate_weight": round(max(0.0, support_weight), 6),
                "contributors": support_contributors,
            },
            "conflict": {
                "aggregate_weight": round(max(0.0, conflict_weight), 6),
                "contributors": conflict_contributors,
                "direct_conflict_open": bool(open_conflicts),
            },
        }
        signals["interaction_inputs"] = interaction_inputs
        signals["derived_state"]["interaction_inputs"] = interaction_inputs
        return signals

    def _list_field_snapshot_memory_ids(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> list[str]:
        where = []
        params: list[Any] = []
        if scope_type is not None:
            where.append("scope_type = ?")
            params.append(scope_type)
        if scope_id is not None:
            where.append("scope_id = ?")
            params.append(scope_id)
        where.append("status IN ('active', 'crystallized', 'archived', 'superseded')")
        where_sql = " AND ".join(where)
        rows = self.storage.fetch_all(
            f"SELECT id FROM memories WHERE {where_sql} ORDER BY updated_at DESC",
            tuple(params),
        )
        return [str(row["id"]) for row in rows]

    def v10_core_signals(self, memory_id: str) -> Dict[str, Any]:
        return self.operator_surface.v10_core_signals(memory_id)

    def evaluate_v10_transition_operator(self, memory_id: str) -> Dict[str, Any]:
        memory = self.storage.get_memory(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found: {memory_id}")
        signals = self.compute_v10_core_signals(memory_id)
        gate = signals["transition_gate"]
        current_state = gate["current_state"]
        target_state = gate["recommended_state"]
        if current_state == target_state:
            recommended_action = "hold"
        elif target_state == "validated":
            recommended_action = "promote"
        elif target_state == "hypothesized":
            recommended_action = "demote"
        else:
            recommended_action = "transition"
        return {
            "backend": "python",
            "memory_id": memory_id,
            "scope_type": memory.scope_type,
            "scope_id": memory.scope_id,
            "inputs": {
                "current_state": current_state,
                "trust_score": signals["trust_score"],
                "evidence_signal": signals["evidence_signal"],
                "conflict_signal": signals["conflict_signal"],
                "usage_signal": signals["usage_signal"],
                "readiness_score": signals["readiness_score"],
            },
            "decision": {
                "recommended_state": target_state,
                "recommended_action": recommended_action,
                "promote_ready": gate["promote_ready"],
                "demote_ready": gate["demote_ready"],
            },
            "thresholds": gate["thresholds"],
            "signals": signals,
            "transition_gate": gate,
        }

    def v10_transition_gate(self, memory_id: str) -> Dict[str, Any]:
        return self.operator_surface.v10_transition_gate(memory_id)

    def apply_v10_outcome_feedback(
        self,
        memory_id: str,
        *,
        success_score: float,
        relevance_score: float | None = None,
        override_score: float = 0.0,
        actor: str = "v10_feedback",
    ) -> Dict[str, Any]:
        memory = self.storage.get_memory(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found: {memory_id}")
        relevance = float(success_score if relevance_score is None else relevance_score)
        signals = self.compute_v10_core_signals(memory_id)
        updated = apply_outcome_feedback(
            row={
                "confidence": memory.confidence,
                "activation_score": memory.activation_score,
                "access_count": memory.access_count,
                "metadata": memory.metadata,
            },
            evidence_signal=signals["evidence_signal"],
            support_signal=signals["support_signal"],
            conflict_signal=signals["conflict_signal"],
            success_score=float(success_score),
            relevance_score=relevance,
            override_score=float(override_score),
        )
        last_feedback_at = self.memory_state_machine._now()
        metadata = dict(memory.metadata)
        metadata[V10_STATE_METADATA_KEY] = {
            **metadata.get(V10_STATE_METADATA_KEY, {}),
            **updated,
            "last_feedback_at": last_feedback_at,
        }
        persisted_signals = compute_v10_core_signals(
            row={
                "confidence": updated["belief_score"],
                "activation_score": memory.activation_score,
                "access_count": memory.access_count,
                "metadata": metadata,
            },
            admission_state=signals["admission_state"],
            evidence_count=signals["evidence_count"],
            support_weight=signals["support_weight"],
            conflict_weight=signals["conflict_weight"],
            direct_conflict_open=signals["direct_conflict_open"],
        )
        persisted_state = build_persisted_v10_state(
            signals=persisted_signals,
            feedback_count=updated["feedback_count"],
            belief_delta=updated["belief_delta"],
            last_feedback_at=last_feedback_at,
        )
        metadata[V10_STATE_METADATA_KEY] = persisted_state
        metadata[LEGACY_V10_DYNAMICS_METADATA_KEY] = {
            **updated,
            "last_feedback_at": last_feedback_at,
        }
        self.storage.execute(
            "UPDATE memories SET metadata_json = ?, confidence = ?, updated_at = ? WHERE id = ?",
            (
                json.dumps(metadata, ensure_ascii=True),
                updated["belief_score"],
                last_feedback_at,
                memory_id,
            ),
        )
        artifact_id = self.storage.record_evidence_artifact(
            artifact_kind="v10_outcome_feedback",
            scope_type=memory.scope_type,
            scope_id=memory.scope_id,
            memory_id=memory_id,
            payload={
                "actor": actor,
                "success_score": round(float(success_score), 6),
                "relevance_score": round(relevance, 6),
                "override_score": round(float(override_score), 6),
                "updated_dynamics": updated,
            },
        )
        self.storage.record_governance_event(
            event_kind="v10_outcome_feedback_applied",
            scope_type=memory.scope_type,
            scope_id=memory.scope_id,
            memory_id=memory_id,
            payload={
                "actor": actor,
                "artifact_id": artifact_id,
                "updated_dynamics": updated,
            },
        )
        return {
            "backend": "python",
            "memory_id": memory_id,
            "artifact_id": artifact_id,
            "updated_dynamics": updated,
            "signals": self.compute_v10_core_signals(memory_id),
        }

    def apply_v10_retrieval_feedback(
        self,
        *,
        query: str,
        scope_id: str,
        scope_type: str = "session",
        success_score: float,
        selected_memory_ids: list[str] | None = None,
        override_memory_ids: list[str] | None = None,
        limit: int = 5,
        include_global: bool = True,
        actor: str = "v10_bundle_feedback",
    ) -> Dict[str, Any]:
        results = self.search(
            query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
        )
        before_snapshot = bundle_energy_snapshot([
            dict(result.v10_core_signals or {})
            for result in results
            if result.v10_core_signals is not None
        ])
        selected = set(selected_memory_ids or [])
        overridden = set(override_memory_ids or [])
        if not results:
            return {
                "backend": "python",
                "query": query,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "applied": False,
                "reason": "no_results",
                "assignments": [],
                "before_snapshot": before_snapshot,
                "after_snapshot": before_snapshot,
            }

        base_weights: list[float] = []
        for index, result in enumerate(results):
            weight = 1.0 / float(index + 1)
            if result.memory.id in selected:
                weight *= 1.75
            if result.memory.id in overridden:
                weight *= 0.35
            base_weights.append(weight)
        total_weight = sum(base_weights) or 1.0

        assignments: list[dict[str, Any]] = []
        for result, weight in zip(results, base_weights):
            contribution = round(weight / total_weight, 6)
            relevance_score = contribution
            if result.memory.id in selected:
                relevance_score = max(relevance_score, 0.9)
            override_score = 0.0
            if result.memory.id in overridden:
                override_score = 0.9
            elif selected and result.memory.id not in selected:
                override_score = round(min(0.65, (1.0 - contribution) * 0.45), 6)
            memory_success = round(float(success_score) * contribution, 6)
            feedback = self.apply_v10_outcome_feedback(
                result.memory.id,
                success_score=memory_success,
                relevance_score=relevance_score,
                override_score=override_score,
                actor=actor,
            )
            assignments.append(
                {
                    "memory_id": result.memory.id,
                    "score": result.score,
                    "contribution_weight": contribution,
                    "memory_success_score": memory_success,
                    "relevance_score": round(relevance_score, 6),
                    "override_score": override_score,
                    "feedback": feedback["updated_dynamics"],
                }
            )

        artifact_id = self.storage.record_evidence_artifact(
            artifact_kind="v10_retrieval_feedback_bundle",
            scope_type=scope_type,
            scope_id=scope_id,
            payload={
                "actor": actor,
                "query": query,
                "success_score": round(float(success_score), 6),
                "selected_memory_ids": sorted(selected),
                "override_memory_ids": sorted(overridden),
                "assignments": assignments,
            },
        )
        self.storage.record_governance_event(
            event_kind="v10_retrieval_feedback_applied",
            scope_type=scope_type,
            scope_id=scope_id,
            payload={
                "actor": actor,
                "artifact_id": artifact_id,
                "query": query,
                "assignment_count": len(assignments),
            },
        )
        updated_results = self.search(
            query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
        )
        after_snapshot = bundle_energy_snapshot([
            dict(result.v10_core_signals or {})
            for result in updated_results
            if result.v10_core_signals is not None
        ])
        return {
            "backend": "python",
            "query": query,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "applied": True,
            "artifact_id": artifact_id,
            "before_snapshot": before_snapshot,
            "after_snapshot": after_snapshot,
            "assignments": assignments,
        }

    def v10_bundle_snapshot(
        self,
        *,
        query: str,
        scope_id: str,
        scope_type: str = "session",
        limit: int = 5,
        include_global: bool = True,
    ) -> Dict[str, Any]:
        results = self.search(
            query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
        )
        snapshot = bundle_energy_snapshot([
            dict(result.v10_core_signals or {})
            for result in results
            if result.v10_core_signals is not None
        ])
        return {
            "backend": "python",
            "query": query,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "snapshot": snapshot,
            "memory_ids": [result.memory.id for result in results],
        }

    def apply_v10_transition_gate(self, memory_id: str, *, actor: str = "v10_core") -> Dict[str, Any]:
        operator = self.evaluate_v10_transition_operator(memory_id)
        signals = operator["signals"]
        gate = operator["transition_gate"]
        current_state = operator["inputs"]["current_state"]
        target_state = operator["decision"]["recommended_state"]
        if current_state == target_state:
            return {
                "backend": "python",
                "memory_id": memory_id,
                "applied": False,
                "reason": "no_transition_recommended",
                "from_state": current_state,
                "to_state": target_state,
                "transition_operator": operator,
                "signals": signals,
                "transition_gate": gate,
            }

        applied = self.memory_state_machine.transition(
            memory_id=memory_id,
            to_state=target_state,
            reason="v10_core_transition_gate",
            actor=actor,
            details={
                "trust_score": signals["trust_score"],
                "evidence_signal": signals["evidence_signal"],
                "conflict_signal": signals["conflict_signal"],
                "usage_signal": signals["usage_signal"],
                "readiness_score": signals["readiness_score"],
                "thresholds": gate["thresholds"],
            },
        )
        return {
            "backend": "python",
            "memory_id": memory_id,
            "applied": applied,
            "reason": "transition_applied" if applied else "transition_blocked",
            "from_state": current_state,
            "to_state": target_state,
            "transition_operator": operator,
            "post_transition_operator": self.evaluate_v10_transition_operator(memory_id),
            "signals": self.compute_v10_core_signals(memory_id),
            "transition_gate": gate,
        }

    def public_surface(self) -> Dict[str, Any]:
        """Describe the stable host-facing contract owned by the Python runtime."""
        return build_public_surface(runtime_version=RUNTIME_VERSION)

    def _runtime_health_snapshot(self, workspace_dir: Path | None = None) -> Dict[str, Any]:
        issues: list[dict[str, Any]] = []
        db_exists = self.db_path == ":memory:" or Path(self.db_path).expanduser().exists()
        effective_workspace = workspace_dir if workspace_dir is not None else Path(self.db_path).expanduser().parent
        workspace_writable = False

        try:
            effective_workspace.mkdir(parents=True, exist_ok=True)
            probe = effective_workspace / ".aegis_doctor_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            workspace_writable = True
        except OSError:
            issues.append(
                {
                    "code": "workspace_not_writable",
                    "severity": "warn",
                    "details": {"workspace": str(effective_workspace)},
                }
            )

        state = "HEALTHY"
        capabilities = {
            "local_store": True,
            "local_search": True,
            "local_status": True,
            "backup_restore": workspace_writable,
            "optional_sync": True,
        }

        if not db_exists:
            state = "BROKEN"
            capabilities["local_store"] = False
            capabilities["local_search"] = False
            capabilities["local_status"] = True
            capabilities["backup_restore"] = False
            issues.append(
                {
                    "code": "database_missing",
                    "severity": "error",
                    "details": {"db_path": self.db_path},
                }
            )
        else:
            try:
                self.storage.fetch_one("SELECT 1 AS ok")
            except sqlite3.Error as exc:
                state = "BROKEN"
                capabilities["local_store"] = False
                capabilities["local_search"] = False
                capabilities["backup_restore"] = False
                issues.append(
                    {
                        "code": "local_storage_unavailable",
                        "severity": "error",
                        "details": {"error": str(exc)},
                    }
                )

        if state != "BROKEN":
            try:
                policies = self.storage.list_scope_policies()
            except sqlite3.Error as exc:
                state = "BROKEN"
                capabilities["local_store"] = False
                capabilities["local_search"] = False
                capabilities["backup_restore"] = False
                issues.append(
                    {
                        "code": "local_storage_unavailable",
                        "severity": "error",
                        "details": {"error": str(exc)},
                    }
                )
            else:
                degraded_sync = [
                    {
                        "scope_type": policy["scope_type"],
                        "scope_id": policy["scope_id"],
                        "sync_state": policy["sync_state"],
                    }
                    for policy in policies
                    if policy.get("sync_state") in {"pending_sync", "sync_error"}
                ]
                if degraded_sync:
                    state = "DEGRADED_SYNC"
                    capabilities["optional_sync"] = False
                    issues.append(
                        {
                            "code": "sync_degraded",
                            "severity": "warn",
                            "details": {"scopes": degraded_sync},
                        }
                    )

        return {
            "state": state,
            "issues": issues,
            "capabilities": capabilities,
            "database_exists": db_exists,
            "workspace_writable": workspace_writable,
        }

    def _safe_count(self, query: str) -> int:
        try:
            row = self.storage.fetch_one(query)
        except Exception:
            return 0
        if not row:
            return 0
        # Try 'count' key, fallback to first value in row
        try:
            return row["count"]
        except (KeyError, IndexError, TypeError):
            try:
                # If it's a dict-like row (sqlite3.Row), values() might work or just indexing
                return list(row.values())[0] if hasattr(row, "values") else row[0]
            except (IndexError, TypeError):
                return 0

    def set_scope_policy(
        self,
        scope_type: str,
        scope_id: str,
        *,
        sync_policy: str,
        sync_state: str = "local",
        last_sync_at: str | None = None,
    ) -> dict[str, Any]:
        """Persist sync classification for a scope while keeping local-first defaults."""
        return self.sync_surface.set_scope_policy(
            scope_type,
            scope_id,
            sync_policy=sync_policy,
            sync_state=sync_state,
            last_sync_at=last_sync_at,
        )

    def get_scope_policy(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        sync_policy: str | None = None,
    ) -> dict[str, Any]:
        """Inspect effective sync policy without requiring any remote backend."""
        return self.sync_surface.get_scope_policy(
            scope_type=scope_type,
            scope_id=scope_id,
            sync_policy=sync_policy,
        )

    def export_sync_envelope(
        self,
        *,
        scope_type: str,
        scope_id: str,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        return self.sync_surface.export_sync_envelope(
            scope_type=scope_type,
            scope_id=scope_id,
            workspace_dir=workspace_dir,
        )

    def preview_sync_envelope(self, envelope_path: str) -> dict[str, Any]:
        return self.sync_surface.preview_sync_envelope(envelope_path)

    def import_sync_envelope(self, envelope_path: str) -> dict[str, Any]:
        return self.sync_surface.import_sync_envelope(envelope_path)

    def search_payload(
        self,
        query: str,
        scope_id: str | None = None,
        scope_type: str | None = None,
        limit: int = 10,
        include_global: bool = True,
        semantic: bool = True,
        semantic_model: str | None = None,
        retrieval_mode: str = "explain",
    ) -> list[dict[str, Any]]:
        """Return retrieval results as a stable integration payload.
        
        V10: Results are now filtered through the Governance Engine (Constitutional Memory).
        Superseded memories are blocked. Quarantined memories are excluded from normal recall.
        """
        mode = normalize_retrieval_mode(retrieval_mode)
        scope_type, scope_id = self._normalize_retrieval_scope_pair(
            scope_type=scope_type,
            scope_id=scope_id,
        )
        results = self.search(
            query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
        )
        
        # V10 Governance Filter: Apply Constitutional Policy to each result
        governed_results = []
        for r in results:
            try:
                decision = self.v10_engine.govern(
                    r.memory,
                    query_signals={"query": query, "score": r.score},
                    intent="normal_recall"
                )
                # Attach decision to result for downstream serialization
                r.v10_decision = decision
                
                # Only include admissible results in normal recall
                if decision.admissible and decision.retrievable_mode == V10RetrievableMode.NORMAL:
                    governed_results.append(r)
                elif decision.retrievable_mode in (V10RetrievableMode.AUDIT, V10RetrievableMode.CONFLICT_PROBE):
                    # Move to suppressed candidates for transparency
                    reason_text = ", ".join(decision.decision_reason) or "Chặn bởi Policy"
                    if governed_results:
                        governed_results[0].suppressed_candidates.append({
                            "id": r.memory.id,
                            "content": r.memory.content[:80],
                            "reason": reason_text,
                            "score": r.score,
                        })
                else:
                    # Silently excluded (REVOKED, etc.)
                    governed_results.append(r)  # Still include but let serialization handle status
            except Exception:
                # If governance fails, fall back to including the result as-is
                governed_results.append(r)
        
        return self.serialize_search_results(governed_results or results, retrieval_mode=mode)

    def _build_scope_boundary_contract(
        self,
        *,
        scope_type: str,
        scope_id: str,
        include_global: bool,
    ) -> dict[str, Any]:
        return {
            "requested_scope": {"scope_type": scope_type, "scope_id": scope_id},
            "exact_scope_locked": True,
            "global_fallback_enabled": include_global,
            "cross_scope_expansion_allowed": False,
        }

    def _normalize_retrieval_scope_pair(
        self,
        *,
        scope_type: str | None,
        scope_id: str | None,
    ) -> tuple[str, str]:
        if scope_type is None and scope_id is None:
            return "session", "default"
        if (scope_type is None) != (scope_id is None):
            raise ValueError("scope_type and scope_id must both be provided for retrieval scopes.")
        return scope_type, scope_id

    def _default_consumer_scope(self) -> tuple[str, str]:
        return DEFAULT_CONSUMER_SCOPE_TYPE, DEFAULT_CONSUMER_SCOPE_ID

    def _consumer_scope_candidates(self) -> list[tuple[str, str]]:
        primary = self._default_consumer_scope()
        legacy = ("session", "default")
        if primary == legacy:
            return [primary]
        return [primary, legacy]

    def _default_consumer_provenance(self) -> tuple[str, str]:
        return DEFAULT_CONSUMER_SOURCE_KIND, DEFAULT_CONSUMER_SOURCE_REF

    def _run_guided_hygiene_cycle(
        self,
        *,
        subject: str | None = None,
        aggressive: bool = False,
    ) -> dict[str, Any]:
        report: dict[str, Any] = {
            "triggered": True,
            "mode": "aggressive" if aggressive else "light",
            "subject": subject,
        }
        if aggressive:
            self.maintenance()
            report["maintenance"] = "full"
            return report
        conflicts_detected = 0
        if subject:
            conflicts = self.conflict_manager.scan_conflicts(subject)
            conflicts_detected = len(conflicts)
        report["maintenance"] = "light"
        report["conflicts_detected"] = conflicts_detected
        return report

    def search_context_pack(
        self,
        query: str,
        scope_id: str | None = None,
        scope_type: str | None = None,
        limit: int = 5,
        include_global: bool = True,
        semantic: bool = False,
        semantic_model: str | None = None,
    ) -> dict[str, Any]:
        """Return an explainable context pack for external host models."""
        scope_type, scope_id = self._normalize_retrieval_scope_pair(
            scope_type=scope_type,
            scope_id=scope_id,
        )
        results = self._search_expanded_context(
            query=query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
        )
        return build_context_pack(
            query=query,
            scope_type=scope_type,
            scope_id=scope_id,
            results=results,
            boundary=self._build_scope_boundary_contract(
                scope_type=scope_type,
                scope_id=scope_id,
                include_global=include_global,
            ),
        )

    def _search_expanded_context(
        self,
        *,
        query: str,
        scope_id: str,
        scope_type: str,
        limit: int,
        include_global: bool,
        semantic: bool,
        semantic_model: str | None,
    ) -> List[SearchResult]:
        search_query = SearchQuery(
            query=query,
            scope_id=scope_id,
            scope_type=scope_type,
            limit=limit,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
        )
        return self.retrieval_orchestrator.retrieve(search_query).results

    def link_memories(
        self,
        source_id: str,
        target_id: str,
        *,
        link_type: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "backend": "python",
            "stored": True,
            "link": self.storage.upsert_memory_link(
                source_id=source_id,
                target_id=target_id,
                link_type=link_type,
                weight=weight,
                metadata=metadata,
            ),
        }

    def memory_neighbors(self, memory_id: str, *, limit: int = 10) -> dict[str, Any]:
        return self.operator_surface.memory_neighbors(memory_id, limit=limit)

    def export_memories(self, format_type: str = "json") -> str:
        """Export active memories in a compact machine or human-readable format."""
        rows = self.storage.fetch_all("SELECT * FROM memories WHERE status = 'active' ORDER BY created_at ASC")
        memories_list = [dict(row) for row in rows]
        if format_type.lower() == "json":
            return json.dumps(memories_list, indent=2, ensure_ascii=False)
        if format_type.lower() == "markdown":
            parts = ["# Aegis Memory Export", ""]
            for item in memories_list:
                parts.append(f"## [{item['type']}] {item['subject'] or 'General'}")
                parts.append(item["content"])
                parts.append("")
            return "\n".join(parts)
        return f"Error: Unsupported format {format_type}"

    def render_profile(self, scope_id: str | None = None, scope_type: str | None = None) -> str:
        """Returns a human-readable summary of what Aegis knows about the user/scope."""
        if scope_id is None and scope_type is None:
            scope_type, scope_id = self._default_consumer_scope()
        elif scope_id is not None and scope_type is None:
            scope_type = "session"
        elif scope_id is None and scope_type is not None:
            raise ValueError("scope_type and scope_id must both be provided for profiles.")
        prefs = self.get_preferences(scope_id, scope_type)
        
        # 1. Fetch recent important facts (top activation)
        search_res = self.search("", scope_id=scope_id, scope_type=scope_type, limit=5)
        
        lines = [f"## Memory Profile: {scope_id} ({scope_type})", ""]
        
        if prefs:
            lines.append("### Interaction Habits")
            for k, v in prefs.items():
                if isinstance(v, float):
                    desc = "High" if v > 0.7 else "Low" if v < 0.3 else "Neutral"
                    lines.append(f"- {k.title()}: {desc} ({v:.2f})")
                else:
                    lines.append(f"- {k.title()}: {v}")
            lines.append("")
            
        if search_res:
            lines.append("### Core Knowledge & Persona")
            for r in search_res:
                lines.append(f"- [{r.memory.type}] {r.memory.content}")
            lines.append("")
        else:
            lines.append("_No specific memories found for this scope yet._")
            
        return "\n".join(lines)

    def read_memory(
        self,
        rel_path: str,
        *,
        from_line: int = 0,
        line_count: int | None = None,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        """Read a memory citation or workspace file fragment through the Python runtime."""
        memory = self._resolve_memory_reference(rel_path)
        if memory is not None:
            lines = memory.content.splitlines() or [memory.content]
            fragment = self._slice_lines(lines, from_line, line_count)
            return {
                "text": fragment,
                "path": rel_path,
                "memory_id": memory.id,
                "type": memory.type,
                "source_ref": memory.source_ref,
                "from": max(from_line, 0),
                "lines": len(fragment.splitlines()) if fragment else 0,
                "backend": "python",
            }

        resolved = self._resolve_workspace_path(rel_path, workspace_dir)
        if resolved is None or not resolved.exists():
            return {
                "text": f"Memory or file not found: {rel_path}",
                "path": rel_path,
                "backend": "python",
            }

        content = resolved.read_text(encoding="utf-8")
        lines = content.splitlines()
        fragment = self._slice_lines(lines, from_line, line_count)
        return {
            "text": fragment,
            "path": rel_path,
            "from": max(from_line, 0),
            "lines": len(fragment.splitlines()) if fragment else 0,
            "backend": "python",
        }

    def create_backup(
        self,
        mode: str = "snapshot",
        *,
        workspace_dir: str | None = None,
    ) -> dict[str, Any]:
        """Create a snapshot or logical export owned by the Python runtime."""
        return self.backup_surface.create_backup(mode=mode, workspace_dir=workspace_dir)

    def list_backups(self, workspace_dir: str | None = None) -> dict[str, Any]:
        """List manifest-backed backups in stable newest-first order."""
        return self.backup_surface.list_backups(workspace_dir=workspace_dir)

    def preview_restore(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate a restore target without mutating the active database."""
        return self.backup_surface.preview_restore(
            snapshot_path,
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def _get_honorifics(self) -> dict[str, str]:
        """Retrieves the user's preferred honorifics from their profile."""
        scope_type, scope_id = self._default_consumer_scope()
        profile = self.storage.get_profile(scope_id, scope_type)
        
        # New defaults for v10: Neutral / Empty
        h_user = ""
        h_assistant = ""
        h_user_prefix = ""

        if profile:
            prefs = profile.preferences_json or {}
            h_user = prefs.get("user_honorific", "")
            h_assistant = prefs.get("assistant_honorific", "")
        
        # Add spacing and Vietnamese politeness (Dạ) only if honorifics exist
        if self.locale == "vi":
            if h_user:
                h_user_prefix = "Dạ "
                h_user = f"{h_user} "
            if h_assistant:
                h_assistant = f"{h_assistant} "
        
        res = {
            "h_user": h_user,
            "h_assistant": h_assistant,
            "h_user_prefix": h_user_prefix
        }
            
        return res

    def memory_remember(self, content: str) -> str:
        """Simplified action to store a memory with smart intent detection."""
        scope_type, scope_id = self._default_consumer_scope()
        source_kind, source_ref = self._default_consumer_provenance()
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        observation = ObservedOperation(self.observability, tool="memory_remember", scope_type=scope_type, scope_id=scope_id, session_id=session_id)
        try:
            # Smart Intent Detection: Check for correction keywords
            correction_keywords = ["sai rồi", "nhầm rồi", "đổi lại", "không phải", "sửa lại", "thay bằng", "chốt lại"]
            is_potential_correction = any(kw in content.lower() for kw in correction_keywords)
            
            # Metadata for ingest
            metadata = {}
            if is_potential_correction:
                metadata["is_correction"] = True
                metadata["correction_type"] = "explicit_user_intent_detected"

            # We pass metadata to trigger existing correction logic if detected
            mem = self.put_memory(
                content, 
                scope_type=scope_type,
                scope_id=scope_id,
                session_id=session_id,
                source_kind=source_kind,
                source_ref=source_ref,
                metadata=metadata,
            )
            
            if mem:
                self._run_guided_hygiene_cycle(subject=mem.subject, aggressive=True)
                observation.finish(result="success", details={"memory_id": mem.id, "subject": mem.subject})
                
                # Perfect UX (Sprint 2): Clean natural response
                h = self._get_honorifics()
                msg = get_text("action_remembered", locale=self.locale).format(**h)
                
                # Proactive Conflict Check (6.md compliant)
                conflict_msg = ""
                if mem.subject:
                    # Scan for new conflicts triggered by this ingest
                    self.conflict_manager.scan_conflicts(mem.subject)
                    # Check if there are prompts to show
                    prompts = self.memory_conflict_prompts()
                    if prompts:
                        # Append as a 'note' with visual rhythm
                        conflict_msg = f"\n\n{prompts}"

                return f"{msg}{conflict_msg}"
            else:
                observation.finish(result="no_op", details={"reason": "put_memory_rejected"})
                h = self._get_honorifics()
                return get_text("action_not_remembered", locale=self.locale).format(**h)
        except Exception as exc:
            observation.finish(result="error", error_code=type(exc).__name__)
            raise

    def memory_recall(
        self,
        query: str,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        locale: str | None = None,
        retrieval_mode: str = "fast",
    ) -> str:
        """Simplified action to retrieve memories with i18n support."""
        current_locale = locale or self.locale
        initial_scope_type = scope_type
        initial_scope_id = scope_id
        observation = ObservedOperation(
            self.observability,
            tool="memory_recall",
            scope_type=initial_scope_type,
            scope_id=initial_scope_id,
        )
        results = []
        scope_candidates = (
            [(scope_type, scope_id)]
            if scope_type is not None and scope_id is not None
            else self._consumer_scope_candidates()
        )
        for candidate_scope_type, candidate_scope_id in scope_candidates:
            results = self.search(
                query,
                scope_id=candidate_scope_id,
                scope_type=candidate_scope_type,
                limit=5,
                fallback_to_or=True,
            )
            if results:
                break
        
        # 1. Identity/Preference Check (Debt 4 Fix)
        h = self._get_honorifics()
        profile_match = None
        if not initial_scope_type or initial_scope_type == DEFAULT_CONSUMER_SCOPE_TYPE:
            profile = self.storage.get_profile(candidate_scope_id, candidate_scope_type)
            if profile and profile.preferences_json:
                # Simple keyword match in preferences for now
                for key, val in profile.preferences_json.items():
                    if key.lower() in query.lower() or any(word in query.lower() for word in key.split('_')):
                        u_h = h.get("h_user", "").strip()
                        a_h = h.get("h_assistant", "").strip()
                        if u_h:
                            profile_match = f"Dựa trên sở thích của {u_h}, {a_h or ''}nhớ là {u_h} thích: {val}"
                        else:
                            profile_match = f"Dựa trên sở thích đã lưu, thông tin ghi nhận là: {val}"
                        break

        if not results and not profile_match:
            observation.finish(
                result="empty",
                scope_type=initial_scope_type,
                scope_id=initial_scope_id,
                details={"query": query, "result_count": 0},
            )
            return get_text("recall_empty", locale=current_locale).format(query=query, **h)
        
        # Filter results strictly to prioritize active ones for consumer recall
        active_results = [r for r in results if r.memory.status in ('active', 'crystallized')]
        
        if not active_results and not profile_match:
             observation.finish(result="empty_active", details={"query": query})
             return get_text("recall_no_active", locale=current_locale).format(query=query, **h)

        # Use canonical surface serialization for consistency
        serialized_results = serialize_search_results(
            active_results, 
            retrieval_mode=retrieval_mode, 
            locale=current_locale
        )
        
        parts = []
        if profile_match:
            parts.append(f"✨ {profile_match}\n")
            if active_results:
                parts.append("Ngoài ra, em còn thấy các ký ức liên quan:")
        else:
            parts.append(get_text("recall_header", locale=current_locale).format(**h))
        
        for res in serialized_results:
            trust_state = res.get("trust_state", "uncertain")
            trust_prefix_key = f"trust_prefix_{trust_state}"
            trust_prefix = get_text(trust_prefix_key, locale=current_locale)
            
            content = res["memory"]["content"]
            human_reason = res.get("human_reason")
            
            # Traceability for expanded results (Debt 6 Fix)
            trace = ""
            if res.get("retrieval_stage") != "lexical":
                stage = res.get("retrieval_stage", "unknown")
                via = res.get("relation_via_subject") or res.get("relation_via_memory_id", "...")
                trace = f" (📎 Tìm thấy qua {stage}: {via})"
            
            parts.append(f"\n{trust_prefix}\"{content}\"{trace}")
            if human_reason:
                parts.append(f"   └─ {human_reason}")
        
        # Add Why-not (Suppressed Candidates) if in explain mode (Debt 6 Fix)
        if retrieval_mode == "explain":
            suppressed = []
            for res in serialized_results:
                for cand in res.get("suppressed_candidates", []):
                    # Dedup by ID
                    if not any(s["id"] == cand["id"] for s in suppressed):
                        suppressed.append(cand)
            
            if suppressed:
                parts.append("\n" + get_text("suppressed_header", locale=current_locale))
                for cand in suppressed:
                    content = cand["content"]
                    # Map raw reason to i18n
                    reason_key = "suppressed_reason_superseded" if "Superseded" in cand["reason"] else "suppressed_reason_archived"
                    reason = get_text(reason_key, locale=current_locale)
                    parts.append(f"   ❌ \"{content}...\" ({reason})")
                
        # Add conflict awareness if any result is conflicting
        if any(res.get("trust_state") == "conflicting" for res in serialized_results):
            parts.append("\n" + get_text("recall_conflict_warning", locale=current_locale))

        observation.finish(
            result="success",
            scope_type=candidate_scope_type,
            scope_id=candidate_scope_id,
            details={"query": query, "result_count": len(active_results)},
        )
        return "\n".join(parts)

    def memory_correct(self, content: str) -> str:
        """Simplified action to explicitly correct an old fact."""
        scope_type, scope_id = self._default_consumer_scope()
        source_kind, source_ref = self._default_consumer_provenance()
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        observation = ObservedOperation(self.observability, tool="memory_correct", scope_type=scope_type, scope_id=scope_id, session_id=session_id)
        # Intelligently resolve subject by searching for existing matches first
        # This ensures we hit the same-subject conflict/correction logic
        existing = []
        for candidate_scope_type, candidate_scope_id in self._consumer_scope_candidates():
            existing = self.search(
                content,
                scope_id=candidate_scope_id,
                scope_type=candidate_scope_type,
                limit=1,
                fallback_to_or=True,
            )
            if existing:
                scope_type, scope_id = candidate_scope_type, candidate_scope_id
                break
        target_subject = None
        old_memory_id = None
        if existing:
            target_subject = existing[0].memory.subject
            old_memory_id = existing[0].memory.id

        # We pass is_correction=True in metadata to trigger existing correction logic
        mem = self.put_memory(
            content, 
            scope_type=scope_type,
            scope_id=scope_id,
            session_id=session_id,
            subject=target_subject,
            source_kind=source_kind,
            source_ref=source_ref,
            metadata={"is_correction": True, "correction_type": "explicit_user_action"},
        )
        if mem:
            # FORCE SUPERSESSION: If we found an old memory but subject was null, 
            # we must manually retire it since the automatic logic depends on subjects.
            if old_memory_id and not target_subject:
                self.memory_state_machine.transition(
                    memory_id=old_memory_id,
                    to_state="invalidated",
                    reason="explicit_correction_without_subject",
                    details={"corrected_by": mem.id}
                )
            
            self._run_guided_hygiene_cycle(subject=mem.subject, aggressive=True)
            observation.finish(result="success", details={"memory_id": mem.id, "subject": mem.subject})
            h = self._get_honorifics()
            return get_text("action_updated", locale=self.locale).format(**h)
        observation.finish(result="no_op", details={"reason": "put_memory_rejected"})
        h = self._get_honorifics()
        return get_text("action_not_updated", locale=self.locale).format(**h)

    def memory_forget(self, query: str) -> str:
        """Simplified action to archive a memory matching the query."""
        observation = ObservedOperation(self.observability, tool="memory_forget")
        results = []
        for scope_type, scope_id in self._consumer_scope_candidates():
            results = self.search(query, scope_id=scope_id, scope_type=scope_type, limit=1)
            if results:
                break
        if not results:
            observation.finish(result="empty", details={"query": query, "result_count": 0})
            h = self._get_honorifics()
            return get_text("action_not_forgotten", locale=self.locale).format(query=query, **h)
        
        mem_id = results[0].memory.id
        transition_memory(
            self.storage,
            mem_id,
            status="archived",
            event="forgotten_by_user_action",
            details={"query": query},
        )
        self._run_guided_hygiene_cycle(subject=results[0].memory.subject, aggressive=True)
        observation.finish(
            result="success",
            scope_type=scope_type,
            scope_id=scope_id,
            details={"query": query, "memory_id": mem_id},
        )
        h = self._get_honorifics()
        return get_text("action_forgotten", locale=self.locale).format(**h)

    def onboarding(self, workspace_dir: str | None = None) -> dict[str, Any]:
        """Run a bounded first-run onboarding flow against the active Python runtime."""
        effective_workspace = Path(workspace_dir).expanduser() if workspace_dir else Path(self.db_path).expanduser().parent
        doctor = self.doctor(workspace_dir=str(effective_workspace))
        health = doctor["health"]
        health_state = health["state"]

        probe_token = f"aegis-onboarding-{uuid.uuid4().hex[:10]}"
        probe_memory_id: str | None = None
        write_ok = False
        recall_ok = False
        issues: list[str] = []

        try:
            stored = self.put_memory(
                f"Aegis onboarding check {probe_token}",
                type="working",
                scope_type="session",
                scope_id="onboarding",
                source_kind="manual",
                source_ref="onboarding",
                subject="system.onboarding",
                metadata={"ephemeral_probe": True},
            )
            write_ok = stored is not None
            if stored is not None:
                probe_memory_id = stored.id
                results = self.search(
                    probe_token,
                    scope_id="onboarding",
                    scope_type="session",
                    limit=1,
                    include_global=False,
                    fallback_to_or=True,
                )
                recall_ok = any(probe_token in result.memory.content for result in results)
        except Exception as exc:
            issues.append(f"Onboarding check failed during local runtime validation: {exc}")
        finally:
            if probe_memory_id is not None:
                transition_memory(
                    self.storage,
                    probe_memory_id,
                    status="archived",
                    event="onboarding_probe_cleanup",
                    details={"workspace": str(effective_workspace)},
                )

        checks = {
            "workspace": {
                "ok": doctor["workspace"]["writable"],
                "details": f"Workspace path: {doctor['workspace']['path']}",
            },
            "database": {
                "ok": doctor["database"]["exists"],
                "details": f"Database path: {doctor['database']['path']}",
            },
            "write_test": {
                "ok": write_ok,
                "details": "Stored a temporary onboarding probe memory.",
            },
            "recall_test": {
                "ok": recall_ok,
                "details": "Recalled the temporary onboarding probe memory.",
            },
        }

        if health_state == "BROKEN":
            readiness = "NOT_READY"
        elif all(check["ok"] for check in checks.values()):
            readiness = "READY"
        else:
            readiness = "NOT_READY"

        guidance: list[str] = []
        if readiness == "READY" and health_state == "HEALTHY":
            guidance.append("Aegis is ready. You can start using remember, recall, correct, and forget.")
        elif readiness == "READY" and health_state == "DEGRADED_SYNC":
            guidance.append("Aegis is usable locally, but optional sync-related features are currently degraded.")
        else:
            if not checks["workspace"]["ok"]:
                guidance.append("Aegis could not write to the workspace. Check folder permissions and try again.")
            if not checks["database"]["ok"]:
                guidance.append("Aegis could not confirm the local database path. Check the DB location and try again.")
            if not checks["write_test"]["ok"]:
                guidance.append("Aegis could not store a local test memory. Local runtime setup is not ready yet.")
            if checks["write_test"]["ok"] and not checks["recall_test"]["ok"]:
                guidance.append("Aegis stored a test memory but could not recall it. The local search path needs attention.")
            if health_state == "BROKEN":
                guidance.append("Aegis is broken for local use right now. Fix the local database or workspace issue before relying on memory.")

        if issues:
            guidance.extend(issues)

        summary_lines = [
            "## Aegis Setup Check",
            "",
            f"Readiness: {readiness}",
            f"Health: {health_state}",
            "",
            "Checks:",
            f"- Workspace writable: {'yes' if checks['workspace']['ok'] else 'no'}",
            f"- Database available: {'yes' if checks['database']['ok'] else 'no'}",
            f"- Local write test: {'yes' if checks['write_test']['ok'] else 'no'}",
            f"- Local recall test: {'yes' if checks['recall_test']['ok'] else 'no'}",
        ]
        if guidance:
            summary_lines.extend(["", "Guidance:"])
            summary_lines.extend([f"- {entry}" for entry in guidance])

        return {
            "backend": "python",
            "readiness": readiness,
            "health_state": health_state,
            "health": health,
            "workspace": doctor["workspace"],
            "database": doctor["database"],
            "checks": checks,
            "guidance": guidance,
            "summary": "\n".join(summary_lines),
        }

    def status_summary(self) -> str:
        """Return a plain-language status summary for everyday users."""
        return self.health_surface.status_summary()

    def doctor_summary(self, workspace_dir: str | None = None) -> str:
        """Return a plain-language diagnostic summary for everyday users."""
        return self.health_surface.doctor_summary(workspace_dir=workspace_dir)

    def backup_create_summary(self, payload: dict[str, Any]) -> str:
        return self.backup_surface.backup_create_summary(payload)

    def backup_list_summary(self, payload: dict[str, Any]) -> str:
        return self.backup_surface.backup_list_summary(payload)

    def restore_preview_summary(self, payload: dict[str, Any]) -> str:
        return self.backup_surface.restore_preview_summary(payload)

    def restore_result_summary(self, payload: dict[str, Any]) -> str:
        return self.backup_surface.restore_result_summary(payload)

    def restore_backup(
        self,
        snapshot_path: str,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        """Restore a SQLite snapshot or JSON export into the active Python runtime DB."""
        return self.backup_surface.restore_backup(
            snapshot_path,
            scope_type=scope_type,
            scope_id=scope_id,
        )

    def observability_snapshot(self) -> dict[str, Any]:
        snapshot = self.observability.snapshot()
        snapshot["health_state"] = self._runtime_health_snapshot()["state"]
        snapshot["db_path"] = self.db_path
        return snapshot

    def close(self) -> None:
        self.storage.close()

    def serialize_search_results(
        self,
        results: List[SearchResult],
        *,
        retrieval_mode: str = "explain",
    ) -> list[dict[str, Any]]:
        return serialize_search_results(results, retrieval_mode=retrieval_mode)

    def _serialize_search_result(self, result: SearchResult, *, retrieval_mode: str = "explain") -> dict[str, Any]:
        return serialize_search_result(result, retrieval_mode=retrieval_mode)

    def spotlight(
        self,
        query: str,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        limit: int = 3,
        include_global: bool = False,
        semantic: bool = False,
        semantic_model: str | None = None,
        intent: str | None = None,
    ) -> dict[str, Any]:
        st = scope_type or DEFAULT_CONSUMER_SCOPE_TYPE
        sid = scope_id or DEFAULT_CONSUMER_SCOPE_ID
        spotlight_query = SearchQuery(
            query=query,
            scope_id=sid,
            scope_type=st,
            limit=limit,
            min_score=0.0,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
        )
        if intent:
            setattr(spotlight_query, "intent", intent)
        if semantic:
            results = self.retrieval_orchestrator.retrieve(spotlight_query).results
        else:
            results = self.search_pipeline.search(spotlight_query)
        return build_spotlight_response(
            query,
            results,
            scope_type=st,
            scope_id=sid,
            locale=self.locale,
        )

    def core_showcase(
        self,
        query: str,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        limit: int = 3,
        include_global: bool = False,
        semantic: bool = False,
        semantic_model: str | None = None,
        intent: str | None = None,
    ) -> dict[str, Any]:
        st = scope_type or DEFAULT_CONSUMER_SCOPE_TYPE
        sid = scope_id or DEFAULT_CONSUMER_SCOPE_ID
        showcase_query = SearchQuery(
            query=query,
            scope_id=sid,
            scope_type=st,
            limit=limit,
            min_score=0.0,
            include_global=include_global,
            semantic=semantic,
            semantic_model=semantic_model,
        )
        if intent:
            setattr(showcase_query, "intent", intent)
        if semantic:
            results = self.retrieval_orchestrator.retrieve(showcase_query).results
        else:
            results = self.search_pipeline.search(showcase_query)
        if not results:
            return build_core_showcase_response(query, scope_type=st, scope_id=sid, payload=None)

        top = results[0]
        memory_id = top.memory.id
        payload = build_core_showcase_payload(
            top,
            evidence=self.operator_surface.get_memory_evidence(memory_id),
            governance=self.operator_surface.inspect_governance(memory_id=memory_id, limit=10),
            neighbors=self.operator_surface.memory_neighbors(memory_id, limit=5),
            v10_signals=self.operator_surface.v10_core_signals(memory_id),
            transition_gate=self.operator_surface.v10_transition_gate(memory_id),
            health=self.memory_health_snapshot(scope_type=st, scope_id=sid),
            locale=self.locale,
        )
        return build_core_showcase_response(query, scope_type=st, scope_id=sid, payload=payload)

    def _resolve_memory_reference(self, rel_path: str):
        memory_id = rel_path
        if rel_path.startswith("aegis://"):
            memory_id = rel_path.rsplit("/", 1)[-1]
        memory = self.storage.get_memory(memory_id)
        if memory is not None:
            return memory

        row = self.storage.fetch_one(
            "SELECT id FROM memories WHERE source_ref = ? OR summary = ? LIMIT 1",
            (rel_path, rel_path),
        )
        if row is None:
            return None
        return self.storage.get_memory(row["id"])

    def _resolve_workspace_path(self, rel_path: str, workspace_dir: str | None) -> Path | None:
        candidate = Path(rel_path).expanduser()
        if candidate.is_absolute():
            return candidate
        if workspace_dir:
            return Path(workspace_dir).expanduser() / rel_path
        return None

    def _slice_lines(self, lines: list[str], from_line: int, line_count: int | None) -> str:
        start = max(from_line, 0)
        end = None if line_count is None else start + max(line_count, 0)
        return "\n".join(lines[start:end])

    def _auto_link_same_subject(self, memory_id: str, *, limit: int = 5) -> int:
        memory = self.storage.get_memory(memory_id)
        if memory is None or not memory.subject or memory.subject == "general.untagged":
            return 0
        peers = self.storage.find_same_subject_peers(
            memory_id=memory.id,
            scope_type=memory.scope_type,
            scope_id=memory.scope_id,
            subject=memory.subject,
            limit=limit,
        )
        linked = 0
        conn = self.storage._get_connection()
        for peer in peers:
            self.storage.upsert_memory_link(
                source_id=memory.id,
                target_id=peer["id"],
                link_type="same_subject",
                weight=0.6,
                metadata={"auto": True, "rule": "same_subject"},
                commit=False,
                bump_revision=False,
            )
            linked += 1
        if linked:
            self.storage.bump_scope_revision(memory.scope_type, memory.scope_id, commit=False)
            conn.commit()
        return linked

    def _backfill_missing_derived_fields(self) -> int:
        rows = self.storage.fetch_all(
            """
            SELECT id, content, subject, summary
            FROM memories
            WHERE status = 'active'
              AND (
                subject IS NULL OR TRIM(subject) = ''
                OR summary IS NULL OR TRIM(summary) = ''
              )
            """
        )
        updates: list[tuple[str | None, str | None, str]] = []
        for row in rows:
            subject = row["subject"]
            summary = row["summary"]
            next_subject = subject
            next_summary = summary

            if subject is None or not str(subject).strip():
                next_subject = self.ingest_engine.subject_normalizer.normalize(
                    self.ingest_engine.content_extractor.derive_subject(row["content"])
                )
            if summary is None or not str(summary).strip():
                next_summary = self.ingest_engine.content_extractor.derive_summary(row["content"])

            if next_subject != subject or next_summary != summary:
                updates.append((next_subject, next_summary, row["id"]))

        if updates:
            self.storage.executemany(
                "UPDATE memories SET subject = ?, summary = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                updates,
            )
        return len(updates)

    def _backfill_missing_evidence(self) -> int:
        rows = self.storage.fetch_all(
            """
            SELECT id, type, scope_type, scope_id, session_id, content, source_kind, source_ref, metadata_json
            FROM memories
            WHERE status IN ('active', 'archived', 'expired', 'conflict_candidate', 'superseded')
            """
        )
        backfilled = 0
        for row in rows:
            metadata = self.storage._coerce_metadata(row["metadata_json"])
            evidence = metadata.get("evidence")
            if isinstance(evidence, dict) and evidence.get("event_id"):
                continue
            event = self.storage.create_evidence_event(
                scope_type=row["scope_type"],
                scope_id=row["scope_id"],
                session_id=row["session_id"],
                memory_id=row["id"],
                source_kind=row["source_kind"],
                source_ref=row["source_ref"],
                raw_content=row["content"],
                metadata={
                    "capture_stage": "rebuild_backfill",
                    "memory_type": row["type"],
                },
            )
            metadata["evidence"] = {
                "event_id": event.id,
                "kind": "raw_ingest",
                "source_kind": event.source_kind,
                "source_ref": event.source_ref,
                "captured_at": event.created_at.isoformat(),
            }
            self.storage.execute(
                "UPDATE memories SET metadata_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(metadata, ensure_ascii=True), row["id"]),
            )
            backfilled += 1
        return backfilled

    def _backfill_same_subject_links(self, *, per_memory_limit: int = 5) -> int:
        rows = self.storage.fetch_all(
            """
            SELECT id
            FROM memories
            WHERE status = 'active' AND subject IS NOT NULL AND TRIM(subject) != ''
            """
        )
        linked = 0
        for row in rows:
            linked += self._auto_link_same_subject(row["id"], limit=per_memory_limit)
        return linked

    def _auto_link_procedural_semantic(self, memory_id: str, *, limit: int = 5) -> int:
        memory = self.storage.get_memory(memory_id)
        if memory is None or not memory.subject or memory.subject == "general.untagged":
            return 0
        if memory.type == "procedural":
            peer_type = "semantic"
            link_type = "procedural_supports_semantic"
            source_first = True
        elif memory.type == "semantic":
            peer_type = "procedural"
            link_type = "procedural_supports_semantic"
            source_first = False
        else:
            return 0

        peers = self.storage.find_same_subject_typed_peers(
            memory_id=memory.id,
            scope_type=memory.scope_type,
            scope_id=memory.scope_id,
            subject=memory.subject,
            peer_type=peer_type,
            limit=limit,
        )
        linked = 0
        conn = self.storage._get_connection()
        for peer in peers:
            source_id = memory.id if source_first else peer["id"]
            target_id = peer["id"] if source_first else memory.id
            self.storage.upsert_memory_link(
                source_id=source_id,
                target_id=target_id,
                link_type=link_type,
                weight=0.75,
                metadata={"auto": True, "rule": "procedural_semantic_same_subject"},
                commit=False,
                bump_revision=False,
            )
            linked += 1
        if linked:
            self.storage.bump_scope_revision(memory.scope_type, memory.scope_id, commit=False)
            conn.commit()
        return linked

    def _backfill_procedural_semantic_links(self, *, per_memory_limit: int = 5) -> int:
        rows = self.storage.fetch_all(
            """
            SELECT id
            FROM memories
            WHERE status = 'active'
              AND subject IS NOT NULL
              AND TRIM(subject) != ''
              AND type IN ('procedural', 'semantic')
            """
        )
        linked = 0
        for row in rows:
            linked += self._auto_link_procedural_semantic(row["id"], limit=per_memory_limit)
        return linked

    def _timestamp_slug(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _backups_dir(self, workspace_dir: str | None) -> Path:
        return Path(workspace_dir or Path(self.db_path).parent) / ".aegis_py" / "backups"

    def _manifest_path_for_backup(self, backup_path: Path) -> Path:
        return backup_path.with_name(f"{backup_path.name}.manifest.json")

    def _write_backup_manifest(self, backup_path: Path, mode: str) -> Path:
        manifest = {
            "manifest_version": 1,
            "runtime_version": RUNTIME_VERSION,
            "mode": mode,
            "created_at": self._timestamp_slug(),
            "artifact_path": str(backup_path),
            "artifact_bytes": backup_path.stat().st_size,
            "db_path": self.db_path,
            "counts": self._memory_counts(),
        }
        manifest_path = self._manifest_path_for_backup(backup_path)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        return manifest_path

    def _load_manifest_for_backup(self, backup_path: Path) -> dict[str, Any] | None:
        manifest_path = self._manifest_path_for_backup(backup_path)
        if not manifest_path.exists():
            return None
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if payload.get("artifact_path") != str(backup_path):
            raise ValueError("Backup manifest does not match the selected artifact.")
        return payload

    def _memory_counts(self, scope_filter: dict[str, str] | None = None) -> dict[str, int]:
        if scope_filter is None:
            rows = self.storage.fetch_all("SELECT status, COUNT(*) AS count FROM memories GROUP BY status")
        else:
            rows = self.storage.fetch_all(
                """
                SELECT status, COUNT(*) AS count
                FROM memories
                WHERE scope_type = ? AND scope_id = ?
                GROUP BY status
                """,
                (scope_filter["scope_type"], scope_filter["scope_id"]),
            )
        return {row["status"]: row["count"] for row in rows}

    def _normalize_scope_filter(
        self,
        *,
        scope_type: str | None,
        scope_id: str | None,
    ) -> dict[str, str] | None:
        if scope_type is None and scope_id is None:
            return None
        if not scope_type or not scope_id:
            raise ValueError("scope_type and scope_id must both be provided for scoped restore flows.")
        return {"scope_type": scope_type, "scope_id": scope_id}

    def _filter_export_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        scope_filter: dict[str, str] | None,
    ) -> list[dict[str, Any]]:
        if scope_filter is None:
            return rows
        return [
            row for row in rows
            if row.get("scope_type") == scope_filter["scope_type"]
            and row.get("scope_id") == scope_filter["scope_id"]
        ]

    def _read_snapshot_memories(
        self,
        conn: sqlite3.Connection,
        *,
        scope_filter: dict[str, str] | None,
    ) -> list[dict[str, Any]]:
        if scope_filter is None:
            rows = conn.execute("SELECT * FROM memories").fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM memories
                WHERE scope_type = ? AND scope_id = ?
                """,
                (scope_filter["scope_type"], scope_filter["scope_id"]),
            ).fetchall()
        return [dict(row) for row in rows]

    def _build_preview_counts(
        self,
        *,
        source_rows: list[dict[str, Any]],
        source_scope_count: int,
        current_scope_counts: dict[str, int],
        scope_filter: dict[str, str] | None,
    ) -> dict[str, Any]:
        source_counts: dict[str, int] = {}
        for row in source_rows:
            status = row.get("status", "active")
            source_counts[status] = source_counts.get(status, 0) + 1

        preview: dict[str, Any] = {
            "records": len(source_rows),
            "counts": source_counts,
        }
        if scope_filter is None:
            preview["scopes"] = source_scope_count
        else:
            preview["restore_strategy"] = "replace_scope"
            preview["would_replace_scope_counts"] = current_scope_counts
        return preview

    def _restore_scope_from_backup(
        self,
        source: Path,
        *,
        scope_filter: dict[str, str],
    ) -> int:
        style_signal_rows: list[dict[str, Any]] = []
        style_profile_rows: list[dict[str, Any]] = []
        if source.suffix.lower() == ".json":
            rows = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                raise ValueError("Export backup payload must be a JSON array.")
            source_rows = self._filter_export_rows(rows, scope_filter=scope_filter)
        else:
            with sqlite3.connect(source) as conn:
                conn.row_factory = sqlite3.Row
                source_rows = self._read_snapshot_memories(conn, scope_filter=scope_filter)
                style_signal_rows = self._read_snapshot_scope_table(
                    conn,
                    table="style_signals",
                    scope_filter=scope_filter,
                )
                style_profile_rows = self._read_snapshot_scope_table(
                    conn,
                    table="style_profiles",
                    scope_filter=scope_filter,
                )

        target = self.storage._get_connection()
        with target:
            target.execute(
                "DELETE FROM style_signals WHERE scope_type = ? AND scope_id = ?",
                (scope_filter["scope_type"], scope_filter["scope_id"]),
            )
            target.execute(
                "DELETE FROM style_profiles WHERE scope_type = ? AND scope_id = ?",
                (scope_filter["scope_type"], scope_filter["scope_id"]),
            )
            target.execute(
                "DELETE FROM memories WHERE scope_type = ? AND scope_id = ?",
                (scope_filter["scope_type"], scope_filter["scope_id"]),
            )
            for row in source_rows:
                target.execute(
                    """
                    INSERT INTO memories (
                        id, type, scope_type, scope_id, session_id, content, summary, subject,
                        source_kind, source_ref, status, confidence, activation_score, access_count,
                        created_at, updated_at, last_accessed_at, expires_at, archived_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row["type"],
                        row["scope_type"],
                        row["scope_id"],
                        row.get("session_id"),
                        row["content"],
                        row.get("summary"),
                        row.get("subject"),
                        row.get("source_kind", "manual"),
                        row.get("source_ref"),
                        row.get("status", "active"),
                        row.get("confidence", 1.0),
                        row.get("activation_score", 1.0),
                        row.get("access_count", 0),
                        row.get("created_at"),
                        row.get("updated_at") or row.get("created_at"),
                        row.get("last_accessed_at"),
                        row.get("expires_at"),
                        row.get("archived_at"),
                        self._normalize_metadata_json(row.get("metadata_json")),
                    ),
                )
            for row in style_signal_rows:
                target.execute(
                    """
                    INSERT INTO style_signals (
                        id, session_id, scope_id, scope_type, signal_key, signal_value,
                        agent_id, signal, weight, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row.get("session_id"),
                        row.get("scope_id"),
                        row.get("scope_type"),
                        row.get("signal_key"),
                        row.get("signal_value"),
                        row.get("agent_id"),
                        row.get("signal"),
                        row.get("weight", 1.0),
                        row.get("created_at"),
                    ),
                )
            for row in style_profile_rows:
                target.execute(
                    """
                    INSERT INTO style_profiles (
                        id, scope_id, scope_type, preferences_json, last_updated
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row.get("scope_id"),
                        row.get("scope_type"),
                        self._normalize_metadata_json(row.get("preferences_json")),
                        row.get("last_updated"),
                    ),
                )
        return len(source_rows)

    def _normalize_metadata_json(self, metadata: Any) -> str:
        if metadata is None:
            return "{}"
        if isinstance(metadata, str):
            return metadata
        return json.dumps(metadata, ensure_ascii=True)

    def _read_snapshot_scope_table(
        self,
        conn: sqlite3.Connection,
        *,
        table: str,
        scope_filter: dict[str, str],
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            f"""
            SELECT * FROM {table}
            WHERE scope_type = ? AND scope_id = ?
            """,
            (scope_filter["scope_type"], scope_filter["scope_id"]),
        ).fetchall()
        return [dict(row) for row in rows]
