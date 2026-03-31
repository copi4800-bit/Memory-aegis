from typing import Any
from ..storage.manager import StorageManager

class BowerbirdBeast:
    """Taxonomy cleanup and subject normalization."""
    
    def __init__(self, storage: StorageManager):
        self.storage = storage

    def normalize_subjects(self):
        """Chuẩn hóa subject names (e.g. lowercase, strip whitespace)."""
        conn = self.storage._get_connection()
        # Find all distinct subjects
        rows = self.storage.fetch_all("SELECT DISTINCT subject FROM memories WHERE subject IS NOT NULL")
        for row in rows:
            subject = row["subject"]
            normalized = subject.strip().lower()
            if subject != normalized:
                # Update all memories with this subject
                conn.execute(
                    "UPDATE memories SET subject = ? WHERE subject = ?",
                    (normalized, subject)
                )
        conn.commit()

    def detect_subject_drift(self) -> list[dict[str, Any]]:
        """Tìm subjects tương tự cần merge (e.g. edit distance or subset)."""
        rows = self.storage.fetch_all("SELECT DISTINCT subject FROM memories WHERE subject IS NOT NULL")
        subjects = sorted([r["subject"] for r in rows if r["subject"]])
        
        drifts = []
        for i in range(len(subjects)):
            for j in range(i + 1, len(subjects)):
                s1, s2 = subjects[i], subjects[j]
                if s1 in s2 or s2 in s1:
                    drifts.append({"subject_1": s1, "subject_2": s2, "confidence": 0.8})
        return drifts

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
