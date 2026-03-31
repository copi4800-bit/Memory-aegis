# Implementation Plan: Aegis Python Benchmark And Release Hardening

**Branch**: `002-benchmark-release-hardening` | **Date**: 2026-03-23 | **Spec**: [spec.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/spec.md)
**Input**: Feature specification from `/specs/002-benchmark-release-hardening/spec.md`

## Summary

Strengthen the post-vNext release bar by expanding the seeded retrieval benchmark corpus, formalizing benchmark threshold evaluation, and documenting a contributor-facing local validation workflow that records release-readiness evidence in active `spec-kit` artifacts.

## Technical Context

**Language/Version**: Python 3.13.x  
**Primary Dependencies**: Standard library, existing `aegis_py` modules, `pytest`  
**Storage**: Local SQLite with FTS5 for seeded benchmark fixtures  
**Testing**: Python regression suite under `tests/` executed with `pytest`  
**Target Platform**: Local Linux/macOS developer environments and OpenClaw-hosted local agent runtimes  
**Project Type**: Local library and MCP integration surface with spec/documentation artifacts  
**Performance Goals**: Keep the local regression benchmark fast enough for routine contributor use while preserving explicit thresholds for relevance, leakage, explainability, and latency  
**Constraints**: Local-first only, no cloud dependency, do not reopen core engine semantics from feature `001`, keep benchmark/reporting changes explainable and deterministic  
**Scale/Scope**: One follow-up hardening wave covering benchmark fixtures, validation workflow docs, and release-readiness records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `Local-First Memory Engine`: Pass. All validation and benchmark work stays local and seeded.
- `Brownfield Refactor Over Rewrite`: Pass. This feature hardens release discipline and benchmark coverage without changing the engine architecture wholesale.
- `Explainable Retrieval Is Non-Negotiable`: Pass. The benchmark gate explicitly keeps explanation completeness in scope.
- `Safe Memory Mutation By Default`: Pass. This feature does not expand destructive hygiene behavior.
- `Measured Simplicity`: Pass. The work is narrowly scoped to regression discipline, docs, and release evidence.

No constitutional violations are expected for this feature.

## Project Structure

### Documentation (this feature)

```text
specs/002-benchmark-release-hardening/
├── plan.md
├── spec.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
aegis_py/
├── retrieval/
│   └── benchmark.py
└── ...

tests/
├── test_benchmark_core.py
├── test_retrieval.py
├── test_integration.py
└── ...

.specify/
specs/
README.md
AEGIS_PYTHON_SPEC.md
```

**Structure Decision**: Keep the existing single-project Python layout. This feature touches the benchmark harness, regression tests, contributor-facing docs, and `spec-kit` artifacts rather than introducing new runtime modules.

## Phase Plan

### Phase 0 - Benchmark Gap Inventory

Objective: Identify which retrieval behaviors are already benchmarked and which remain only regression-tested or undocumented.

Deliverables:

- Inventory seeded benchmark cases in `tests/test_benchmark_core.py`
- Map missing benchmark shapes against feature `001` closeout gaps
- Confirm which thresholds are currently implicit versus explicit

Exit Criteria:

- We know exactly which retrieval shapes still need benchmark or gate coverage
- We can state the benchmark threshold contract in one canonical place

Current inventory on 2026-03-23:

- `tests/test_benchmark_core.py` now covers scoped retrieval, anti-leak behavior, punctuation-safe retrieval, empty-result behavior, and expected conflict-visible retrieval
- `tests/test_retrieval.py` remains the focused regression layer for pipeline behavior beneath the benchmark summary
- `tests/test_app_surface.py` now locks the contributor-facing validation command and active `spec-kit` layout references

### Phase 1 - Benchmark Gate Hardening

Objective: Broaden the benchmark harness and make threshold evaluation explicit and reusable.

Primary Files:

- [aegis_py/retrieval/benchmark.py](/home/hali/.openclaw/extensions/memory-aegis-v7/aegis_py/retrieval/benchmark.py)
- [tests/test_benchmark_core.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_benchmark_core.py)
- supporting retrieval tests under [tests/test_retrieval.py](/home/hali/.openclaw/extensions/memory-aegis-v7/tests/test_retrieval.py)

Exit Criteria:

- Benchmark threshold evaluation produces explicit pass/fail reasons
- The seeded benchmark corpus covers the agreed retrieval shapes for this feature

Status:

- threshold ownership is explicit in `BenchmarkThresholds`
- threshold evaluation is explicit in `evaluate_summary()`
- failure output is explicit in `render_gate_report()`

### Phase 2 - Contributor Validation Workflow

Objective: Make the local validation path obvious and stable for contributors.

Primary Files:

- [README.md](/home/hali/.openclaw/extensions/memory-aegis-v7/README.md)
- [AEGIS_PYTHON_SPEC.md](/home/hali/.openclaw/extensions/memory-aegis-v7/AEGIS_PYTHON_SPEC.md)

Exit Criteria:

- Contributors can identify the local regression command set and benchmark gate without external explanation
- Docs align with the canonical Python engine contract and active `spec-kit` layout

### Phase 3 - Release Readiness Record

Objective: Record what was actually validated and what remains outside the current release bar.

Primary Files:

- [specs/002-benchmark-release-hardening/plan.md](/home/hali/.openclaw/extensions/memory-aegis-v7/specs/002-benchmark-release-hardening/plan.md)
- follow-up `spec-kit` artifacts for tasks or closeout notes if created

Exit Criteria:

- Validation commands and observed results are recorded in the active feature artifacts
- Remaining release gaps are explicit and ready to seed the next feature wave

## Complexity Tracking

No constitution violations currently require exception handling.

## Validation Closeout

Validation run completed on 2026-03-23 for feature `002-benchmark-release-hardening`.

Executed command:

```bash
cd /home/hali/.openclaw/extensions/memory-aegis-v7
PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests
```

Observed result:

- `51 passed in 0.84s`

Validated additions in this feature:

- broadened benchmark corpus for punctuation-safe queries, empty-result behavior, and expected conflict-visible retrieval
- explicit metric/value failure reporting for benchmark gate failures
- contributor-facing regression coverage for the published validation command and active root-level `spec-kit` layout

Remaining gaps after this hardening wave:

- benchmark breadth is still fixture-driven and not yet sourced from a larger external corpus
- validation remains local and manual; CI wiring was not added in this feature
- release packaging and publishing workflow still need a separate feature if they become part of the product bar
