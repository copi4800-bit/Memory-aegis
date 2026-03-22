import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, resolveDbPath } from "../../src/db/connection.js";
import { ingestChunk } from "../../src/core/ingest.js";
import { createSnapshot } from "../../src/cognitive/tardigrade.js";
import { restoreFromSnapshot } from "../../src/cognitive/planarian.js";
import { AegisMemoryManager } from "../../src/aegis-manager.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";

let testDir: string;
let dbPath: string;

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-planarian-"));
  dbPath = resolveDbPath(testDir);
});

afterEach(() => {
  try {
    fs.rmSync(testDir, { recursive: true, force: true });
  } catch (e) {
    // Ignore EPERM on Windows
  }
});

describe("Planarian Restore", () => {
  it("restores the database fully from a .db.bak snapshot", async () => {
    // 1. Create original database through the manager and ingest something memorable
    let manager = await AegisMemoryManager.create({
      agentId: "agent-test",
      workspaceDir: testDir,
      config: {},
    });
    
    // Ingest specific sentence
    ingestChunk(manager!.getDb(), {
      sourcePath: "planarian-knowledge.md",
      content: "Planarians can regrow their entire head from a severed tail.",
      source: "memory",
    });

    // Verify search works on original
    let docs = await executeRetrievalPipeline(manager!.getDb(), "Planarians regrow", DEFAULT_AEGIS_CONFIG);
    expect(docs.length).toBeGreaterThan(0);

    // 2. Take a Snapshot using Tardigrade
    const backupDir = path.join(testDir, "backups");
    const snapshotResult = await createSnapshot(manager!.getDb(), backupDir);
    expect(fs.existsSync(snapshotResult.snapshotPath)).toBe(true);

    // 3. Close the DB and Corrupt/Destroy the working directory
    await manager!.close();
    
    // Simulate disaster: write garbage over the DB
    fs.writeFileSync(dbPath, "COMPLETELY CORRUPTED GARBAGE BITS");
    
    // Verify it's corrupted (manager creation will likely fail or DB will be empty/throw)
    try {
      const dbFileStats = fs.statSync(dbPath);
      expect(dbFileStats.size).toBeLessThan(1024); // tiny garbage string
    } catch {}

    // 4. Run Restore (The Magic of Planarian)
    const restoreResult = await restoreFromSnapshot(snapshotResult.snapshotPath, dbPath);
    expect(restoreResult.success).toBe(true);

    // 5. Re-open via Manager to verify Memory is fully intact
    const restoredManager = await AegisMemoryManager.create({
      agentId: "agent-test",
      workspaceDir: testDir,
      config: {},
    });

    const restoredDocs = await executeRetrievalPipeline(
      restoredManager!.getDb(),
      "Planarians regrow head",
      DEFAULT_AEGIS_CONFIG
    );

    // It should find the original knowledge because indexes were rebuilt and content restored
    expect(restoredDocs.length).toBeGreaterThan(0);
    expect(restoredDocs[0].snippet).toContain("Planarians can regrow");

    await restoredManager!.close();
  });

  it("fails gracefully given a non-existent backup file", async () => {
    // Attempt restore
    await expect(restoreFromSnapshot(
      path.join(testDir, "does-not-exist.db.bak"), 
      dbPath
    )).rejects.toThrow("Backup file not found");
  });
});
