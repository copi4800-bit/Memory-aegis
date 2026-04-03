from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compressed_prefilter import CompressedCandidatePrefilter

DEFAULT_COMPRESSED_TIER_ARTIFACT = Path(".planning/benchmarks/compressed_candidate_tier_summary.json")
DEFAULT_COMPRESSED_TIER_THRESHOLDS = {
    "compressed_candidate_yield_rate": 1.0,
    "governed_top1_preservation_rate": 1.0,
    "persistent_coverage_rate": 1.0,
    "rebuild_backfill_rate": 1.0,
}


def classify_compressed_tier(
    *,
    status: str,
    activation_score: float,
    metadata: dict[str, Any] | None,
) -> str:
    payload = metadata or {}
    if payload.get("is_winner") is True or status in {"crystallized"}:
        return "hot"
    if status in {"archived", "superseded", "expired"} or activation_score < 0.5:
        return "cold"
    return "warm"


def build_compressed_tier_payload(
    *,
    content: str | None,
    summary: str | None,
    subject: str | None,
    status: str,
    activation_score: float,
    metadata: dict[str, Any] | None,
    prefilter: CompressedCandidatePrefilter | None = None,
) -> dict[str, Any]:
    engine = prefilter or CompressedCandidatePrefilter()
    tier = classify_compressed_tier(
        status=status,
        activation_score=activation_score,
        metadata=metadata,
    )
    signature = engine.build_signature(
        " ".join(filter(None, [content, summary, subject])),
        semantic_terms=[subject or ""],
    )
    lexical_density = round(signature.lexical_mask.bit_count() / max(signature.lexical_width, 1), 6)
    semantic_density = round(signature.semantic_mask.bit_count() / max(signature.semantic_width, 1), 6)
    return {
        "tier": tier,
        "lexical_mask": format(signature.lexical_mask, "x"),
        "semantic_mask": format(signature.semantic_mask, "x"),
        "lexical_width": signature.lexical_width,
        "semantic_width": signature.semantic_width,
        "lexical_density": lexical_density,
        "semantic_density": semantic_density,
        "signature_version": 1,
    }


def build_compressed_tier_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    covered = 0
    tier_counts = {"hot": 0, "warm": 0, "cold": 0}
    for row in rows:
        metadata = row.get("metadata_json", {})
        if not isinstance(metadata, dict):
            continue
        compressed = metadata.get("compressed_tier")
        if not isinstance(compressed, dict):
            continue
        covered += 1
        tier = str(compressed.get("tier") or "warm")
        if tier in tier_counts:
            tier_counts[tier] += 1
    total = len(rows)
    return {
        "memory_count": total,
        "covered_memories": covered,
        "coverage_rate": round(covered / total, 6) if total else 0.0,
        "tier_counts": tier_counts,
    }


def load_compressed_tier_artifact(path: Path | None = None) -> dict[str, Any] | None:
    resolved_path = path or DEFAULT_COMPRESSED_TIER_ARTIFACT
    if not resolved_path.exists():
        return None
    return json.loads(resolved_path.read_text(encoding="utf-8"))


def evaluate_compressed_tier_gate(
    artifact: dict[str, Any] | None,
    thresholds: dict[str, float] | None = None,
) -> tuple[bool, list[str], dict[str, float]]:
    if artifact is None:
        return False, ["compressed candidate benchmark artifact is missing"], {}

    gate = thresholds or DEFAULT_COMPRESSED_TIER_THRESHOLDS
    summary = artifact.get("summary", {})
    failures: list[str] = []
    for key, minimum in gate.items():
        actual = float(summary.get(key, 0.0) or 0.0)
        if actual < minimum:
            failures.append(f"{key}={actual:.3f} fell below required {minimum:.3f}")
    return len(failures) == 0, failures, {key: float(summary.get(key, 0.0) or 0.0) for key in gate}


def build_compressed_tier_status(
    *,
    rows: list[dict[str, Any]],
    artifact: dict[str, Any] | None = None,
    thresholds: dict[str, float] | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
) -> dict[str, Any]:
    coverage = build_compressed_tier_coverage(rows)
    benchmark = artifact if artifact is not None else load_compressed_tier_artifact()
    gate_passed, failures, summary_metrics = evaluate_compressed_tier_gate(benchmark, thresholds)
    return {
        "scope": {
            "scope_type": scope_type,
            "scope_id": scope_id,
        },
        "coverage": coverage,
        "benchmark_available": benchmark is not None,
        "benchmark_summary": benchmark.get("summary", {}) if benchmark else {},
        "readiness": {
            "passed": gate_passed,
            "failures": failures,
            "thresholds": dict(thresholds or DEFAULT_COMPRESSED_TIER_THRESHOLDS),
            "summary_metrics": summary_metrics,
        },
    }
