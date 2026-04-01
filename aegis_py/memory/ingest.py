from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING
import re
from .classifier import LaneClassifier
from .entity import EntityExtractor
from .extractor import ContentExtractor
from .filter import WorthyFilter
from .factory import MemoryFactory
from .normalizer import SubjectNormalizer
from .scorer import WriteTimeScorer
from .weaver import WeaverBeast
from .correction import CorrectionDetector
from ..storage.manager import StorageManager
from ..storage.models import Memory
from ..v7.policy_gate import ValidationPolicyGate
from ..v7.state_machine import MemoryStateMachine

if TYPE_CHECKING:
    from ..retrieval.search import SearchPipeline
    from ..retrieval.models import SearchQuery

@dataclass
class MemoryCandidate:
    memory: Memory
    evidence_event_id: str | None
    has_evidence: bool
    contradiction_risk: bool
    confidence: float
    activation_score: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class PromotionDecision:
    promotable: bool
    reasons: list[str] = field(default_factory=list)
    target_state: str = "validated"
    policy_name: str = "legacy-ingest"


class IngestEngine:
    """Orchestrates memory ingestion: filtering -> creation -> storage."""
    NEGATION_MARKERS = (
        " not ",
        " no ",
        " never ",
        " no longer ",
        " does not ",
        " do not ",
        " isn't ",
        " aren't ",
        " không ",
        " chẳng ",
        " chưa ",
    )
    
    def __init__(
        self, 
        storage: StorageManager, 
        filter: Optional[WorthyFilter] = None,
        search_pipeline: Optional["SearchPipeline"] = None
    ):
        self.storage = storage
        self.filter = filter or WorthyFilter()
        self.factory = MemoryFactory()
        self.lane_classifier = LaneClassifier()
        self.entity_extractor = EntityExtractor()
        self.content_extractor = ContentExtractor()
        self.subject_normalizer = SubjectNormalizer()
        self.write_time_scorer = WriteTimeScorer()
        self.weaver = WeaverBeast(storage)
        self.correction_detector = CorrectionDetector()
        self.search_pipeline = search_pipeline
        self.policy_gate = ValidationPolicyGate()
        self.state_machine = MemoryStateMachine(storage)

    def ingest(
        self,
        content: str,
        type: str = "episodic",
        scope_type: str = "session",
        scope_id: str = "default",
        source_kind: str = "message",
        **kwargs
    ) -> Optional[Memory]:
        """Ingests a memory if it's worthy and not a duplicate."""
        
        # 1. Worthiness Check
        if not self.filter.is_worthy(content):
            return None
            
        # 2. Early Correction Detection
        metadata = dict(kwargs.pop("metadata", {}) or {})
        if self.correction_detector.is_correction(content):
            metadata["is_correction"] = True
            
        is_explicit_correction = metadata.get("is_correction", False)

        # 3. Semantic Deduplication & Subject Resolution Check (The Fact Slot Lane)
        # We look for a 'Fact Slot' (Subject) rather than just content similarity
        resolved_subject = kwargs.get("subject")
        
        # 3.1 EXACT DEDUPLICATION (Early Check to avoid 'ingest_rejected' logs)
        # We check for exact content/scope/type match before anything else
        existing_exact = self.storage.fetch_one(
            "SELECT id FROM memories WHERE content = ? AND scope_id = ? AND scope_type = ? LIMIT 1",
            (content, scope_id, scope_type)
        )
        if existing_exact:
            mem_id = existing_exact["id"]
            self.storage.reinforce_memory(mem_id)
            return self.storage.get_memory(mem_id)

        if not resolved_subject and self.search_pipeline:
            from ..retrieval.models import SearchQuery
            # Search for semantic matches to resolve the 'Slot' we are talking about
            res_query = SearchQuery(
                query=content,
                scope_id=scope_id,
                scope_type=scope_type,
                limit=1,
                semantic=True,
                include_global=False
            )
            resolution_results = self.search_pipeline.search(res_query)
            if resolution_results:
                top_match = resolution_results[0]
                # If it's a strong semantic match (>= 0.7), we've found our Fact Slot
                if top_match.score >= 0.70:
                    resolved_subject = top_match.memory.subject or self.content_extractor.derive_subject(top_match.memory.content)
                    kwargs["subject"] = resolved_subject
                    # If the user intent looks like a correction, mark it explicitly
                    if is_explicit_correction or self.correction_detector.is_correction(content):
                        metadata["is_correction"] = True
                        metadata["correction_type"] = "fact_slot_update"

        if (
            self.search_pipeline
            and resolved_subject
        ):
            from ..retrieval.models import SearchQuery
            normalized_subject = self.subject_normalizer.normalize(resolved_subject)
            resolved_subject = normalized_subject
            kwargs["subject"] = normalized_subject
            
        # DETERMINISTIC RULE (Phase 1): If same subject OR explicit old_ids, we MUST supersede
        if metadata.get("is_correction"):
            # 1. Handle explicit old_ids from facade or elsewhere
            explicit_old_ids = metadata.get("corrected_from", [])
            if isinstance(explicit_old_ids, str):
                explicit_old_ids = [explicit_old_ids]
            
            # 2. Find all active memories with this exact subject slot (if subject resolved)
            peer_ids = []
            if resolved_subject:
                peers = self.storage.fetch_all(
                    """
                    SELECT id FROM memories 
                    WHERE status = 'active' AND scope_type = ? AND scope_id = ? AND subject = ?
                    """,
                    (scope_type, scope_id, resolved_subject)
                )
                peer_ids = [row["id"] for row in peers]
            
            # Combine both sets of IDs to retire
            all_ids_to_retire = set(peer_ids) | set(explicit_old_ids)
            
            for oid in all_ids_to_retire:
                self.state_machine.transition(
                    memory_id=oid,
                    to_state="invalidated",
                    reason="deterministic_fact_correction",
                    details={"new_memory_content": content[:50]}
                )

        if (
            self.search_pipeline
            and resolved_subject
            and not metadata.get("is_correction")
        ):
            from ..retrieval.models import SearchQuery
            # Normal deduplication logic for non-corrections

        # 3. Classify omitted lane
        if type is None:
            type = self.lane_classifier.infer(
                content=content,
                session_id=kwargs.get("session_id"),
                source_kind=source_kind,
            )

        # 4. Create Memory Instance
        # metadata already prepared above
            
        subject = (
            kwargs["subject"]
            if "subject" in kwargs
            else self.content_extractor.derive_subject(content)
        )
        summary = (
            kwargs["summary"]
            if "summary" in kwargs
            else self.content_extractor.derive_summary(content)
        )
        subject = self.subject_normalizer.normalize(subject)
        if "confidence" in kwargs:
            confidence = kwargs["confidence"]
        else:
            confidence = None
        if "activation_score" in kwargs:
            activation_score = kwargs["activation_score"]
        else:
            activation_score = None
        if confidence is None or activation_score is None:
            score_profile = self.write_time_scorer.build_profile(
                content=content,
                memory_type=type,
                source_kind=source_kind,
            )
            inferred_confidence, inferred_activation = self.write_time_scorer.infer(
                content=content,
                memory_type=type,
                source_kind=source_kind,
            )
            if confidence is None:
                confidence = inferred_confidence
            if activation_score is None:
                activation_score = inferred_activation
        else:
            score_profile = self.write_time_scorer.build_profile(
                content=content,
                memory_type=type,
                source_kind=source_kind,
            )
        kwargs["subject"] = subject
        kwargs["summary"] = summary
        kwargs["confidence"] = confidence
        kwargs["activation_score"] = activation_score
        metadata["score_profile"] = score_profile
        entities = self.entity_extractor.extract(content=content, subject=kwargs.get("subject"))
        if entities:
            metadata["entities"] = entities
        memory = self.factory.create(
            type=type,
            content=content,
            scope_type=scope_type,
            scope_id=scope_id,
            source_kind=source_kind,
            metadata=metadata,
            **kwargs
        )

        if not (isinstance(metadata.get("evidence"), dict) and metadata["evidence"].get("event_id")):
            evidence_event = self.storage.create_evidence_event(
                scope_type=scope_type,
                scope_id=scope_id,
                session_id=kwargs.get("session_id"),
                memory_id=memory.id,
                source_kind=source_kind,
                source_ref=kwargs.get("source_ref"),
                raw_content=content,
                metadata={
                    "capture_stage": "canonical_ingest",
                    "memory_type": type,
                },
            )
            memory.metadata["evidence"] = {
                "event_id": evidence_event.id,
                "kind": "raw_ingest",
                "source_kind": source_kind,
                "source_ref": kwargs.get("source_ref"),
                "captured_at": evidence_event.created_at.isoformat(),
            }

        candidate = self.build_candidate(memory)
        decision = self.evaluate_candidate(candidate)
        admission_state = decision.target_state
        memory.metadata["promotion"] = {
            "promotable": decision.promotable,
            "reasons": decision.reasons,
            "policy_name": decision.policy_name,
        }
        memory.metadata["admission_state"] = admission_state
        memory.metadata["memory_state"] = admission_state
        memory.metadata["validation_gate"] = {
            "target_state": decision.target_state,
            "policy_name": decision.policy_name,
            "reasons": decision.reasons,
        }
        if not decision.promotable:
            self.storage.record_governance_event(
                event_kind="validation_blocked",
                scope_type=scope_type,
                scope_id=scope_id,
                evidence_event_id=candidate.evidence_event_id,
                payload={
                    "memory_type": type,
                    "target_state": decision.target_state,
                    "reasons": decision.reasons,
                    "score_profile": score_profile,
                    "content": content,
                },
            )
            return None
        
        # 4. Store (with built-in deduplication)
        success = self.storage.put_memory(memory)
        if success:
            self.state_machine.record_initial_state(
                memory_id=memory.id,
                to_state=decision.target_state,
                reason="ingest_policy_gate",
                evidence_event_id=candidate.evidence_event_id,
                details={"reasons": decision.reasons},
            )
            self.storage.record_governance_event(
                event_kind="memory_admitted",
                scope_type=scope_type,
                scope_id=scope_id,
                memory_id=memory.id,
                evidence_event_id=candidate.evidence_event_id,
                payload={
                    "memory_type": type,
                    "target_state": decision.target_state,
                    "reasons": decision.reasons,
                    "score_profile": score_profile,
                },
            )
        return memory if success else None

    def _token_overlap_ratio(self, left: str, right: str) -> float:
        token_pattern = re.compile(r"\w+", re.UNICODE)
        left_tokens = {token for token in token_pattern.findall(left.lower()) if len(token) > 2}
        right_tokens = {token for token in token_pattern.findall(right.lower()) if len(token) > 2}
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = left_tokens & right_tokens
        return len(overlap) / min(len(left_tokens), len(right_tokens))

    def build_candidate(self, memory: Memory) -> MemoryCandidate:
        evidence = memory.metadata.get("evidence", {}) if isinstance(memory.metadata, dict) else {}
        evidence_event_id = evidence.get("event_id") if isinstance(evidence, dict) else None
        contradiction_risk = self._has_contradiction_risk(memory)
        reasons: list[str] = []
        if contradiction_risk:
            reasons.append("contradiction_risk_detected")
        if evidence_event_id:
            reasons.append("evidence_present")
        else:
            reasons.append("evidence_missing")
        return MemoryCandidate(
            memory=memory,
            evidence_event_id=evidence_event_id,
            has_evidence=bool(evidence_event_id),
            contradiction_risk=contradiction_risk,
            confidence=float(memory.confidence or 0.0),
            activation_score=float(memory.activation_score or 0.0),
            reasons=reasons,
        )

    def evaluate_candidate(self, candidate: MemoryCandidate) -> PromotionDecision:
        decision = self.policy_gate.evaluate(
            memory=candidate.memory,
            evidence_event_id=candidate.evidence_event_id,
            contradiction_risk=candidate.contradiction_risk,
        )
        return PromotionDecision(
            promotable=decision.promotable,
            reasons=decision.reasons,
            target_state=decision.target_state,
            policy_name=decision.policy_name,
        )

    def _has_contradiction_risk(self, memory: Memory) -> bool:
        if not memory.subject or bool(memory.metadata.get("is_correction")):
            return False
        peers = self.storage.fetch_all(
            """
            SELECT content
            FROM memories
            WHERE id != ?
              AND status = 'active'
              AND scope_type = ?
              AND scope_id = ?
              AND subject = ?
            ORDER BY activation_score DESC, updated_at DESC
            LIMIT 5
            """,
            (memory.id, memory.scope_type, memory.scope_id, memory.subject),
        )
        return any(
            self._candidate_conflicts_with_peer(memory.content, row["content"])
            for row in peers
        )

    def _candidate_conflicts_with_peer(self, candidate_content: str, peer_content: str) -> bool:
        overlap = self._token_overlap_ratio(candidate_content, peer_content)
        if overlap < 0.45:
            return False
        return self._contains_negation(candidate_content) != self._contains_negation(peer_content)

    def _contains_negation(self, content: str) -> bool:
        normalized = f" {' '.join(content.lower().split())} "
        return any(marker in normalized for marker in self.NEGATION_MARKERS)
