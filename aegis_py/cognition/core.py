from __future__ import annotations

import uuid
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StyleTracker:
    """Tracks bounded response-style preference signals."""

    def __init__(self, db_manager):
        self.db = db_manager

    def log_signal(self, signal: str, agent_id: str = "default", weight: float = 1.0) -> bool:
        self.db.execute(
            """
            INSERT INTO style_signals (id, agent_id, signal, weight, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), agent_id, signal, weight, _now_iso()),
        )
        return True

    def get_style_hints(self, agent_id: str = "default") -> str:
        results = self.db.fetch_all(
            """
            SELECT signal, SUM(weight) AS total_weight
            FROM style_signals
            WHERE agent_id = ?
            GROUP BY signal
            ORDER BY total_weight DESC
            LIMIT 5
            """,
            (agent_id,),
        )
        if not results:
            return ""
        hints = [row["signal"].replace("_", " ") for row in results]
        return "User prefers: " + ", ".join(hints) + "."

    def clear_signals(self, agent_id: str = "default") -> bool:
        self.db.execute("DELETE FROM style_signals WHERE agent_id = ?", (agent_id,))
        return True
