from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from typing import Any

from aegis_py.app import AegisApp
from aegis_py.retrieval.v8_dynamics import (
    V8DynamicsProfile,
    get_active_v8_profile,
    reset_active_v8_profile,
    set_active_v8_profile,
)


@dataclass(frozen=True)
class V8RetrievalCase:
    query: str
    scope_type: str
    scope_id: str
    expected_top_id: str
    expected_reason_tags: list[str] = field(default_factory=list)
    expected_signal_mins: dict[str, float] = field(default_factory=dict)
    expected_signal_maxs: dict[str, float] = field(default_factory=dict)
    limit: int = 5


@dataclass(frozen=True)
class V8TransitionCase:
    memory_id: str
    expected_recommended_state: str
    expected_signal_mins: dict[str, float] = field(default_factory=dict)
    expected_signal_maxs: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class V8FeedbackCase:
    query: str
    scope_type: str
    scope_id: str
    selected_memory_ids: list[str]
    override_memory_ids: list[str] = field(default_factory=list)
    success_score: float = 1.0
    selected_signal_increases: list[str] = field(default_factory=list)
    selected_signal_decreases: list[str] = field(default_factory=list)
    override_signal_increases: list[str] = field(default_factory=list)
    override_signal_decreases: list[str] = field(default_factory=list)
    limit: int = 5


@dataclass
class V8BenchmarkSummary:
    retrieval_hit_rate: float
    signal_coverage: float
    dynamic_reason_coverage: float
    retrieval_state_fidelity: float
    transition_gate_accuracy: float
    transition_state_fidelity: float
    feedback_alignment_rate: float
    feedback_state_fidelity: float
    objective_regression_mean: float
    bundle_energy_mean: float
    bundle_objective_mean: float
    latency_p50_ms: float
    latency_p95_ms: float
    retrieval_cases: list[dict[str, Any]]
    transition_cases: list[dict[str, Any]]
    feedback_cases: list[dict[str, Any]]


@dataclass(frozen=True)
class V8BenchmarkThresholds:
    retrieval_hit_rate_min: float = 1.0
    signal_coverage_min: float = 1.0
    dynamic_reason_coverage_min: float = 1.0
    retrieval_state_fidelity_min: float = 0.0
    transition_gate_accuracy_min: float = 1.0
    transition_state_fidelity_min: float = 0.0
    feedback_alignment_rate_min: float = 1.0
    feedback_state_fidelity_min: float = 0.0
    objective_regression_max: float | None = 0.05
    bundle_energy_max: float | None = 1.5
    bundle_objective_max: float | None = 1.5
    latency_p95_ms_max: float | None = 50.0


@dataclass
class V8BenchmarkGateResult:
    passed: bool
    failures: list[str] = field(default_factory=list)


@dataclass
class V8ProfileSelection:
    profile_name: str
    profile: V8DynamicsProfile
    summary: V8BenchmarkSummary
    gate: V8BenchmarkGateResult


def run_v8_dynamics_benchmark(
    app: AegisApp,
    *,
    retrieval_cases: list[V8RetrievalCase],
    transition_cases: list[V8TransitionCase],
    feedback_cases: list[V8FeedbackCase] | None = None,
) -> V8BenchmarkSummary:
    retrieval_payloads: list[dict[str, Any]] = []
    transition_payloads: list[dict[str, Any]] = []
    feedback_payloads: list[dict[str, Any]] = []
    latencies: list[float] = []

    for case in retrieval_cases:
        started = time.perf_counter()
        results = app.search(
            case.query,
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            limit=case.limit,
            fallback_to_or=True,
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        latencies.append(latency_ms)
        top_id = results[0].memory.id if results else None
        top_reasons = results[0].reasons if results else []
        top_signals = dict(results[0].v8_core_signals or {}) if results and results[0].v8_core_signals is not None else {}
        snapshot = app.v8_bundle_snapshot(
            query=case.query,
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            limit=case.limit,
            include_global=True,
        )["snapshot"]
        signal_coverage = (
            sum(1 for result in results if getattr(result, "v8_core_signals", None) is not None) / len(results)
            if results
            else 0.0
        )
        retrieval_payloads.append(
            {
                "query": case.query,
                "top_id": top_id,
                "expected_top_id": case.expected_top_id,
                "hit": top_id == case.expected_top_id,
                "signal_coverage": signal_coverage,
                "dynamic_reason_hit": all(tag in top_reasons for tag in case.expected_reason_tags),
                "state_fidelity_hit": _signals_within_thresholds(
                    top_signals,
                    mins=case.expected_signal_mins,
                    maxs=case.expected_signal_maxs,
                ),
                "top_reasons": top_reasons,
                "top_signals": top_signals,
                "bundle_energy": snapshot["energy"],
                "bundle_objective": snapshot["objective"],
                "latency_ms": round(latency_ms, 3),
            }
        )

    for case in transition_cases:
        payload = app.v8_transition_gate(case.memory_id)
        transition_payloads.append(
            {
                "memory_id": case.memory_id,
                "recommended_state": payload["transition_gate"]["recommended_state"],
                "expected_recommended_state": case.expected_recommended_state,
                "hit": payload["transition_gate"]["recommended_state"] == case.expected_recommended_state,
                "state_fidelity_hit": _signals_within_thresholds(
                    payload["signals"],
                    mins=case.expected_signal_mins,
                    maxs=case.expected_signal_maxs,
                ),
                "signals": payload["signals"],
            }
        )

    for case in feedback_cases or []:
        tracked_ids = list(dict.fromkeys(case.selected_memory_ids + case.override_memory_ids))
        before_signals = {memory_id: app.compute_v8_core_signals(memory_id) for memory_id in tracked_ids}
        before = app.v8_bundle_snapshot(
            query=case.query,
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            limit=case.limit,
            include_global=True,
        )["snapshot"]
        payload = app.apply_v8_retrieval_feedback(
            query=case.query,
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            success_score=case.success_score,
            selected_memory_ids=case.selected_memory_ids,
            override_memory_ids=case.override_memory_ids,
            limit=case.limit,
            include_global=True,
            actor="v8_benchmark_bundle_feedback",
        )
        assignments = {item["memory_id"]: item for item in payload["assignments"]}
        selected_weights = [
            assignments[memory_id]["contribution_weight"]
            for memory_id in case.selected_memory_ids
            if memory_id in assignments
        ]
        overridden_weights = [
            assignments[memory_id]["contribution_weight"]
            for memory_id in case.override_memory_ids
            if memory_id in assignments
        ]
        after_signals = {memory_id: app.compute_v8_core_signals(memory_id) for memory_id in tracked_ids}
        feedback_payloads.append(
            {
                "query": case.query,
                "before_snapshot": before,
                "after_snapshot": payload["after_snapshot"],
                "feedback_aligned": (
                    bool(selected_weights)
                    and (max(selected_weights) >= (max(overridden_weights) if overridden_weights else 0.0))
                ),
                "state_fidelity_hit": (
                    _signal_deltas_follow_direction(
                        before=before_signals,
                        after=after_signals,
                        memory_ids=case.selected_memory_ids,
                        increases=case.selected_signal_increases,
                        decreases=case.selected_signal_decreases,
                    )
                    and _signal_deltas_follow_direction(
                        before=before_signals,
                        after=after_signals,
                        memory_ids=case.override_memory_ids,
                        increases=case.override_signal_increases,
                        decreases=case.override_signal_decreases,
                    )
                ),
                "objective_regression": round(
                    max(0.0, payload["after_snapshot"]["objective"] - before["objective"]),
                    6,
                ),
                "tracked_before_signals": before_signals,
                "tracked_after_signals": after_signals,
                "assignments": payload["assignments"],
            }
        )

    latency_p50 = statistics.median(latencies) if latencies else 0.0
    latency_p95 = _percentile(latencies, 95)
    return V8BenchmarkSummary(
        retrieval_hit_rate=_avg(item["hit"] for item in retrieval_payloads),
        signal_coverage=_avg(item["signal_coverage"] for item in retrieval_payloads),
        dynamic_reason_coverage=_avg(item["dynamic_reason_hit"] for item in retrieval_payloads),
        retrieval_state_fidelity=_avg(item["state_fidelity_hit"] for item in retrieval_payloads),
        transition_gate_accuracy=_avg(item["hit"] for item in transition_payloads),
        transition_state_fidelity=_avg(item["state_fidelity_hit"] for item in transition_payloads),
        feedback_alignment_rate=_avg(item["feedback_aligned"] for item in feedback_payloads),
        feedback_state_fidelity=_avg(item["state_fidelity_hit"] for item in feedback_payloads),
        objective_regression_mean=_avg(item["objective_regression"] for item in feedback_payloads),
        bundle_energy_mean=_avg(item["bundle_energy"] for item in retrieval_payloads),
        bundle_objective_mean=_avg(item["bundle_objective"] for item in retrieval_payloads),
        latency_p50_ms=latency_p50,
        latency_p95_ms=latency_p95,
        retrieval_cases=retrieval_payloads,
        transition_cases=transition_payloads,
        feedback_cases=feedback_payloads,
    )


def evaluate_v8_benchmark(
    summary: V8BenchmarkSummary,
    thresholds: V8BenchmarkThresholds = V8BenchmarkThresholds(),
) -> V8BenchmarkGateResult:
    failures: list[str] = []
    if summary.retrieval_hit_rate < thresholds.retrieval_hit_rate_min:
        failures.append(f"retrieval_hit_rate={summary.retrieval_hit_rate:.3f}<{thresholds.retrieval_hit_rate_min}")
    if summary.signal_coverage < thresholds.signal_coverage_min:
        failures.append(f"signal_coverage={summary.signal_coverage:.3f}<{thresholds.signal_coverage_min}")
    if summary.dynamic_reason_coverage < thresholds.dynamic_reason_coverage_min:
        failures.append(
            f"dynamic_reason_coverage={summary.dynamic_reason_coverage:.3f}<{thresholds.dynamic_reason_coverage_min}"
        )
    if summary.retrieval_state_fidelity < thresholds.retrieval_state_fidelity_min:
        failures.append(
            f"retrieval_state_fidelity={summary.retrieval_state_fidelity:.3f}<{thresholds.retrieval_state_fidelity_min}"
        )
    if summary.transition_gate_accuracy < thresholds.transition_gate_accuracy_min:
        failures.append(
            f"transition_gate_accuracy={summary.transition_gate_accuracy:.3f}<{thresholds.transition_gate_accuracy_min}"
        )
    if summary.transition_state_fidelity < thresholds.transition_state_fidelity_min:
        failures.append(
            f"transition_state_fidelity={summary.transition_state_fidelity:.3f}<{thresholds.transition_state_fidelity_min}"
        )
    if summary.feedback_alignment_rate < thresholds.feedback_alignment_rate_min:
        failures.append(
            f"feedback_alignment_rate={summary.feedback_alignment_rate:.3f}<{thresholds.feedback_alignment_rate_min}"
        )
    if summary.feedback_state_fidelity < thresholds.feedback_state_fidelity_min:
        failures.append(
            f"feedback_state_fidelity={summary.feedback_state_fidelity:.3f}<{thresholds.feedback_state_fidelity_min}"
        )
    if thresholds.objective_regression_max is not None and summary.objective_regression_mean > thresholds.objective_regression_max:
        failures.append(
            f"objective_regression_mean={summary.objective_regression_mean:.3f}>{thresholds.objective_regression_max}"
        )
    if thresholds.bundle_energy_max is not None and summary.bundle_energy_mean > thresholds.bundle_energy_max:
        failures.append(f"bundle_energy_mean={summary.bundle_energy_mean:.3f}>{thresholds.bundle_energy_max}")
    if thresholds.bundle_objective_max is not None and summary.bundle_objective_mean > thresholds.bundle_objective_max:
        failures.append(f"bundle_objective_mean={summary.bundle_objective_mean:.3f}>{thresholds.bundle_objective_max}")
    if thresholds.latency_p95_ms_max is not None and summary.latency_p95_ms > thresholds.latency_p95_ms_max:
        failures.append(f"latency_p95_ms={summary.latency_p95_ms:.3f}>{thresholds.latency_p95_ms_max}")
    return V8BenchmarkGateResult(passed=not failures, failures=failures)


def render_v8_benchmark(summary: V8BenchmarkSummary, gate: V8BenchmarkGateResult) -> str:
    payload = {
        "retrieval_hit_rate": round(summary.retrieval_hit_rate, 3),
        "signal_coverage": round(summary.signal_coverage, 3),
        "dynamic_reason_coverage": round(summary.dynamic_reason_coverage, 3),
        "retrieval_state_fidelity": round(summary.retrieval_state_fidelity, 3),
        "transition_gate_accuracy": round(summary.transition_gate_accuracy, 3),
        "transition_state_fidelity": round(summary.transition_state_fidelity, 3),
        "feedback_alignment_rate": round(summary.feedback_alignment_rate, 3),
        "feedback_state_fidelity": round(summary.feedback_state_fidelity, 3),
        "objective_regression_mean": round(summary.objective_regression_mean, 3),
        "bundle_energy_mean": round(summary.bundle_energy_mean, 3),
        "bundle_objective_mean": round(summary.bundle_objective_mean, 3),
        "latency_p50_ms": round(summary.latency_p50_ms, 3),
        "latency_p95_ms": round(summary.latency_p95_ms, 3),
        "passed": gate.passed,
        "failures": gate.failures,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def select_best_v8_profile(
    *,
    app_factory,
    candidate_profiles: dict[str, V8DynamicsProfile],
    retrieval_cases: list[V8RetrievalCase],
    transition_cases: list[V8TransitionCase],
    feedback_cases: list[V8FeedbackCase] | None = None,
    thresholds: V8BenchmarkThresholds = V8BenchmarkThresholds(),
) -> V8ProfileSelection:
    original = get_active_v8_profile()
    selections: list[V8ProfileSelection] = []
    try:
        for name, profile in candidate_profiles.items():
            set_active_v8_profile(profile)
            app = app_factory()
            summary = run_v8_dynamics_benchmark(
                app,
                retrieval_cases=retrieval_cases,
                transition_cases=transition_cases,
                feedback_cases=feedback_cases,
            )
            gate = evaluate_v8_benchmark(summary, thresholds)
            selections.append(
                V8ProfileSelection(
                    profile_name=name,
                    profile=profile,
                    summary=summary,
                    gate=gate,
                )
            )
    finally:
        set_active_v8_profile(original)

    passing = [item for item in selections if item.gate.passed]
    ranked = passing if passing else selections
    ranked.sort(
        key=lambda item: (
            0 if item.gate.passed else 1,
            item.summary.objective_regression_mean,
            item.summary.bundle_objective_mean,
            -item.summary.feedback_alignment_rate,
            -item.summary.retrieval_hit_rate,
        )
    )
    return ranked[0]


def _avg(values) -> float:
    collected = list(values)
    if not collected:
        return 0.0
    normalized: list[float] = []
    for item in collected:
        if isinstance(item, bool):
            normalized.append(1.0 if item else 0.0)
        else:
            normalized.append(float(item))
    return sum(normalized) / len(normalized)


def _percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * (pct / 100.0)))))
    return ordered[index]


def _signals_within_thresholds(
    signals: dict[str, Any],
    *,
    mins: dict[str, float],
    maxs: dict[str, float],
) -> bool:
    for field, expected in mins.items():
        actual = float(signals.get(field, 0.0) or 0.0)
        if actual < float(expected):
            return False
    for field, expected in maxs.items():
        actual = float(signals.get(field, 0.0) or 0.0)
        if actual > float(expected):
            return False
    return True


def _signal_deltas_follow_direction(
    *,
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    memory_ids: list[str],
    increases: list[str],
    decreases: list[str],
) -> bool:
    if not memory_ids:
        return True
    for memory_id in memory_ids:
        before_signals = before.get(memory_id, {})
        after_signals = after.get(memory_id, {})
        for field in increases:
            if float(after_signals.get(field, 0.0) or 0.0) <= float(before_signals.get(field, 0.0) or 0.0):
                return False
        for field in decreases:
            if float(after_signals.get(field, 0.0) or 0.0) >= float(before_signals.get(field, 0.0) or 0.0):
                return False
    return True
