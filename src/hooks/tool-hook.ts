/**
 * Legacy compatibility stub for the retired TypeScript tool-hook path.
 *
 * The production tool-routing path now lives in the root OpenClaw plugin
 * bootstrap and routes behavior into `aegis_py`.
 */

const LEGACY_TOOL_HOOK_ERROR =
  "TypeScript tool hooks have been retired. Use the root plugin bootstrap and Python-owned surfaces in aegis_py instead.";

export function createToolHooks(): never {
  throw new Error(LEGACY_TOOL_HOOK_ERROR);
}
