from aegis_py.retrieval.models import SearchQuery
from aegis_py.storage.models import Memory
from aegis_py.v10.engine import GovernanceEngineV10
from aegis_py.v10.models import GovernanceStatus, RetrievableMode, TruthRole
from aegis_py.v10_scoring.models import (
    ConflictSignals,
    CorrectionSignals,
    LifecycleSignals,
    MemoryRecordV10,
    TrustSignals,
)


def test_tyrannosaurus_dominance_boost_surfaces_in_pipeline(runtime_harness):
    winner = Memory(
        id="trex_winner",
        type="semantic",
        content="The flagship color is crimson.",
        subject="flagship.color",
        confidence=1.0,
        activation_score=1.0,
        source_kind="manual",
        source_ref="test://trex/winner",
        scope_type="agent",
        scope_id="default",
        metadata={"is_winner": True},
    )
    contender = Memory(
        id="trex_contender",
        type="semantic",
        content="The flagship color might be red.",
        subject="flagship.color",
        confidence=0.82,
        activation_score=0.95,
        source_kind="message",
        source_ref="test://trex/contender",
        scope_type="agent",
        scope_id="default",
    )

    runtime_harness.put(winner)
    runtime_harness.put(contender)
    runtime_harness.sync_fts()

    results = runtime_harness.pipeline.search(
        SearchQuery(query="flagship color", scope_type="agent", scope_id="default", min_score=-10.0)
    )

    assert results[0].memory.id == "trex_winner"
    assert results[0].v10_trace.factors["tyrannosaurus_dominance_boost"] > 0.0
    assert "trex_dominance_boost" in results[0].v10_decision.decision_reason


def test_archelon_invariants_surface_for_winner_and_superseded(runtime_harness):
    engine = GovernanceEngineV10(runtime_harness.storage)

    winner_record = MemoryRecordV10(
        id="archelon_winner",
        content="Current truth winner",
        canonical_subject="truth.slot",
        fact_slot="truth.slot",
        memory_type="semantic",
        trust=TrustSignals(),
        conflict=ConflictSignals(unresolved_contradiction=0.0),
        correction=CorrectionSignals(is_slot_winner=True, is_superseded=False),
        lifecycle=LifecycleSignals(),
        metadata={"is_winner": True},
    )
    winner_decision = engine.govern(
        winner_record,
        {"semantic_relevance": 0.0, "lexical_match": 0.0, "scope_fit": 0.0, "link_support": 0.0},
        intent="normal_recall",
    )

    assert winner_decision.truth_role == TruthRole.WINNER
    assert winner_decision.governance_status == GovernanceStatus.ACTIVE
    assert winner_decision.retrievable_mode == RetrievableMode.NORMAL
    assert "ARCHELON_WINNER_INVARIANT" in winner_decision.policy_trace

    superseded_record = MemoryRecordV10(
        id="archelon_superseded",
        content="Old truth",
        canonical_subject="truth.slot",
        fact_slot="truth.slot",
        memory_type="semantic",
        trust=TrustSignals(),
        conflict=ConflictSignals(unresolved_contradiction=0.0),
        correction=CorrectionSignals(is_slot_winner=False, is_superseded=True),
        lifecycle=LifecycleSignals(),
        metadata={},
    )
    superseded_decision = engine.govern(
        superseded_record,
        {"semantic_relevance": 1.0, "lexical_match": 1.0, "scope_fit": 1.0, "link_support": 0.0},
        intent="normal_recall",
    )

    assert superseded_decision.governance_status == GovernanceStatus.SUPERSEDED
    assert superseded_decision.retrievable_mode == RetrievableMode.AUDIT
    assert "ARCHELON_SUPERSEDED_INVARIANT" in superseded_decision.policy_trace
