#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import uuid

from aegis_py.app import AegisApp
from aegis_py.conflict.core import ConflictManager
from aegis_py.retrieval.v8_benchmark import (
    V8BenchmarkThresholds,
    V8FeedbackCase,
    V8RetrievalCase,
    V8TransitionCase,
    evaluate_v8_benchmark,
    run_v8_dynamics_benchmark,
)


def main() -> int:
    workspace = Path("/tmp") / f"aegis_v8_benchmark_{uuid.uuid4().hex[:8]}"
    workspace.mkdir(parents=True, exist_ok=True)
    app = AegisApp(db_path=str(workspace / "v8_benchmark.db"))

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

    summary = run_v8_dynamics_benchmark(
        app,
        retrieval_cases=[
            V8RetrievalCase(
                query="release plan checklist",
                scope_type="project",
                scope_id="V8",
                expected_top_id=strong.id,
                expected_reason_tags=["v8_evidence_strong", "v8_trust_elevated"],
            ),
            V8RetrievalCase(
                query="deployment runbook",
                scope_type="project",
                scope_id="V8",
                expected_top_id=warm.id,
                expected_reason_tags=["v8_usage_reinforced"],
            ),
        ],
        transition_cases=[
            V8TransitionCase(memory_id=draft.id, expected_recommended_state="validated"),
            V8TransitionCase(memory_id=demote.id, expected_recommended_state="hypothesized"),
        ],
        feedback_cases=[
            V8FeedbackCase(
                query="deployment runbook",
                scope_type="project",
                scope_id="V8",
                selected_memory_ids=[warm.id],
                override_memory_ids=[cold.id],
                success_score=1.0,
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
            transition_gate_accuracy_min=1.0,
            feedback_alignment_rate_min=1.0,
            objective_regression_max=0.05,
            bundle_energy_max=1.5,
            bundle_objective_max=1.5,
            latency_p95_ms_max=50.0,
        ),
    )
    print(
        json.dumps(
            {
                "retrieval_hit_rate": round(summary.retrieval_hit_rate, 3),
                "signal_coverage": round(summary.signal_coverage, 3),
                "dynamic_reason_coverage": round(summary.dynamic_reason_coverage, 3),
                "transition_gate_accuracy": round(summary.transition_gate_accuracy, 3),
                "feedback_alignment_rate": round(summary.feedback_alignment_rate, 3),
                "objective_regression_mean": round(summary.objective_regression_mean, 3),
                "bundle_energy_mean": round(summary.bundle_energy_mean, 3),
                "bundle_objective_mean": round(summary.bundle_objective_mean, 3),
                "latency_p95_ms": round(summary.latency_p95_ms, 3),
                "passed": gate.passed,
                "failures": gate.failures,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
