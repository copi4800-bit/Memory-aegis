from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from aegis_py.memory.core import MemoryManager
from aegis_py.retrieval.search import SearchPipeline
from aegis_py.storage.manager import StorageManager
from aegis_py.storage.models import Memory


@dataclass
class RuntimeHarness:
    storage: StorageManager
    manager: MemoryManager
    pipeline: SearchPipeline

    def store(self, memory: Memory) -> Memory:
        self.manager.store(memory)
        return memory

    def put(self, memory: Memory) -> Memory:
        self.storage.put_memory(memory)
        return memory

    def sync_fts(self) -> None:
        self.storage.execute("DELETE FROM memories_fts")
        self.storage.execute(
            "INSERT INTO memories_fts(rowid, content, subject) SELECT rowid, content, subject FROM memories"
        )

    def add_evidence(
        self,
        memory_id: str,
        *,
        count: int,
        scope_type: str,
        scope_id: str,
        source_kind: str = "manual",
        source_ref: str = "test",
        raw_content: str = "Confirmed",
    ) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        for index in range(count):
            self.storage.execute(
                """
                INSERT INTO evidence_events (
                    id, scope_type, scope_id, memory_id, source_kind, source_ref, raw_content, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{memory_id}_ev_{index}",
                    scope_type,
                    scope_id,
                    memory_id,
                    source_kind,
                    source_ref,
                    raw_content,
                    created_at,
                ),
            )


@pytest.fixture
def runtime_harness(tmp_path):
    db_path = tmp_path / "aegis_test.db"
    storage = StorageManager(str(db_path))
    harness = RuntimeHarness(
        storage=storage,
        manager=MemoryManager(storage),
        pipeline=SearchPipeline(storage),
    )
    try:
        yield harness
    finally:
        storage.close()
