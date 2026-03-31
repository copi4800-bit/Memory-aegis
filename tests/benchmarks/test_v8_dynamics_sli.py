from __future__ import annotations

import json

from aegis_py.app import AegisApp
from aegis_py.conflict.core import ConflictManager
from aegis_py.retrieval.v8_benchmark import (
    V8BenchmarkThresholds,
    V8FeedbackCase,
    V8ProfileSelection,
    V8RetrievalCase,
    V8TransitionCase,
    evaluate_v8_benchmark,
    run_v8_dynamics_benchmark,
    select_best_v8_profile,
)
from aegis_py.retrieval.v8_dynamics import DEFAULT_V8_DYNAMICS_PROFILE, with_profile


def _seed_v8_benchmark_app(tmp_path, db_name: str) -> tuple[AegisApp, dict[str, str]]:
    app = AegisApp(db_path=str(tmp_path / db_name))

    strong = app.put_memory(
        "Release plan evidence-backed checklist for launch.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://strong",
        subject="release.plan.strong",
    )
    weak = app.put_memory(
        "Release plan rumor checklist for launch.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://weak",
        subject="release.plan.weak",
    )
    challenger = app.put_memory(
        "Release plan rumor checklist is not approved.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://challenger",
        subject="release.plan.weak",
    )
    warm = app.put_memory(
        "Deployment runbook applies to release automation and rollback.",
        type="procedural",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://runbook",
        subject="deployment.runbook",
    )
    cold = app.put_memory(
        "Deployment runbook applies to release automation.",
        type="procedural",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://runbook-cold",
        subject="deployment.runbook.alt",
    )
    assert strong and weak and challenger and warm and cold

    app.storage.create_evidence_event(
        scope_type="project",
        scope_id="V8",
        memory_id=strong.id,
        source_kind="manual",
        source_ref="bench://strong/evidence",
        raw_content="Independent evidence confirms the release plan checklist.",
        metadata={"capture_stage": "benchmark"},
    )
    app.storage.execute("UPDATE memories SET access_count = ?, activation_score = ? WHERE id = ?", (8, 2.5, warm.id))

    draft = app.put_memory(
        "Validated release policy for launch trains.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://draft",
        subject="release.policy",
    )
    assert draft is not None
    draft_row = app.storage.get_memory(draft.id)
    draft_metadata = dict(draft_row.metadata)
    draft_metadata["memory_state"] = "draft"
    draft_metadata["admission_state"] = "draft"
    app.storage.execute(
        "UPDATE memories SET metadata_json = ?, access_count = ?, activation_score = ? WHERE id = ?",
        (json.dumps(draft_metadata, ensure_ascii=True), 10, 2.5, draft.id),
    )
    app.storage.create_evidence_event(
        scope_type="project",
        scope_id="V8",
        memory_id=draft.id,
        source_kind="manual",
        source_ref="bench://draft/evidence",
        raw_content="Operator evidence confirms the release policy.",
        metadata={"capture_stage": "benchmark"},
    )

    demote = app.put_memory(
        "The release gate is enabled for project v8.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://demote/a",
        subject="release.gate",
    )
    other_a = app.put_memory(
        "The release gate is not enabled for project v8.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://demote/b",
        subject="release.gate",
    )
    other_b = app.put_memory(
        "The release gate remains disabled for project v8 under rollback conditions.",
        type="semantic",
        scope_type="project",
        scope_id="V8",
        source_kind="manual",
        source_ref="bench://demote/c",
        subject="release.gate",
    )
    assert demote and other_a and other_b

    ConflictManager(app.storage).scan_conflicts("release.plan.weak")
    ConflictManager(app.storage).scan_conflicts("release.gate")
    app.storage.execute("DELETE FROM memory_links WHERE source_id = ? OR target_id = ?", (demote.id, demote.id))
    app.storage.execute("DELETE FROM evidence_events WHERE memory_id = ?", (demote.id,))
    app.storage.execute(
        "UPDATE memories SET access_count = ?, activation_score = ?, confidence = ? WHERE id = ?",
        (0, 1.0, 0.2, demote.id),
    )
    app.apply_v8_outcome_feedback(
        warm.id,
        success_score=1.0,
        relevance_score=1.0,
        override_score=0.0,
    )
    app.apply_v8_outcome_feedback(
        cold.id,
        success_score=0.2,
        relevance_score=0.2,
        override_score=0.8,
    )
    return app, {"strong": strong.id, "warm": warm.id, "cold": cold.id, "draft": draft.id, "demote": demote.id}


def test_v8_dynamics_benchmark_gate_for_runtime(tmp_path):
    app, ids = _seed_v8_benchmark_app(tmp_path, "v8_benchmark.db")

    summary = run_v8_dynamics_benchmark(
        app,
        retrieval_cases=[
            V8RetrievalCase(
                query="release plan checklist",
                scope_type="project",
                scope_id="V8",
                expected_top_id=ids["strong"],
                expected_reason_tags=["v8_evidence_strong", "v8_trust_elevated"],
                expected_signal_mins={"belief_score": 0.7, "trust_score": 0.84, "evidence_signal": 0.83},
            ),
            V8RetrievalCase(
                query="deployment runbook",
                scope_type="project",
                scope_id="V8",
                expected_top_id=ids["warm"],
                expected_reason_tags=["v8_usage_reinforced"],
                expected_signal_mins={"usage_signal": 0.8, "readiness_score": 0.9, "trust_score": 0.9},
            ),
        ],
        transition_cases=[
            V8TransitionCase(
                memory_id=ids["draft"],
                expected_recommended_state="validated",
                expected_signal_mins={"trust_score": 0.9, "evidence_signal": 0.83},
                expected_signal_maxs={"conflict_signal": 0.1},
            ),
            V8TransitionCase(
                memory_id=ids["demote"],
                expected_recommended_state="hypothesized",
                expected_signal_mins={"conflict_signal": 0.58},
                expected_signal_maxs={"trust_score": 0.6},
            ),
        ],
        feedback_cases=[
            V8FeedbackCase(
                query="deployment runbook",
                scope_type="project",
                scope_id="V8",
                selected_memory_ids=[ids["cold"]],
                success_score=1.0,
                selected_signal_increases=["usage_signal", "readiness_score", "trust_score"],
                selected_signal_decreases=["regret_signal"],
                limit=5,
            ),
            V8FeedbackCase(
                query="deployment runbook",
                scope_type="project",
                scope_id="V8",
                selected_memory_ids=[ids["warm"]],
                override_memory_ids=[ids["cold"]],
                success_score=1.0,
                override_signal_increases=["regret_signal"],
                override_signal_decreases=["usage_signal", "readiness_score", "trust_score"],
                limit=5,
            ),
        ],
    )
    gate = evaluate_v8_benchmark(
        summary,
        V8BenchmarkThresholds(
            retrieval_hit_rate_min=1.0,
            signal_coverage_min=1.0,
            dynamic_reason_coverage_min=1.0,
            retrieval_state_fidelity_min=1.0,
            transition_gate_accuracy_min=1.0,
            transition_state_fidelity_min=1.0,
            feedback_alignment_rate_min=1.0,
            feedback_state_fidelity_min=1.0,
            objective_regression_max=0.05,
            bundle_energy_max=1.5,
            bundle_objective_max=1.5,
            latency_p95_ms_max=50.0,
        ),
    )

    assert gate.passed, gate.failures
    assert summary.retrieval_state_fidelity >= 1.0
    assert summary.transition_state_fidelity >= 1.0
    assert summary.feedback_alignment_rate >= 1.0
    assert summary.feedback_state_fidelity >= 1.0
    assert summary.objective_regression_mean <= 0.05
    assert summary.bundle_energy_mean >= 0.0
    assert summary.bundle_objective_mean >= 0.0


def test_v8_profile_selector_prefers_seeded_benchmark_winner(tmp_path):
    _, ids = _seed_v8_benchmark_app(tmp_path, "v8_profile_selector.db")
    retrieval_cases = [
        V8RetrievalCase(
            query="release plan checklist",
            scope_type="project",
            scope_id="V8",
            expected_top_id=ids["strong"],
            expected_reason_tags=["v8_evidence_strong", "v8_trust_elevated"],
            expected_signal_mins={"belief_score": 0.7, "trust_score": 0.84, "evidence_signal": 0.83},
        ),
        V8RetrievalCase(
            query="deployment runbook",
            scope_type="project",
            scope_id="V8",
            expected_top_id=ids["warm"],
            expected_reason_tags=["v8_usage_reinforced"],
            expected_signal_mins={"usage_signal": 0.8, "readiness_score": 0.9, "trust_score": 0.9},
        ),
    ]

    def app_factory():
        return AegisApp(db_path=str(tmp_path / "v8_profile_selector.db"))

    thresholds = V8BenchmarkThresholds(
        retrieval_hit_rate_min=1.0,
        signal_coverage_min=1.0,
        dynamic_reason_coverage_min=1.0,
        retrieval_state_fidelity_min=1.0,
        transition_gate_accuracy_min=0.0,
        feedback_alignment_rate_min=0.0,
        objective_regression_max=None,
        bundle_energy_max=None,
        bundle_objective_max=None,
        latency_p95_ms_max=50.0,
    )
    selected = select_best_v8_profile(
        app_factory=app_factory,
        candidate_profiles={
            "baseline": DEFAULT_V8_DYNAMICS_PROFILE,
            "underpowered": with_profile(
                DEFAULT_V8_DYNAMICS_PROFILE,
                trust_evidence_weight=0.15,
                trust_belief_weight=0.15,
                score_bonus_trust_weight=0.01,
                transition_promote_trust=0.95,
            ),
        },
        retrieval_cases=retrieval_cases,
        transition_cases=[],
        feedback_cases=None,
        thresholds=thresholds,
    )

    assert isinstance(selected, V8ProfileSelection)
    assert selected.profile_name == "baseline"
    assert selected.gate.passed is True
