import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { AegisMemoryManager } from "../../src/aegis-manager.js";

let manager: AegisMemoryManager;
let testDir: string;

beforeEach(async () => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-manager-"));

  // Create memory directory with test files
  const memoryDir = path.join(testDir, "memory");
  fs.mkdirSync(memoryDir, { recursive: true });

  fs.writeFileSync(
    path.join(memoryDir, "facts.md"),
    "# Facts\n\nThe Orca whale is the largest member of the dolphin family.\nOrca pods have complex social structures and communication.\n",
  );

  fs.writeFileSync(
    path.join(memoryDir, "project.md"),
    "# SkyClaw Project\n\nSkyClaw is an AI agent platform built with TypeScript.\nIt uses SQLite for local-first data storage.\nMemory Aegis is the cognitive memory engine.\n",
  );

  fs.writeFileSync(
    path.join(testDir, "MEMORY.md"),
    "# Memory Index\n\n- facts.md — Animal facts\n- project.md — Project info\n",
  );

  manager = (await AegisMemoryManager.create({
    agentId: "test-agent",
    workspaceDir: testDir,
  }))!;

  expect(manager).not.toBeNull();
});

afterEach(async () => {
  await manager?.close();
  fs.rmSync(testDir, { recursive: true, force: true });
});

describe("AegisMemoryManager interface compliance", () => {
  it("implements search()", async () => {
    // Sync first to ingest files
    await manager.sync({ reason: "test", force: true });

    const results = await manager.search("Orca whale dolphin", {});
    expect(Array.isArray(results)).toBe(true);

    if (results.length > 0) {
      const r = results[0];
      expect(r).toHaveProperty("path");
      expect(r).toHaveProperty("startLine");
      expect(r).toHaveProperty("endLine");
      expect(r).toHaveProperty("score");
      expect(r).toHaveProperty("snippet");
      expect(r).toHaveProperty("source");
    }
  });

  it("implements readFile() for physical files", async () => {
    const result = await manager.readFile({ relPath: "MEMORY.md" });
    expect(result.text).toContain("Memory Index");
    expect(result.path).toBe("MEMORY.md");
  });

  it("implements status()", () => {
    const status = manager.status();
    expect(status.backend).toBe("aegis");
    expect(status.provider).toBe("aegis-fts5");
    expect(status.fts?.enabled).toBe(true);
    expect(status.fts?.available).toBe(true);
    expect(status.custom?.aegis).toBeDefined();
    expect((status.custom!.aegis as any).version).toBe("4.0.0");
  });

  it("implements sync()", async () => {
    let progressCalled = false;
    await manager.sync({
      reason: "test",
      force: true,
      progress: (update) => {
        progressCalled = true;
        expect(update).toHaveProperty("completed");
        expect(update).toHaveProperty("total");
      },
    });
    expect(progressCalled).toBe(true);

    // After sync, status should show indexed files
    const status = manager.status();
    expect(status.chunks).toBeGreaterThan(0);
  });

  it("implements probeEmbeddingAvailability()", async () => {
    const result = await manager.probeEmbeddingAvailability();
    expect(result.ok).toBe(true);
    // No error because Aegis doesn't need embeddings
    expect(result.error).toBeUndefined();
  });

  it("implements probeVectorAvailability()", async () => {
    const result = await manager.probeVectorAvailability();
    expect(result).toBe(true);
  });

  it("implements close()", async () => {
    // Should not throw
    await manager.close();
  });
});

describe("Search after sync", () => {
  it("finds content from synced files", async () => {
    await manager.sync({ reason: "test", force: true });

    const results = await manager.search("SkyClaw TypeScript", {});
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].snippet).toContain("SkyClaw");
  });

  it("respects maxResults", async () => {
    await manager.sync({ reason: "test", force: true });

    const results = await manager.search("AI memory", { maxResults: 1 });
    expect(results.length).toBeLessThanOrEqual(1);
  });

  it("returns source=memory for memory files", async () => {
    await manager.sync({ reason: "test", force: true });

    const results = await manager.search("Orca whale", {});
    if (results.length > 0) {
      expect(results[0].source).toBe("memory");
    }
  });
});

describe("Status reporting", () => {
  it("reports layer configuration", () => {
    const status = manager.status();
    const aegis = status.custom!.aegis as any;
    expect(aegis.layers).toContain("elephant");
    expect(aegis.layers).toContain("orca");
    expect(aegis.layers).toContain("salmon");
    expect(aegis.layers).toContain("dolphin");
  });

  it("reports node/edge/entity counts", async () => {
    await manager.sync({ reason: "test", force: true });

    const status = manager.status();
    expect(status.chunks).toBeGreaterThan(0);

    const aegis = status.custom!.aegis as any;
    expect(typeof aegis.entityCount).toBe("number");
    expect(typeof aegis.edgeCount).toBe("number");
  });

  it("reports database path", () => {
    const status = manager.status();
    expect(status.dbPath).toContain("memory-aegis.db");
    expect(status.workspaceDir).toBe(testDir);
  });
});

describe("Manager caching", () => {
  it("returns same instance for same agent", async () => {
    const m1 = await AegisMemoryManager.create({
      agentId: "cache-test",
      workspaceDir: testDir,
    });
    const m2 = await AegisMemoryManager.create({
      agentId: "cache-test",
      workspaceDir: testDir,
    });

    expect(m1).toBe(m2);
    await m1?.close();
  });
});
