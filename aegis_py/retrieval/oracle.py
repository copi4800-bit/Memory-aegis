from __future__ import annotations

import logging
from ..storage.manager import StorageManager

logger = logging.getLogger(__name__)

class OracleBeast:
    """
    The Oracle Beast is responsible for semantic query expansion.
    It translates user intent and meaning into expanded search terms
    that can be used for lexical retrieval over local memory.
    """

    SYNONYM_MAP = {
        "phở bò": ["beef noodle soup", "vietnamese food", "beef soup"],
        "sqlite": ["sql", "database", "relational storage", "fts5"],
        "lỗi": ["bug", "error", "exception", "crash", "failure"],
        "tạo": ["create", "build", "generate", "make"],
        "xóa": ["delete", "remove", "destroy", "clear"]
    }

    def __init__(self, storage: StorageManager = None):
        self.storage = storage

    def _ngram_split(self, text: str, n: int = 2) -> list[str]:
        """Simple N-gram splitting for Vietnamese/languages without clear word boundaries."""
        words = text.split()
        if len(words) < n:
            return []
        ngrams = []
        for i in range(len(words) - n + 1):
            ngrams.append(" ".join(words[i:i+n]))
        return ngrams

    def expand_query(self, query: str, model: str | None = None) -> list[str]:
        """
        Expands the user query into a list of semantically related terms.
        Uses Synonym expansion, N-gram splitting, and Subject-based expansion.
        """
        try:
            if not query or len(query.strip()) < 3:
                return []

            expansions = []
            q_lower = query.lower()
            
            # 1. Canonical -> synonym expansion
            for key, synonyms in self.SYNONYM_MAP.items():
                if key in q_lower:
                    expansions.extend(synonyms)

            # 2. Reverse synonym expansion so English or alternate phrasing can
            # retrieve the canonical local phrasing stored in memory.
            for key, synonyms in self.SYNONYM_MAP.items():
                for synonym in synonyms:
                    synonym_lower = synonym.lower()
                    if synonym_lower in q_lower or q_lower in synonym_lower:
                        expansions.append(key)
                        expansions.extend(s for s in synonyms if s.lower() != synonym_lower)

            # 3. N-gram splitting cho Vietnamese text
            expansions.extend(self._ngram_split(q_lower, n=2))
            expansions.extend(self._ngram_split(q_lower, n=3))

            # 4. Subject-based expansion từ DB
            if self.storage:
                rows = self.storage.fetch_all(
                    "SELECT DISTINCT subject FROM memories WHERE subject LIKE ? LIMIT 5",
                    (f"%{q_lower}%",)
                )
                for row in rows:
                    if row["subject"]:
                        expansions.append(row["subject"])

            # Deduplicate and remove original query
            result = list(dict.fromkeys(expansions))
            if query in result:
                result.remove(query)
            if q_lower in result:
                result.remove(q_lower)
                
            return result
        except Exception as e:
            logger.error(f"OracleBeast expansion failed: {e}")
            return []
