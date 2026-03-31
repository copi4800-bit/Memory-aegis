/**
 * Legacy compatibility stub for the retired TypeScript message-hook path.
 *
 * The production hook surface now lives in the root OpenClaw plugin bootstrap
 * and routes behavior into `aegis_py`. This file remains only so old imports
 * fail clearly instead of reviving TS-owned hook behavior.
 */

const LEGACY_MESSAGE_HOOK_ERROR =
  "TypeScript message hooks have been retired. Use the root plugin bootstrap and Python-owned surfaces in aegis_py instead.";

export function createMessageHooks(): never {
  throw new Error(LEGACY_MESSAGE_HOOK_ERROR);
}
