import sqlite3
import json
import math
import re
from typing import Optional, List, Any
from datetime import datetime
from .evidence import EvidenceRepository
from .graph import GraphRepository
from .governance import GovernanceRepository
from .memory import MemoryRepository
from .models import ADMISSION_STATES, EvidenceEvent, Memory
from .hygiene import StorageHygieneRepository
from .scope import ScopeRepository
from ..hygiene.transitions import transition_memory, coerce_metadata, now_iso

LEGACY_COLUMN_REPAIRS: dict[str, dict[str, str]] = {
    "memories": {
        "session_id": "TEXT",
        "summary": "TEXT",
        "subject": "TEXT",
        "source_ref": "TEXT",
        "origin_node_id": "TEXT",
        "status": "TEXT NOT NULL DEFAULT 'active'",
        "confidence": "REAL NOT NULL DEFAULT 1.0",
        "activation_score": "REAL NOT NULL DEFAULT 1.0",
        "access_count": "INTEGER NOT NULL DEFAULT 0",
        "updated_at": "TEXT",
        "last_accessed_at": "TEXT",
        "expires_at": "TEXT",
        "archived_at": "TEXT",
        "metadata_json": "TEXT",
    },
    "style_signals": {
        "session_id": "TEXT",
        "scope_id": "TEXT",
        "scope_type": "TEXT",
        "signal_key": "TEXT",
        "signal_value": "TEXT",
        "agent_id": "TEXT",
        "signal": "TEXT",
        "weight": "REAL NOT NULL DEFAULT 1.0",
        "created_at": "TEXT",
    },
    "style_profiles": {
        "id": "TEXT",
        "scope_id": "TEXT",
        "scope_type": "TEXT",
        "preferences_json": "TEXT NOT NULL DEFAULT '{}'",
        "last_updated": "TEXT",
    },
    "scope_policies": {
        "sync_policy": "TEXT NOT NULL DEFAULT 'local_only'",
        "sync_state": "TEXT NOT NULL DEFAULT 'local'",
        "last_sync_at": "TEXT",
        "updated_at": "TEXT",
    },
    "scope_revisions": {
        "revision": "INTEGER NOT NULL DEFAULT 0",
        "updated_at": "TEXT",
    },
    "memory_links": {
        "weight": "REAL NOT NULL DEFAULT 1.0",
        "metadata_json": "TEXT",
        "created_at": "TEXT",
    },
    "conflicts": {
        "subject_key": "TEXT",
        "score": "REAL NOT NULL DEFAULT 0",
        "reason": "TEXT",
        "resolution": "TEXT",
        "status": "TEXT NOT NULL DEFAULT 'open'",
        "created_at": "TEXT",
        "resolved_at": "TEXT",
    },
}

RETENTION_THRESHOLDS: dict[str, tuple[float, float, float]] = {
    "working": (0.7, 0.3, 0.12),
    "episodic": (0.62, 0.28, 0.1),
    "semantic": (0.55, 0.24, 0.08),
    "procedural": (0.58, 0.22, 0.08),
}

DEFAULT_COMPACTION_POLICY: dict[str, int] = {
    "archived_memory_days": 30,
    "superseded_memory_days": 14,
    "evidence_days": 30,
    "governance_days": 30,
    "replication_days": 14,
    "background_days": 14,
}

class StorageManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self.memory = MemoryRepository(self)
        self.evidence = EvidenceRepository(self)
        self.governance = GovernanceRepository(self)
        self.scope = ScopeRepository(self)
        self.graph = GraphRepository(self)
        self.storage_hygiene = StorageHygieneRepository(self)
        self._init_db()

    def _get_connection(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA synchronous = NORMAL;")
            self._conn.execute("PRAGMA busy_timeout = 5000;")
        return self._conn

    def _init_db(self):
        conn = self._get_connection()
        from aegis_py.ops.migration import MigrationManager
        from pathlib import Path
        migrations_dir = Path(__file__).parent / "migrations"
        
        # Legacy repair (if schema exists but user_version = 0, we still want to ensure 
        # missing columns are added before we rely on versioned migrations)
        try:
            self._repair_legacy_schema()
        except Exception:
            pass # If tables don't exist, this does nothing
            
        migrator = MigrationManager(conn, str(migrations_dir))
        migrator.run_migrations()

    def _table_exists(self, table_name: str) -> bool:
        row = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return row is not None

    def _table_columns(self, table_name: str) -> set[str]:
        conn = self._get_connection()
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

    def _repair_legacy_schema(self) -> None:
        conn = self._get_connection()
        for table_name, expected_columns in LEGACY_COLUMN_REPAIRS.items():
            if not self._table_exists(table_name):
                continue
            existing_columns = self._table_columns(table_name)
            for column_name, column_sql in expected_columns.items():
                if column_name in existing_columns:
                    continue
                conn.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"
                )

    def put_memory(self, memory: Memory) -> bool:
        return self.memory.put_memory(memory)

    def put_evidence_event(self, event: EvidenceEvent) -> EvidenceEvent:
        return self.evidence.put_evidence_event(event)

    def create_evidence_event(
        self,
        *,
        scope_type: str,
        scope_id: str,
        raw_content: str,
        source_kind: str,
        session_id: str | None = None,
        source_ref: str | None = None,
        memory_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceEvent:
        return self.evidence.create_evidence_event(
            scope_type=scope_type,
            scope_id=scope_id,
            raw_content=raw_content,
            source_kind=source_kind,
            session_id=session_id,
            source_ref=source_ref,
            memory_id=memory_id,
            metadata=metadata,
        )

    def get_evidence_event(self, event_id: str) -> EvidenceEvent | None:
        return self.evidence.get_evidence_event(event_id)

    def list_evidence_events_for_memory(self, memory_id: str) -> list[EvidenceEvent]:
        return self.evidence.list_evidence_events_for_memory(memory_id)

    def get_linked_evidence_for_memory(self, memory_id: str) -> list[EvidenceEvent]:
        return self.evidence.get_linked_evidence_for_memory(memory_id)

    def summarize_evidence_coverage(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        return self.evidence.summarize_evidence_coverage(scope_type=scope_type, scope_id=scope_id)

    def get_memory_state(self, memory_id: str) -> dict[str, Any] | None:
        return self.memory.get_memory_state(memory_id)

    def summarize_memory_states(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
    ) -> dict[str, Any]:
        return self.memory.summarize_memory_states(scope_type=scope_type, scope_id=scope_id)

    def record_memory_state_transition(
        self,
        *,
        memory_id: str,
        from_state: str | None,
        to_state: str,
        reason: str,
        actor: str = "system",
        policy_name: str | None = None,
        evidence_event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        return self.governance.record_memory_state_transition(
            memory_id=memory_id,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            actor=actor,
            policy_name=policy_name,
            evidence_event_id=evidence_event_id,
            details=details,
        )

    def list_memory_state_transitions(self, memory_id: str) -> list[dict[str, Any]]:
        return self.governance.list_memory_state_transitions(memory_id)

    def record_governance_event(
        self,
        *,
        event_kind: str,
        scope_type: str,
        scope_id: str,
        memory_id: str | None = None,
        evidence_event_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> str:
        return self.governance.record_governance_event(
            event_kind=event_kind,
            scope_type=scope_type,
            scope_id=scope_id,
            memory_id=memory_id,
            evidence_event_id=evidence_event_id,
            payload=payload,
        )

    def list_governance_events(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self.governance.list_governance_events(
            scope_type=scope_type,
            scope_id=scope_id,
            memory_id=memory_id,
            limit=limit,
        )

    def record_evidence_artifact(
        self,
        *,
        artifact_kind: str,
        scope_type: str,
        scope_id: str,
        payload: dict[str, Any],
        memory_id: str | None = None,
        evidence_event_id: str | None = None,
    ) -> str:
        return self.evidence.record_evidence_artifact(
            artifact_kind=artifact_kind,
            scope_type=scope_type,
            scope_id=scope_id,
            payload=payload,
            memory_id=memory_id,
            evidence_event_id=evidence_event_id,
        )

    def list_evidence_artifacts(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        memory_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self.evidence.list_evidence_artifacts(
            scope_type=scope_type,
            scope_id=scope_id,
            memory_id=memory_id,
            limit=limit,
        )

    def record_background_intelligence_run(
        self,
        *,
        scope_type: str,
        scope_id: str,
        worker_kind: str,
        proposal: dict[str, Any],
        mode: str = "working_copy",
        status: str = "planned",
    ) -> str:
        return self.governance.record_background_intelligence_run(
            scope_type=scope_type,
            scope_id=scope_id,
            worker_kind=worker_kind,
            proposal=proposal,
            mode=mode,
            status=status,
        )

    def get_background_intelligence_run(self, run_id: str) -> dict[str, Any] | None:
        return self.governance.get_background_intelligence_run(run_id)

    def list_background_intelligence_runs(
        self,
        *,
        scope_type: str,
        scope_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.governance.list_background_intelligence_runs(
            scope_type=scope_type,
            scope_id=scope_id,
            status=status,
        )

    def update_background_intelligence_run(
        self,
        run_id: str,
        *,
        status: str,
        proposal: dict[str, Any] | None = None,
    ) -> None:
        self.governance.update_background_intelligence_run(
            run_id,
            status=status,
            proposal=proposal,
        )

    def execute(self, query: str, params=()):
        conn = self._get_connection()
        cursor = conn.execute(query, tuple(params))
        conn.commit()
        return cursor

    def executemany(self, query: str, rows) -> None:
        conn = self._get_connection()
        conn.executemany(query, rows)
        conn.commit()

    def fetch_all(self, query: str, params=()):
        conn = self._get_connection()
        cursor = conn.execute(query, tuple(params))
        return cursor.fetchall()

    def fetch_one(self, query: str, params=()):
        conn = self._get_connection()
        cursor = conn.execute(query, tuple(params))
        return cursor.fetchone()

    def get_memory(self, memory_id: str) -> Optional[Memory]:
        return self.memory.get_memory(memory_id)

    def index_memory_vector(self, memory_id: str) -> None:
        self.memory.index_memory_vector(memory_id)

    def search_memory_vectors(
        self,
        *,
        query: str,
        scope_type: str,
        scope_id: str,
        include_global: bool = False,
        limit: int = 10,
        min_similarity: float = 0.12,
    ) -> list[dict[str, Any]]:
        return self.memory.search_memory_vectors(
            query=query,
            scope_type=scope_type,
            scope_id=scope_id,
            include_global=include_global,
            limit=limit,
            min_similarity=min_similarity,
        )

    def search_fts(self, query: str, scope_type: str, scope_id: str, limit: int = 10, include_global: bool = True) -> List[tuple[Memory, float]]:
        return self.memory.search_fts(
            query,
            scope_type,
            scope_id,
            limit=limit,
            include_global=include_global,
        )

    def reinforce_memory(self, memory_id: str, increment: float = 1.0, max_score: float = 10.0):
        self.memory.reinforce_memory(memory_id, increment=increment, max_score=max_score)

    def apply_decay(self, half_life_days: float = 7.0, type_half_lives: dict[str, float] | None = None):
        self.memory.apply_decay(half_life_days=half_life_days, type_half_lives=type_half_lives)

    def apply_retention_policy(
        self,
        *,
        thresholds: dict[str, tuple[float, float, float]] | None = None,
    ) -> dict[str, int]:
        return self.memory.apply_retention_policy(thresholds=thresholds or RETENTION_THRESHOLDS)

    def archive_expired(self, session_id: Optional[str] = None):
        self.memory.archive_expired(session_id=session_id)

    def storage_footprint(self) -> dict[str, Any]:
        return self.storage_hygiene.storage_footprint()

    def compact_storage(
        self,
        *,
        archived_memory_days: int = DEFAULT_COMPACTION_POLICY["archived_memory_days"],
        superseded_memory_days: int = DEFAULT_COMPACTION_POLICY["superseded_memory_days"],
        evidence_days: int = DEFAULT_COMPACTION_POLICY["evidence_days"],
        governance_days: int = DEFAULT_COMPACTION_POLICY["governance_days"],
        replication_days: int = DEFAULT_COMPACTION_POLICY["replication_days"],
        background_days: int = DEFAULT_COMPACTION_POLICY["background_days"],
        vacuum: bool = True,
    ) -> dict[str, Any]:
        return self.storage_hygiene.compact_storage(
            archived_memory_days=archived_memory_days,
            superseded_memory_days=superseded_memory_days,
            evidence_days=evidence_days,
            governance_days=governance_days,
            replication_days=replication_days,
            background_days=background_days,
            vacuum=vacuum,
        )

    def _row_to_memory(self, row: Any) -> Memory:
        data = dict(row)
        # Parse ISO strings back to datetime
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        if data.get('last_accessed_at'):
            data['last_accessed_at'] = datetime.fromisoformat(data['last_accessed_at'])
        if data.get('archived_at'):
            data['archived_at'] = datetime.fromisoformat(data['archived_at'])
        
        if isinstance(data['metadata_json'], str):
            data['metadata_json'] = json.loads(data['metadata_json'])
        data['metadata'] = data.pop('metadata_json')
        return Memory(**data)

    def _row_to_evidence_event(self, row: Any) -> EvidenceEvent:
        data = dict(row)
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("metadata_json"), str):
            data["metadata_json"] = json.loads(data["metadata_json"])
        data["metadata"] = data.pop("metadata_json")
        return EvidenceEvent(**data)

    def put_signal(self, signal: Any): # StyleSignal
        self.scope.put_signal(signal)

    def get_profile(self, scope_id: str, scope_type: str) -> Optional[Any]: # StyleProfile
        return self.scope.get_profile(scope_id, scope_type)

    def upsert_profile(self, profile: Any): # StyleProfile
        self.scope.upsert_profile(profile)

    def set_scope_policy(
        self,
        scope_type: str,
        scope_id: str,
        *,
        sync_policy: str,
        sync_state: str = "local",
        last_sync_at: str | None = None,
    ) -> None:
        self.scope.set_scope_policy(
            scope_type,
            scope_id,
            sync_policy=sync_policy,
            sync_state=sync_state,
            last_sync_at=last_sync_at,
        )

    def get_scope_policy(self, scope_type: str, scope_id: str) -> dict[str, Any]:
        return self.scope.get_scope_policy(scope_type, scope_id)

    def list_scope_policies(self, sync_policy: str | None = None) -> list[dict[str, Any]]:
        return self.scope.list_scope_policies(sync_policy=sync_policy)

    def ensure_scope_revision(self, scope_type: str, scope_id: str, *, commit: bool = True) -> None:
        self.scope.ensure_scope_revision(scope_type, scope_id, commit=commit)

    def get_scope_revision(self, scope_type: str, scope_id: str) -> dict[str, Any]:
        return self.scope.get_scope_revision(scope_type, scope_id)

    def bump_scope_revision(self, scope_type: str, scope_id: str, *, commit: bool = True) -> dict[str, Any]:
        return self.scope.bump_scope_revision(scope_type, scope_id, commit=commit)

    def upsert_memory_link(
        self,
        *,
        source_id: str,
        target_id: str,
        link_type: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
        bump_revision: bool = True,
    ) -> dict[str, Any]:
        return self.graph.upsert_memory_link(
            source_id=source_id,
            target_id=target_id,
            link_type=link_type,
            weight=weight,
            metadata=metadata,
            commit=commit,
            bump_revision=bump_revision,
        )

    def list_memory_neighbors(
        self,
        *,
        memory_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self.graph.list_memory_neighbors(memory_id=memory_id, limit=limit)

    def list_link_expansions(
        self,
        *,
        seed_ids: list[str],
        scope_type: str,
        scope_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        return self.graph.list_link_expansions(
            seed_ids=seed_ids,
            scope_type=scope_type,
            scope_id=scope_id,
            limit=limit,
        )

    def find_same_subject_peers(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        subject: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        return self.memory.find_same_subject_peers(
            memory_id=memory_id,
            scope_type=scope_type,
            scope_id=scope_id,
            subject=subject,
            limit=limit,
        )

    def find_same_subject_typed_peers(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        subject: str,
        peer_type: str,
        limit: int = 5,
        ) -> list[dict[str, Any]]:
        return self.memory.find_same_subject_typed_peers(
            memory_id=memory_id,
            scope_type=scope_type,
            scope_id=scope_id,
            subject=subject,
            peer_type=peer_type,
            limit=limit,
        )

    def get_open_conflict_peers(self, memory_id: str) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.fetch_all(
                """
                SELECT
                    CASE
                        WHEN c.memory_a_id = ? THEN c.memory_b_id
                        ELSE c.memory_a_id
                    END AS peer_id,
                    c.subject_key,
                    c.score,
                    c.reason,
                    c.status
                FROM conflicts c
                WHERE c.status = 'open'
                  AND (c.memory_a_id = ? OR c.memory_b_id = ?)
                ORDER BY c.score DESC, c.created_at DESC
                """,
                (memory_id, memory_id, memory_id),
            )
        ]

    def count_links_by_type(self, *, link_type: str) -> int:
        return self.graph.count_links_by_type(link_type=link_type)

    def batch_count_evidence(self, memory_ids: list[str]) -> dict[str, int]:
        if not memory_ids:
            return {}
        placeholders = ",".join("?" for _ in memory_ids)
        rows = self.fetch_all(f"SELECT memory_id, COUNT(*) AS count FROM evidence_events WHERE memory_id IN ({placeholders}) GROUP BY memory_id", memory_ids)
        return {row["memory_id"]: int(row["count"]) for row in rows}

    def batch_support_weight(self, memory_ids: list[str]) -> dict[str, float]:
        if not memory_ids:
            return {}
        placeholders = ",".join("?" for _ in memory_ids)
        rows = self.fetch_all(f"""
            SELECT m.id AS memory_id,
                   COALESCE(SUM(CASE
                       WHEN ml.link_type IN ('same_subject', 'supports', 'extends', 'procedural_supports_semantic')
                       THEN ml.weight
                       ELSE 0
                   END), 0) AS total
            FROM memories m
            LEFT JOIN memory_links ml ON (m.id = ml.source_id OR m.id = ml.target_id)
            WHERE m.id IN ({placeholders})
            GROUP BY m.id
        """, memory_ids)
        return {row["memory_id"]: float(row["total"]) for row in rows}

    def batch_conflict_weight(self, memory_ids: list[str]) -> dict[str, tuple[float, bool]]:
        if not memory_ids:
            return {}
        placeholders = ",".join("?" for _ in memory_ids)
        rows = self.fetch_all(f"""
            SELECT
                target_mem_id AS memory_id,
                COALESCE(SUM(m.confidence), 0) AS weight,
                MAX(1) AS has_open
            FROM (
                SELECT memory_a_id AS target_mem_id, memory_b_id AS peer_id
                FROM conflicts
                WHERE status = 'open' AND memory_a_id IN ({placeholders})
                UNION ALL
                SELECT memory_b_id AS target_mem_id, memory_a_id AS peer_id
                FROM conflicts
                WHERE status = 'open' AND memory_b_id IN ({placeholders})
            ) peer_map
            JOIN memories m ON m.id = peer_map.peer_id
            GROUP BY target_mem_id
        """, memory_ids * 2)
        
        result = {m_id: (0.0, False) for m_id in memory_ids}
        for row in rows:
            result[row["memory_id"]] = (float(row["weight"]), bool(row["has_open"]))
        return result

    def list_entity_peers(
        self,
        *,
        memory_id: str,
        scope_type: str,
        scope_id: str,
        entities: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self.memory.list_entity_peers(
            memory_id=memory_id,
            scope_type=scope_type,
            scope_id=scope_id,
            entities=entities,
            limit=limit,
        )

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _transition_memory(
        self,
        memory_id: str,
        *,
        status: str,
        event: str,
        archived_at: str | None = None,
        expires_at: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        before = self.get_memory_state(memory_id)
        transition_memory(
            self,
            memory_id,
            status=status,
            event=event,
            archived_at=archived_at,
            expires_at=expires_at,
            details=details,
        )
        row = self.fetch_one("SELECT metadata_json, status FROM memories WHERE id = ?", (memory_id,))
        if row is None:
            return
        metadata = self._ensure_memory_state(
            metadata=self._coerce_metadata(row["metadata_json"]),
            status=row["status"],
        )
        metadata["memory_state"] = self._derive_memory_state(
            metadata=metadata,
            status=row["status"],
        )
        metadata = self._ensure_admission_state(
            metadata=metadata,
            status=row["status"],
        )
        self.execute(
            "UPDATE memories SET metadata_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(metadata, ensure_ascii=True), now_iso(), memory_id),
        )
        after_state = metadata["memory_state"]
        before_state = before["memory_state"] if before else None
        if before_state != after_state:
            self.record_memory_state_transition(
                memory_id=memory_id,
                from_state=before_state,
                to_state=after_state,
                reason=event,
                actor="system",
                details=details,
            )

    def _coerce_metadata(self, raw: Any) -> dict[str, Any]:
        return coerce_metadata(raw)

    def _now_iso(self) -> str:
        return now_iso()

    def _ensure_admission_state(
        self,
        *,
        metadata: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        normalized = self._coerce_metadata(metadata)
        state = normalized.get("admission_state")
        if not isinstance(state, str) or not state.strip():
            normalized["admission_state"] = self._derive_admission_state(
                metadata=normalized,
                status=status,
            )
        return normalized

    def _ensure_memory_state(
        self,
        *,
        metadata: dict[str, Any],
        status: str,
    ) -> dict[str, Any]:
        normalized = self._coerce_metadata(metadata)
        state = normalized.get("memory_state")
        if not isinstance(state, str) or not state.strip():
            normalized["memory_state"] = self._derive_memory_state(
                metadata=normalized,
                status=status,
            )
        return normalized

    def _derive_admission_state(
        self,
        *,
        metadata: dict[str, Any],
        status: str,
    ) -> str:
        explicit_state = metadata.get("memory_state")
        if explicit_state == "archived":
            return "archived"
        if isinstance(explicit_state, str) and explicit_state in ADMISSION_STATES:
            return explicit_state
        promotion = metadata.get("promotion")
        reasons = promotion.get("reasons", []) if isinstance(promotion, dict) else []
        if status == "superseded":
            return "invalidated"
        if status in {"archived", "expired"}:
            return "archived" if status == "archived" else "consolidated"
        if isinstance(promotion, dict) and promotion.get("promotable") is False:
            return "draft"
        if "review_contradiction_risk" in reasons or "contradiction_risk_detected" in reasons:
            return "hypothesized"
        return "validated"

    def _derive_memory_state(
        self,
        *,
        metadata: dict[str, Any],
        status: str,
    ) -> str:
        if status == "superseded":
            return "invalidated"
        if status == "archived":
            return "archived"
        if status == "expired":
            return "consolidated"
        explicit_state = metadata.get("memory_state")
        if isinstance(explicit_state, str) and explicit_state.strip():
            return explicit_state
        promotion = metadata.get("promotion")
        reasons = promotion.get("reasons", []) if isinstance(promotion, dict) else []
        if isinstance(promotion, dict) and promotion.get("promotable") is False:
            return "draft"
        if "review_contradiction_risk" in reasons or "contradiction_risk_detected" in reasons:
            return "hypothesized"
        return "validated"

    def _embed_text(self, text: str) -> dict[str, float]:
        tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        filtered = [token for token in tokens if len(token) >= 1]
        if not filtered:
            return {}
        counts: dict[str, float] = {}
        for token in filtered:
            counts[token] = counts.get(token, 0.0) + 1.0
        norm = math.sqrt(sum(value * value for value in counts.values()))
        if norm <= 0:
            return {}
        return {token: round(value / norm, 8) for token, value in counts.items()}

    def _cosine_similarity(self, left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(value * right.get(token, 0.0) for token, value in left.items())

    def _ensure_memory_evidence(self, memory: Memory) -> dict[str, Any]:
        metadata = self._coerce_metadata(memory.metadata)
        evidence = metadata.get("evidence")
        if isinstance(evidence, dict) and evidence.get("event_id"):
            metadata["evidence"] = evidence
            memory.metadata = metadata
            return {"event_id": evidence["event_id"], "metadata": metadata}

        event = self.create_evidence_event(
            scope_type=memory.scope_type,
            scope_id=memory.scope_id,
            session_id=memory.session_id,
            memory_id=memory.id,
            source_kind=memory.source_kind,
            source_ref=memory.source_ref,
            raw_content=memory.content,
            metadata={
                "capture_stage": "storage_backfill",
                "memory_type": memory.type,
            },
        )
        metadata["evidence"] = {
            "event_id": event.id,
            "kind": "raw_ingest",
            "source_kind": event.source_kind,
            "source_ref": event.source_ref,
            "captured_at": event.created_at.isoformat(),
        }
        memory.metadata = metadata
        return {"event_id": event.id, "metadata": metadata}

    def _set_retention_stage(
        self,
        memory_id: str,
        *,
        stage: str,
        current_status: str,
        archived_at: str | None,
        at: str,
        score: float,
    ) -> None:
        row = self.fetch_one("SELECT metadata_json FROM memories WHERE id = ?", (memory_id,))
        if row is None:
            return
        metadata = self._coerce_metadata(row["metadata_json"])
        previous_stage = metadata.get("retention_stage")
        metadata["retention_stage"] = stage
        metadata["retention_last_score"] = round(score, 6)
        metadata_json = json.dumps(metadata, ensure_ascii=True)
        if current_status == "active" and stage in {"archive_candidate", "deprecated_candidate"}:
            if previous_stage != stage:
                transition_memory(
                    self,
                    memory_id,
                    status="archived",
                    event="archived_by_decay_policy",
                    archived_at=archived_at or at,
                    details={"retention_stage": stage, "score": round(score, 6)},
                    at=at,
                )
                refreshed = self.fetch_one("SELECT metadata_json FROM memories WHERE id = ?", (memory_id,))
                current_metadata = self._coerce_metadata(refreshed["metadata_json"]) if refreshed is not None else {}
                current_metadata["retention_stage"] = stage
                current_metadata["retention_last_score"] = round(score, 6)
                self.execute(
                    "UPDATE memories SET metadata_json = ?, updated_at = ? WHERE id = ?",
                    (json.dumps(current_metadata, ensure_ascii=True), at, memory_id),
                )
            return
        if previous_stage == stage:
            self.execute(
                "UPDATE memories SET metadata_json = ?, updated_at = ? WHERE id = ?",
                (metadata_json, at, memory_id),
            )
            return
        metadata.setdefault("lifecycle_events", []).append(
            {"event": "retention_stage_updated", "at": at, "retention_stage": stage, "score": round(score, 6)}
        )
        self.execute(
            "UPDATE memories SET metadata_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(metadata, ensure_ascii=True), at, memory_id),
        )
