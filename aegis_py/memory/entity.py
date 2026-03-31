from __future__ import annotations

import re


ENTITY_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9_-]{2,}|[A-Z0-9]{2,})\b")


class EntityExtractor:
    """Heuristic local-only entity tag extractor."""

    def extract(self, *, content: str, subject: str | None = None) -> list[str]:
        entities: set[str] = set()
        for match in ENTITY_PATTERN.findall(content):
            entities.add(match.lower())
        if subject:
            for part in subject.split("."):
                token = part.strip().lower()
                if len(token) >= 3:
                    entities.add(token)
        return sorted(entities)[:8]
