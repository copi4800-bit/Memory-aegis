from __future__ import annotations

from pathlib import Path
from typing import Optional

from aegis_py.facade import Aegis


class TruthKeep(Aegis):
    """Public correctness-first facade for TruthKeep Memory."""

    @classmethod
    def auto(cls, db_path: Optional[str] = None) -> "TruthKeep":
        if db_path is None:
            default_dir = Path.home() / ".openclaw"
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(default_dir / "truthkeep_v10.db")
        return super().auto(db_path=db_path)
