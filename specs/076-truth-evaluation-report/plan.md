# Plan: 076 Truth Evaluation Report

## Intent

Make truth evaluation easier to review without broadening the benchmark/gate into a larger observability system.

## Workstreams

### 1. Reporting Contract

- Define a stable report shape for summary metrics and scenario outcomes.
- Keep the JSON artifact as source of truth.

### 2. Report Generator

- Add a script that reads the benchmark artifact and emits a Markdown report.
- Write the report to `.planning/benchmarks/`.

### 3. Verification

- Add tests for rendering.
- Run the benchmark, gate, and report together in validation flow.

## Verification Plan

- Run the benchmark to regenerate the artifact.
- Run the gate.
- Generate the report.
- Run targeted report tests.
- Run the full test suite.
