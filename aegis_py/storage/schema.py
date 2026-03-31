from __future__ import annotations

from pathlib import Path


# For legacy access to the baseline schema, we point to the first migration
SCHEMA_SQL = (Path(__file__).parent / "migrations" / "001_baseline.sql").read_text(encoding="utf-8")
