# Feature Spec: 081 Aegis Gauntlet

## Summary

Aegis now has a strong truth-evaluation stack, but it still needs a broader stress pass that probes not only core truth behavior, but also scale pressure, adversarial inputs, and product-readiness flows.

## Problem

Current spotlight evaluation proves key truth behaviors, but it does not answer the larger product question: can Aegis behave like a serious memory product under mixed pressure?

## Goals

- Add a repo-native gauntlet runner that stresses Aegis across multiple dimensions.
- Emit a machine-readable artifact with category-level and overall results.
- Keep the first version bounded and local-first.

## Non-Goals

- Creating a long-running soak environment.
- Benchmarking against external products in this phase.
- Replacing the truth spotlight benchmark or release gate.

## Evaluation Areas

- `core_truth`
- `scale`
- `adversarial`
- `product_readiness`

## Acceptance Criteria

1. A gauntlet script runs multiple categories of Aegis stress scenarios.
2. The gauntlet writes a summary artifact under `.planning/benchmarks/`.
3. The artifact clearly shows pass/fail by scenario and by category.
4. The repo includes automated coverage for gauntlet artifact shaping.
