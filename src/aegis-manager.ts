/**
 * Legacy compatibility stub for the removed TypeScript memory engine.
 *
 * The production runtime is owned by `aegis_py`. This file remains only so
 * legacy imports fail with a clear migration message instead of silently
 * reviving the old engine.
 */

import type Database from "better-sqlite3";

type AegisConfig = Record<string, unknown>;
type CognitiveLayers = string;
type MemorySearchResult = {
  path: string;
  startLine: number;
  endLine: number;
  score: number;
  snippet: string;
  source: "memory" | "sessions";
  citation?: string;
};

const LEGACY_ERROR =
  "AegisMemoryManager has been retired from the production runtime. Use the Python-owned surfaces in aegis_py or the root plugin bootstrap instead.";

export class AegisMemoryManager {
  static async create(_opts: {
    agentId: string;
    workspaceDir: string;
    config?: Partial<AegisConfig>;
  }): Promise<AegisMemoryManager> {
    throw new Error(LEGACY_ERROR);
  }

  async close(): Promise<void> {
    return;
  }

  getDb(): Database.Database {
    throw new Error(LEGACY_ERROR);
  }

  async search(_query: string, _opts: unknown): Promise<MemorySearchResult[]> {
    throw new Error(LEGACY_ERROR);
  }

  async readFile(_params: { relPath: string; from?: number; lines?: number }): Promise<{ text: string }> {
    throw new Error(LEGACY_ERROR);
  }

  status(): Record<string, unknown> {
    throw new Error(LEGACY_ERROR);
  }

  async probeEmbeddingAvailability(): Promise<{ ok: boolean; error?: string }> {
    throw new Error(LEGACY_ERROR);
  }

  async probeVectorAvailability(): Promise<boolean> {
    throw new Error(LEGACY_ERROR);
  }

  async sync(_opts: {
    reason?: string;
    force?: boolean;
    sessionFiles?: string[];
    progress?: (update: unknown) => void;
  }): Promise<void> {
    throw new Error(LEGACY_ERROR);
  }

  async maintenance(): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async runMaintenance(): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async backup(_mode: "snapshot" | "export", _destDir: string): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async restore(_snapshotPath: string): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async getStatus(): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async getHoneybeeStats(): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async getDoctorReport(): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async profile(): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  async runOnboarding(_preset: string): Promise<never> {
    throw new Error(LEGACY_ERROR);
  }

  layerEnabled(_layer: CognitiveLayers): boolean {
    return false;
  }
}

export async function closeAllManagers(): Promise<void> {
  return;
}
