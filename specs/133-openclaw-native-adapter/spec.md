# Phase 133 - OpenClaw Native Adapter

## Goal

Add a thin host-side OpenClaw native memory adapter around TruthKeep so the package can register a real `registerMemoryRuntime(...)` bridge instead of acting only like an MCP-facing memory plugin.

## Scope

- Add a native OpenClaw plugin entry module that registers TruthKeep as a memory runtime.
- Bridge OpenClaw memory runtime calls to the existing TruthKeep Python MCP wrapper via local process execution.
- Map TruthKeep search/read/status outputs into the OpenClaw memory runtime contract.
- Align package metadata so `package.json.openclaw.extensions` points at the native adapter entry module.
- Add regression tests for adapter registration, packaging consistency, and basic bridge behavior.

## Non-Goals

- No changes to TruthKeep truth/governance/retrieval math.
- No OpenClaw host repo modifications.
- No full JS/TS rewrite of TruthKeep runtime behavior.
