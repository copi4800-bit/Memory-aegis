# Plan: 079 Truth Scenario Catalog And Trend

## Intent

Make truth evaluation artifacts more self-explanatory and easier to compare over time without widening scope beyond the current benchmark/report flow.

## Workstreams

### 1. Scenario Catalog

- Define stable metadata for each truth scenario.
- Persist the catalog in the benchmark artifact.

### 2. Trend Report

- Read an optional previous artifact.
- Render compact metric and scenario trend lines in the Markdown report.

### 3. Verification

- Add tests for catalog and trend rendering.
- Re-run benchmark, gate, report, and full suite.
