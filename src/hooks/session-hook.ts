/**
 * Legacy compatibility stub for the retired TypeScript session-hook path.
 *
 * The production session lifecycle path now lives in the root OpenClaw plugin
 * bootstrap and routes behavior into `aegis_py`.
 */

const LEGACY_SESSION_HOOK_ERROR =
  "TypeScript session hooks have been retired. Use the root plugin bootstrap and Python-owned surfaces in aegis_py instead.";

export function createSessionHooks(): never {
  throw new Error(LEGACY_SESSION_HOOK_ERROR);
}
