from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory


def test_utahraptor_lexical_pursuit_surfaces_in_direct_recall(runtime_harness):
    runtime_harness.put(
        Memory(
            id="utahraptor_hit",
            type="semantic",
            content="The release schedule opens every Friday at 18:00.",
            subject="release.schedule",
            confidence=0.95,
            activation_score=1.08,
            source_kind="manual",
            source_ref="test://utahraptor",
            scope_type="agent",
            scope_id="prehistoric_tranche3",
            metadata={"is_winner": True},
        )
    )
    runtime_harness.sync_fts()

    results = runtime_harness.pipeline.search(
        SearchQuery(
            query="release schedule",
            scope_type="agent",
            scope_id="prehistoric_tranche3",
            include_global=False,
            min_score=-10.0,
        )
    )

    assert results
    assert results[0].memory.id == "utahraptor_hit"
    assert any(reason.startswith("utahraptor_lexical_pursuit:") for reason in results[0].reasons)


def test_basilosaurus_semantic_echo_surfaces_synonym_recall(runtime_harness):
    runtime_harness.put(
        Memory(
            id="basilosaurus_hit",
            type="semantic",
            content="SQLite with FTS5 is our preferred storage backend.",
            subject="storage.backend",
            confidence=0.94,
            activation_score=1.02,
            source_kind="manual",
            source_ref="test://basilosaurus",
            scope_type="agent",
            scope_id="prehistoric_tranche3",
            metadata={"is_winner": True},
        )
    )
    runtime_harness.sync_fts()

    results = runtime_harness.pipeline.search(
        SearchQuery(
            query="database backend",
            scope_type="agent",
            scope_id="prehistoric_tranche3",
            include_global=False,
            min_score=-10.0,
        )
    )

    assert results
    assert results[0].memory.id == "basilosaurus_hit"
    assert any(reason.startswith("basilosaurus_semantic_echo:") for reason in results[0].reasons)


def test_pterodactyl_graph_overview_surfaces_link_expansion(runtime_harness):
    seed = Memory(
        id="pterodactyl_seed",
        type="semantic",
        content="The backup window starts at 02:00.",
        subject="backup.window",
        confidence=0.96,
        activation_score=1.06,
        source_kind="manual",
        source_ref="test://pterodactyl-seed",
        scope_type="agent",
        scope_id="prehistoric_tranche3",
        metadata={"is_winner": True},
    )
    linked = Memory(
        id="pterodactyl_linked",
        type="procedural",
        content="Verify the archive checksum after the nightly run completes.",
        subject="backup.checksum",
        confidence=0.92,
        activation_score=1.0,
        source_kind="manual",
        source_ref="test://pterodactyl-linked",
        scope_type="agent",
        scope_id="prehistoric_tranche3",
        metadata={"is_winner": True},
    )
    runtime_harness.put(seed)
    runtime_harness.put(linked)
    runtime_harness.storage.upsert_memory_link(
        source_id="pterodactyl_seed",
        target_id="pterodactyl_linked",
        link_type="supports",
        weight=0.9,
        metadata={"source": "test://pterodactyl-link"},
    )
    runtime_harness.sync_fts()

    results = runtime_harness.pipeline.search(
        SearchQuery(
            query="backup window",
            scope_type="agent",
            scope_id="prehistoric_tranche3",
            include_global=False,
            min_score=-10.0,
        )
    )

    linked_result = next((item for item in results if item.memory.id == "pterodactyl_linked"), None)
    assert linked_result is not None
    assert linked_result.retrieval_stage == "link_expansion"
    assert any(reason.startswith("pterodactyl_graph_overview:") for reason in linked_result.reasons)
