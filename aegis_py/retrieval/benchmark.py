from __future__ import annotations

import json
import math
import statistics
import time
from dataclasses import dataclass, field

from aegis_py.memory.core import MemoryManager


@dataclass
class QueryCase:
    query: str
    expected_ids: list[str]
    scope_type: str
    scope_id: str
    forbidden_ids: list[str] | None = None
    expected_conflict_ids: list[str] | None = None
    limit: int = 5


@dataclass
class QueryMetrics:
    query: str
    retrieval_mode: str
    recall_at_1: float
    recall_at_5: float
    recall_at_k: float
    hit_at_k: float
    mrr_at_10: float
    ndcg_at_10: float
    scope_leakage: float
    conflict_leakage: float
    conflict_visibility: float
    explain_complete: float
    latency_ms: float
    payload_bytes: float


@dataclass
class BenchmarkSummary:
    retrieval_mode: str
    recall_at_1: float
    recall_at_5: float
    recall_at_k: float
    hit_at_k: float
    mrr_at_10: float
    ndcg_at_10: float
    scope_leakage: float
    conflict_leakage: float
    conflict_visibility: float
    explain_completeness: float
    latency_p50_ms: float
    latency_p95_ms: float
    payload_bytes_p50: float
    payload_bytes_p95: float
    queries: list[QueryMetrics]


@dataclass(frozen=True)
class BenchmarkThresholds:
    recall_at_1_min: float = 0.5
    recall_at_5_min: float = 1.0
    recall_at_k_min: float = 1.0
    hit_at_k_min: float = 1.0
    mrr_at_10_min: float = 0.5
    ndcg_at_10_min: float = 0.5
    scope_leakage_max: float = 0.0
    conflict_leakage_max: float = 0.0
    explain_completeness_min: float = 1.0
    conflict_visibility_min: float | None = None
    latency_p95_ms_max: float | None = 50.0
    payload_bytes_p95_max: float | None = None


@dataclass
class BenchmarkGateResult:
    passed: bool
    failures: list[str] = field(default_factory=list)


DEFAULT_THRESHOLDS = BenchmarkThresholds()


def run_benchmark(manager: MemoryManager, cases: list[QueryCase]) -> BenchmarkSummary:
    return run_payload_benchmark(manager, cases, retrieval_mode="explain")


def run_payload_benchmark(
    manager: MemoryManager,
    cases: list[QueryCase],
    *,
    retrieval_mode: str = "explain",
) -> BenchmarkSummary:
    per_query: list[QueryMetrics] = []
    latencies: list[float] = []
    payload_sizes: list[float] = []
    explain_mode = retrieval_mode == "explain"

    for case in cases:
        start = time.perf_counter()
        results = manager.search(
            case.query,
            scope_type=case.scope_type,
            scope_id=case.scope_id,
            limit=case.limit,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)
        payload_bytes = _estimate_payload_bytes(results, retrieval_mode=retrieval_mode)
        payload_sizes.append(payload_bytes)

        result_ids = [result.id for result in results]
        expected = case.expected_ids
        forbidden = set(case.forbidden_ids or [])
        expected_conflicts = set(case.expected_conflict_ids or [])

        recall_at_1 = _recall_at_k(result_ids, expected, 1)
        recall_at_5 = _recall_at_k(result_ids, expected, 5)
        hits = [rid for rid in result_ids[: case.limit] if rid in expected]
        recall = len(set(hits)) / len(expected) if expected else 1.0
        hit_at_k = 1.0 if hits or not expected else 0.0
        mrr = _mrr_at_10(result_ids, expected)
        ndcg = _ndcg_at_10(result_ids, expected)
        leakage = _scope_leakage(result_ids, forbidden, case.limit)
        conflict_leakage = _conflict_leakage(results, expected_conflicts, case.limit)
        conflict_visibility = _conflict_visibility(results, expected_conflicts, case.limit)
        explain_complete = _explain_completeness(results) if explain_mode else 0.0

        per_query.append(
            QueryMetrics(
                query=case.query,
                retrieval_mode=retrieval_mode,
                recall_at_1=recall_at_1,
                recall_at_5=recall_at_5,
                recall_at_k=recall,
                hit_at_k=hit_at_k,
                mrr_at_10=mrr,
                ndcg_at_10=ndcg,
                scope_leakage=leakage,
                conflict_leakage=conflict_leakage,
                conflict_visibility=conflict_visibility,
                explain_complete=explain_complete,
                latency_ms=latency_ms,
                payload_bytes=payload_bytes,
            )
        )

    latency_p50 = statistics.median(latencies) if latencies else 0.0
    latency_p95 = _percentile(latencies, 95)
    payload_p50 = statistics.median(payload_sizes) if payload_sizes else 0.0
    payload_p95 = _percentile(payload_sizes, 95)

    return BenchmarkSummary(
        retrieval_mode=retrieval_mode,
        recall_at_1=_avg(metric.recall_at_1 for metric in per_query),
        recall_at_5=_avg(metric.recall_at_5 for metric in per_query),
        recall_at_k=_avg(metric.recall_at_k for metric in per_query),
        hit_at_k=_avg(metric.hit_at_k for metric in per_query),
        mrr_at_10=_avg(metric.mrr_at_10 for metric in per_query),
        ndcg_at_10=_avg(metric.ndcg_at_10 for metric in per_query),
        scope_leakage=_avg(metric.scope_leakage for metric in per_query),
        conflict_leakage=_avg(metric.conflict_leakage for metric in per_query),
        conflict_visibility=_avg(metric.conflict_visibility for metric in per_query),
        explain_completeness=_avg(metric.explain_complete for metric in per_query) if explain_mode else 0.0,
        latency_p50_ms=latency_p50,
        latency_p95_ms=latency_p95,
        payload_bytes_p50=payload_p50,
        payload_bytes_p95=payload_p95,
        queries=per_query,
    )


def evaluate_summary(
    summary: BenchmarkSummary,
    thresholds: BenchmarkThresholds = DEFAULT_THRESHOLDS,
) -> BenchmarkGateResult:
    failures: list[str] = []

    if summary.recall_at_1 < thresholds.recall_at_1_min:
        failures.append(f"recall_at_1={summary.recall_at_1:.3f}<{thresholds.recall_at_1_min}")
    if summary.recall_at_5 < thresholds.recall_at_5_min:
        failures.append(f"recall_at_5={summary.recall_at_5:.3f}<{thresholds.recall_at_5_min}")
    if summary.recall_at_k < thresholds.recall_at_k_min:
        failures.append(f"recall_at_k={summary.recall_at_k:.3f}<{thresholds.recall_at_k_min}")
    if summary.hit_at_k < thresholds.hit_at_k_min:
        failures.append(f"hit_at_k={summary.hit_at_k:.3f}<{thresholds.hit_at_k_min}")
    if summary.mrr_at_10 < thresholds.mrr_at_10_min:
        failures.append(f"mrr_at_10={summary.mrr_at_10:.3f}<{thresholds.mrr_at_10_min}")
    if summary.ndcg_at_10 < thresholds.ndcg_at_10_min:
        failures.append(f"ndcg_at_10={summary.ndcg_at_10:.3f}<{thresholds.ndcg_at_10_min}")
    if summary.scope_leakage > thresholds.scope_leakage_max:
        failures.append(f"scope_leakage={summary.scope_leakage:.3f}>{thresholds.scope_leakage_max}")
    if summary.conflict_leakage > thresholds.conflict_leakage_max:
        failures.append(f"conflict_leakage={summary.conflict_leakage:.3f}>{thresholds.conflict_leakage_max}")
    if summary.retrieval_mode == "explain" and summary.explain_completeness < thresholds.explain_completeness_min:
        failures.append(f"explain_completeness={summary.explain_completeness:.3f}<{thresholds.explain_completeness_min}")
    if thresholds.conflict_visibility_min is not None and summary.conflict_visibility < thresholds.conflict_visibility_min:
        failures.append(f"conflict_visibility={summary.conflict_visibility:.3f}<{thresholds.conflict_visibility_min}")
    if thresholds.latency_p95_ms_max is not None and summary.latency_p95_ms > thresholds.latency_p95_ms_max:
        failures.append(f"latency_p95_ms={summary.latency_p95_ms:.3f}>{thresholds.latency_p95_ms_max}")
    if thresholds.payload_bytes_p95_max is not None and summary.payload_bytes_p95 > thresholds.payload_bytes_p95_max:
        failures.append(f"payload_bytes_p95={summary.payload_bytes_p95:.3f}>{thresholds.payload_bytes_p95_max}")

    return BenchmarkGateResult(passed=not failures, failures=failures)


def render_gate_report(result: BenchmarkGateResult) -> str:
    if result.passed:
        return "PASS"
    return "FAIL: " + "; ".join(result.failures)


def _estimate_payload_bytes(results, *, retrieval_mode: str) -> float:
    payload: list[dict[str, object]] = []
    explain_mode = retrieval_mode == "explain"
    for result in results:
        item: dict[str, object] = {
            "id": getattr(result, "id", None),
            "score": getattr(result, "score", 0.0),
            "reason": getattr(result, "reason", ""),
            "provenance": getattr(result, "provenance", ""),
            "conflict_status": getattr(result, "conflict_status", "none"),
        }
        if explain_mode:
            item["trust_state"] = getattr(result, "trust_state", "unknown")
            item["trust_reason"] = getattr(result, "trust_reason", "")
            item["reasons"] = getattr(result, "reasons", [])
            item["retrieval_stage"] = getattr(result, "retrieval_stage", "lexical")
        payload.append(item)
    return float(len(json.dumps(payload, ensure_ascii=False)))


def _recall_at_k(result_ids: list[str], expected_ids: list[str], k: int) -> float:
    if not expected_ids:
        return 1.0
    hits = [rid for rid in result_ids[:k] if rid in set(expected_ids)]
    return len(set(hits)) / len(expected_ids)


def _mrr_at_10(result_ids: list[str], expected_ids: list[str]) -> float:
    expected = set(expected_ids)
    for index, result_id in enumerate(result_ids[:10], start=1):
        if result_id in expected:
            return 1.0 / index
    return 0.0


def _ndcg_at_10(result_ids: list[str], expected_ids: list[str]) -> float:
    expected = set(expected_ids)
    dcg = 0.0
    for index, result_id in enumerate(result_ids[:10], start=1):
        if result_id in expected:
            dcg += 1.0 / math.log2(index + 1)
    ideal_hits = min(len(expected_ids), 10)
    if ideal_hits == 0:
        return 1.0
    ideal_dcg = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def _scope_leakage(result_ids: list[str], forbidden_ids: set[str], limit: int) -> float:
    if not forbidden_ids:
        return 0.0
    leaked = [rid for rid in result_ids[:limit] if rid in forbidden_ids]
    return len(leaked) / min(limit, max(1, len(result_ids[:limit])))


def _conflict_leakage(results, expected_conflict_ids: set[str], limit: int) -> float:
    window = results[:limit]
    if not window:
        return 0.0
    leaked = [
        result
        for result in window
        if getattr(result, "conflict_status", "none") != "none" and getattr(result, "id", None) not in expected_conflict_ids
    ]
    return len(leaked) / len(window)


def _conflict_visibility(results, expected_conflict_ids: set[str], limit: int) -> float:
    if not expected_conflict_ids:
        return 1.0
    window = results[:limit]
    visible = {
        getattr(result, "id", None)
        for result in window
        if getattr(result, "conflict_status", "none") != "none"
    }
    return len(visible.intersection(expected_conflict_ids)) / len(expected_conflict_ids)


def _explain_completeness(results) -> float:
    if not results:
        return 1.0
    complete = 0
    for result in results:
        if result.reasons and result.source_kind and result.scope_type and result.scope_id and result.conflict_status:
            complete += 1
    return complete / len(results)


def _avg(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (pct / 100) * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
