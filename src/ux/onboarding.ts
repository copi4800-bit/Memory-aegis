/**
 * Legacy compatibility stub for the retired TypeScript onboarding path.
 *
 * The production onboarding flow is now owned by `aegis_py.cli onboarding`
 * and reached through `aegis-setup`. This file remains only so old imports
 * fail clearly instead of reviving the TS-era onboarding path.
 */

import type Database from "better-sqlite3";

type AegisPreset = "minimal" | "balanced" | "local-safe" | "full";

const LEGACY_ONBOARDING_ERROR =
  "TypeScript onboarding has been retired. Use the Python-owned onboarding flow via `aegis-setup` or `python -m aegis_py.cli onboarding` instead.";

export interface OnboardingResult {
  preset: AegisPreset;
  healthCheck: { passed: boolean; report: unknown };
  storeTest: { passed: boolean; nodeId?: string };
  recallTest: { passed: boolean; found: boolean };
  summary: string;
  allPassed: boolean;
}

export function runOnboarding(
  _db: Database.Database,
  _workspaceDir: string,
  _dbPath: string,
  _preset: AegisPreset = "balanced",
): OnboardingResult {
  throw new Error(LEGACY_ONBOARDING_ERROR);
}
