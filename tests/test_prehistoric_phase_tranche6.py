from aegis_py.hygiene.librarian import LibrarianBeast
from aegis_py.hygiene.nutcracker import NutcrackerBeast
from aegis_py.memory.weaver import WeaverBeast
from aegis_py.storage.models import Memory


def test_deinosuchus_compaction_pressure_surfaces_from_db_health(runtime_harness):
    runtime_harness.put(
        Memory(
            id="deinosuchus_archived",
            type="semantic",
            scope_type="agent",
            scope_id="prehistoric_tranche6",
            content="Archived storage fragment.",
            source_kind="manual",
            subject="archive.fragment",
            confidence=0.8,
            activation_score=0.3,
            status="archived",
            metadata={},
        )
    )
    runtime_harness.put(
        Memory(
            id="deinosuchus_superseded",
            type="semantic",
            scope_type="agent",
            scope_id="prehistoric_tranche6",
            content="Superseded storage fragment.",
            source_kind="manual",
            subject="archive.fragment.old",
            confidence=0.8,
            activation_score=0.3,
            status="superseded",
            metadata={},
        )
    )

    nutcracker = NutcrackerBeast(runtime_harness.storage)
    report = nutcracker.check_db_health()

    assert report.deinosuchus_compaction_pressure > 0.4


def test_titanoboa_index_locality_surfaces_subject_cluster_density(runtime_harness):
    for index in range(3):
        runtime_harness.put(
            Memory(
                id=f"titanoboa_{index}",
                type="semantic",
                scope_type="agent",
                scope_id="prehistoric_tranche6",
                content=f"Backup note {index}",
                source_kind="manual",
                subject="backup.window",
                confidence=0.9,
                activation_score=1.0,
                metadata={},
            )
        )
    runtime_harness.put(
        Memory(
            id="titanoboa_other",
            type="semantic",
            scope_type="agent",
            scope_id="prehistoric_tranche6",
            content="Different subject note",
            source_kind="manual",
            subject="deploy.window",
            confidence=0.9,
            activation_score=1.0,
            metadata={},
        )
    )

    librarian = LibrarianBeast(runtime_harness.storage)
    report = librarian.build_index_locality_report("agent", "prehistoric_tranche6")

    assert report["densest_cluster"] >= 3
    assert report["titanoboa_index_locality"] > 0.5


def test_megarachne_topology_strength_surfaces_from_neighbor_links(runtime_harness):
    seed = Memory(
        id="megarachne_seed",
        type="semantic",
        scope_type="agent",
        scope_id="prehistoric_tranche6",
        content="Seed memory.",
        source_kind="manual",
        subject="seed.memory",
        confidence=0.95,
        activation_score=1.0,
        metadata={},
    )
    peer_a = Memory(
        id="megarachne_peer_a",
        type="semantic",
        scope_type="agent",
        scope_id="prehistoric_tranche6",
        content="Peer A memory.",
        source_kind="manual",
        subject="peer.a",
        confidence=0.92,
        activation_score=0.95,
        metadata={},
    )
    peer_b = Memory(
        id="megarachne_peer_b",
        type="procedural",
        scope_type="agent",
        scope_id="prehistoric_tranche6",
        content="Peer B procedure.",
        source_kind="manual",
        subject="peer.b",
        confidence=0.91,
        activation_score=0.9,
        metadata={},
    )
    runtime_harness.put(seed)
    runtime_harness.put(peer_a)
    runtime_harness.put(peer_b)
    runtime_harness.storage.upsert_memory_link(
        source_id="megarachne_seed",
        target_id="megarachne_peer_a",
        link_type="supports",
        weight=0.9,
        metadata={"source": "test://megarachne-a"},
    )
    runtime_harness.storage.upsert_memory_link(
        source_id="megarachne_seed",
        target_id="megarachne_peer_b",
        link_type="equivalence",
        weight=0.85,
        metadata={"source": "test://megarachne-b"},
    )

    weaver = WeaverBeast(runtime_harness.storage)
    report = weaver.build_topology_report("megarachne_seed")

    assert report["edge_count"] == 2
    assert report["megarachne_topology_strength"] > 0.55

