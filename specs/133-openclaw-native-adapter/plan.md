# Plan

1. Create a native OpenClaw plugin entry module in the TruthKeep package.
2. Add a runtime bridge module that shells into `python -m truthkeep.mcp` for search, read, and health/status operations.
3. Update package metadata so OpenClaw discovers the native adapter entrypoint.
4. Add regression tests that assert the adapter registers a native memory runtime and that the bridge contract is coherent.
5. Run targeted tests and smoke verification.
