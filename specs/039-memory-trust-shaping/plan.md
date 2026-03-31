# Implementation Plan: Memory Trust Shaping

**Branch**: `039-memory-trust-shaping`
**Spec**: [spec.md](./spec.md)

## Summary

Implement a thin trust-shaping layer over existing retrieval outputs so users can distinguish strong, weak, uncertain, and conflicting memories without adding a new subsystem.

## Work Plan

1. Define a bounded trust classification helper inside retrieval.
2. Surface trust state and reason on `SearchResult`.
3. Serialize trust metadata through search payloads and context-pack.
4. Adapt `memory_recall` to render trust cues in plain language.
5. Add regression coverage for strong, uncertain, and conflicting trust states.

## Validation Plan

- `pytest tests/test_retrieval.py`
- `pytest tests/test_integration.py -k trust`
- full regression suite for non-regression

## Validation Evidence

Observed on 2026-03-24 after implementing `039-memory-trust-shaping`:

- retrieval results now expose bounded trust states `strong`, `weak`, `uncertain`, and `conflicting`
- trust metadata flows through serialized search payloads and context-pack results
- the simplified `memory_recall` surface now renders trust cues in plain language without exposing internal fields
- the implementation stayed inside the existing retrieval, surface, and app layers without creating a separate trust subsystem

Validation results:

- `SPECIFY_FEATURE=039-memory-trust-shaping ./.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
  - passed
  - `FEATURE_DIR=/home/hali/.openclaw/extensions/memory-aegis-v7/specs/039-memory-trust-shaping`
  - `AVAILABLE_DOCS=["tasks.md"]`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests/test_retrieval.py tests/test_integration.py -k 'trust or explainability or conflict_visibility or mcp_operational_flows_return_consistent_json or context_pack_and_simple_recall_surface_trust_states'`
  - passed
  - `4 passed`
- `PYTHONPATH=/home/hali/.openclaw/extensions/memory-aegis-v7 .venv/bin/pytest -q tests`
  - passed
  - `114 passed in 2.84s`
