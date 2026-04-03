from typing import Any
from ..storage.manager import StorageManager
from ..memory.normalizer import SubjectNormalizer

class BowerbirdBeast:
    """Taxonomy cleanup and subject normalization."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage
        self.normalizer = SubjectNormalizer()

    def normalize_subjects(self):
        """Chuẩn hóa subject names (e.g. lowercase, strip whitespace)."""
        conn = self.storage._get_connection()
        # Find all distinct subjects
        rows = self.storage.fetch_all("SELECT DISTINCT subject FROM memories WHERE subject IS NOT NULL")
        normalized_count = 0
        for row in rows:
            subject = row["subject"]
            profile = self.normalizer.profile(subject)
            normalized = profile.canonical_subject
            if subject != normalized:
                # Update all memories with this subject
                conn.execute(
                    "UPDATE memories SET subject = ? WHERE subject = ?",
                    (normalized, subject)
                )
                normalized_count += 1
        conn.commit()
        drift_candidates = self.detect_subject_drift()
        return {
            "normalized_count": normalized_count,
            "drift_candidates": len(drift_candidates),
            "oviraptor_taxonomy_order": round(min(0.99, 0.38 + (normalized_count * 0.12) + (len(drift_candidates) * 0.05)), 3),
        }

    def detect_subject_drift(self) -> list[dict[str, Any]]:
        """Tìm subjects tương tự cần merge (e.g. edit distance or subset)."""
        rows = self.storage.fetch_all("SELECT DISTINCT subject FROM memories WHERE subject IS NOT NULL")
        subjects = sorted([r["subject"] for r in rows if r["subject"]])
        
        drifts = []
        for i in range(len(subjects)):
            for j in range(i + 1, len(subjects)):
                s1, s2 = subjects[i], subjects[j]
                if s1 in s2 or s2 in s1:
                    shorter = min(len(s1), len(s2))
                    longer = max(len(s1), len(s2))
                    confidence = round(min(0.97, 0.62 + (shorter / max(1, longer)) * 0.28), 3)
                    drifts.append({"subject_1": s1, "subject_2": s2, "confidence": confidence})
        return drifts

    def assess_subject(self, subject: str | None) -> dict[str, Any]:
        profile = self.normalizer.profile(subject)
        canonical = profile.canonical_subject
        if not canonical:
            return {
                "canonical_subject": canonical,
                "drift_risk": 0.0,
                "taxonomy_guard": "clean",
                "closest_subject": None,
            }
        rows = self.storage.fetch_all(
            "SELECT DISTINCT subject FROM memories WHERE subject IS NOT NULL AND subject != ?",
            (canonical,),
        )
        best_match = None
        best_score = 0.0
        for row in rows:
            other = row["subject"]
            if not other:
                continue
            if canonical in other or other in canonical:
                shorter = min(len(canonical), len(other))
                longer = max(len(canonical), len(other))
                score = round(min(0.97, 0.62 + (shorter / max(1, longer)) * 0.28), 3)
                if score > best_score:
                    best_score = score
                    best_match = other
        if best_score >= 0.82:
            guard = "drift_risk"
        elif best_score >= 0.64:
            guard = "watchful"
        else:
            guard = "clean"
        return {
            "canonical_subject": canonical,
            "drift_risk": best_score,
            "taxonomy_guard": guard,
            "closest_subject": best_match,
        }

    def reclassify_untagged(self):
        """Gán lại general.untagged memories dựa trên content."""
        conn = self.storage._get_connection()
        rows = self.storage.fetch_all("SELECT id, content FROM memories WHERE subject IS NULL OR subject = 'general.untagged'")
        for row in rows:
            content = row["content"]
            new_subject = "general.untagged"
            if "error" in content.lower() or "bug" in content.lower():
                new_subject = "system.errors"
            elif "config" in content.lower():
                new_subject = "system.config"
                
            if new_subject != "general.untagged":
                conn.execute(
                    "UPDATE memories SET subject = ? WHERE id = ?",
                    (new_subject, row["id"])
                )
        conn.commit()

    def build_taxonomy_report(self) -> dict[str, Any]:
        rows = self.storage.fetch_all("SELECT DISTINCT subject FROM memories WHERE subject IS NOT NULL")
        subjects = [r["subject"] for r in rows if r["subject"]]
        normalized = [self.normalizer.profile(subject) for subject in subjects]
        stable = [item for item in normalized if item.ammonite_spiral_stability >= 0.72]
        drifts = sorted(self.detect_subject_drift(), key=lambda item: item["confidence"], reverse=True)
        oviraptor_taxonomy_order = round(
            min(0.99, 0.32 + (len(stable) * 0.06) + (max(0, len(subjects) - len(drifts)) * 0.01)),
            3,
        )
        if oviraptor_taxonomy_order >= 0.82:
            health_band = "ordered"
        elif oviraptor_taxonomy_order >= 0.64:
            health_band = "watchful"
        else:
            health_band = "messy"
        return {
            "subject_count": len(subjects),
            "stable_subjects": len(stable),
            "drift_candidates": len(drifts),
            "merge_recommendations": drifts[:3],
            "taxonomy_health_band": health_band,
            "oviraptor_taxonomy_order": oviraptor_taxonomy_order,
        }
