from .librarian import LibrarianBeast
from .consolidator import ConsolidatorBeast
from .decay import DecayBeast
from .axolotl import AxolotlBeast
from .bowerbird import BowerbirdBeast
from .nutcracker import NutcrackerBeast
from ..storage.manager import StorageManager
from ..conflict.core import ConflictManager

class HygieneEngine:
    """Handles memory maintenance: decay, reinforcement triggers, and cleanup."""

    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.librarian = LibrarianBeast(storage)
        self.consolidator = ConsolidatorBeast(storage)
        self.conflict_manager = ConflictManager(storage)
        self.decay_beast = DecayBeast(storage)
        self.axolotl = AxolotlBeast(storage)
        self.bowerbird = BowerbirdBeast(storage)
        self.nutcracker = NutcrackerBeast(storage)

    def run_maintenance(self, half_life_days: float | None = None):
        """Performs full system hygiene."""
        diplocaulus = self.axolotl.validate_integrity()

        # 1. Apply aging
        if half_life_days is None:
            self.decay_beast.apply_typed_decay()
        else:
            self.storage.apply_decay(half_life_days=half_life_days)
        self.decay_beast.crystallize_hot_memories()
        self.decay_beast.retire_pressure_candidates()
        self.storage.apply_retention_policy()
        
        # 2. Clean up dead nodes
        self.storage.archive_expired()

        # 3. Repair & Taxonomy Cleanup
        if diplocaulus.diplocaulus_regeneration_score >= 0.45:
            self.bowerbird.normalize_subjects()

            # 4. Scan and Resolve conflicts (Corrections)
            self._detect_and_resolve_conflicts()

            # 5. Consolidate semantic duplicates (subject-based)
            self._consolidate_all_subjects()

        # 6. Final vacuum
        if self.nutcracker.check_db_health().deinosuchus_compaction_pressure >= 0.32:
            self.nutcracker.vacuum_db()

    def _detect_and_resolve_conflicts(self):
        """Finds contradictions and auto-resolves if recency-based corrections."""
        subjects = self.storage.fetch_all(
            "SELECT DISTINCT subject FROM memories WHERE status = 'active' AND subject IS NOT NULL"
        )
        for row in subjects:
            self.conflict_manager.scan_conflicts(row["subject"])
        
        # Resolve corrections
        self.consolidator.resolve_corrections()

    def _consolidate_all_subjects(self) -> int:
        """Scan active subjects and consolidate clusters."""
        subjects = self.storage.fetch_all(
            "SELECT DISTINCT scope_type, scope_id, subject FROM memories WHERE status = 'active' AND subject IS NOT NULL"
        )
        total_merged = 0
        for row in subjects:
            total_merged += self.librarian.consolidate_equivalents(
                row["scope_type"], row["scope_id"], row["subject"]
            )
        return total_merged

    def on_session_end(self, session_id: str):
        """Handles lifecycle triggers when a session closes."""
        self.storage.archive_expired(session_id=session_id)
