import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestChunk } from "../../src/core/ingest.js";
import {
  storeElephantMemory,
  findElephantOverrides,
  computeElephantRelevance,
  checkAntiRegression,
  consolidateElephant,
  listElephantMemories,
} from "../../src/cognitive/elephant.js";
import { tokenizeToSet } from "../../src/core/normalize.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";

let db: AegisDatabase;
let testDir: string;

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-elephant-"));
  db = openDatabase(path.join(testDir, "test.db"));
});

afterEach(() => {
  db.close();
  fs.rmSync(testDir, { recursive: true, force: true });
});

describe("storeElephantMemory", () => {
  it("creates crystallized trauma memory with max importance", () => {
    const id = storeElephantMemory(db.db, "NEVER drop production database", "trauma", {
      subject: "database safety",
      overridePriority: 200,
    });

    const node = db.db.prepare("SELECT * FROM memory_nodes WHERE id = ?").get(id) as any;
    expect(node.memory_type).toBe("trauma");
    expect(node.memory_state).toBe("crystallized");
    expect(node.importance).toBe(1.0);
    expect(node.salience).toBe(1.0);
    expect(node.override_priority).toBe(200);
    expect(node.base_decay_rate).toBe(0);
    expect(node.crystallized_at).not.toBeNull();
  });

  it("creates invariant with default scope=global", () => {
    const id = storeElephantMemory(db.db, "Always use parameterized queries", "invariant");

    const node = db.db.prepare("SELECT * FROM memory_nodes WHERE id = ?").get(id) as any;
    expect(node.scope).toBe("global");
    expect(node.memory_type).toBe("invariant");
  });

  it("logs elephant_store event", () => {
    storeElephantMemory(db.db, "Test event logging", "trauma");

    const events = db.db.prepare(
      "SELECT * FROM memory_events WHERE event_type = 'elephant_store'",
    ).all();
    expect(events.length).toBe(1);
  });
});

describe("findElephantOverrides — multi-signal relevance", () => {
  it("finds relevant trauma memories for matching query", () => {
    storeElephantMemory(db.db, "NEVER delete production database without backup", "trauma", {
      subject: "database safety",
    });

    const overrides = findElephantOverrides(db.db, "delete production database");
    expect(overrides.length).toBe(1);
    expect(overrides[0].content).toContain("NEVER delete");
  });

  it("excludes irrelevant trauma memories", () => {
    storeElephantMemory(db.db, "Always wear safety goggles in the lab", "trauma");

    const overrides = findElephantOverrides(db.db, "TypeScript compiler configuration");
    expect(overrides.length).toBe(0);
  });

  it("respects scope matching", () => {
    storeElephantMemory(db.db, "No force-push to main branch", "invariant", {
      scope: "global",
    });

    // Global scope should match any query
    const overrides = findElephantOverrides(db.db, "force push main branch", "user-session");
    expect(overrides.length).toBe(1);
  });
});

describe("computeElephantRelevance", () => {
  it("returns high score for keyword-matching content", () => {
    const id = storeElephantMemory(db.db, "database backup critical safety procedure", "trauma");
    const node = db.db.prepare("SELECT * FROM memory_nodes WHERE id = ?").get(id) as any;

    const queryTokens = tokenizeToSet("database backup safety");
    const { score, signals } = computeElephantRelevance(db.db, queryTokens, node);

    expect(score).toBeGreaterThan(0.2);
    expect(signals.keywordOverlap).toBeGreaterThan(0);
  });

  it("returns low score for unrelated content", () => {
    const id = storeElephantMemory(db.db, "nuclear reactor safety protocol", "trauma");
    const node = db.db.prepare("SELECT * FROM memory_nodes WHERE id = ?").get(id) as any;

    const queryTokens = tokenizeToSet("chocolate cake recipe");
    const { score } = computeElephantRelevance(db.db, queryTokens, node);

    expect(score).toBeLessThan(0.3);
  });

  it("global scope always gives scopeMatch = 1.0", () => {
    const id = storeElephantMemory(db.db, "test", "invariant", { scope: "global" });
    const node = db.db.prepare("SELECT * FROM memory_nodes WHERE id = ?").get(id) as any;

    const { signals } = computeElephantRelevance(db.db, new Set(["test"]), node, "any-scope");
    expect(signals.scopeMatch).toBe(1.0);
  });
});

describe("checkAntiRegression", () => {
  it("detects contradiction with negation language", () => {
    storeElephantMemory(db.db, "Always backup the database before deployment", "invariant");

    const conflicts = checkAntiRegression(db.db, "We don't need to backup the database anymore");
    expect(conflicts.length).toBeGreaterThan(0);
    expect(conflicts[0].conflictScore).toBeGreaterThan(0);
  });

  it("no conflict for unrelated content", () => {
    storeElephantMemory(db.db, "Always use HTTPS for API calls", "invariant");

    const conflicts = checkAntiRegression(db.db, "The new React component renders a chart");
    expect(conflicts.length).toBe(0);
  });

  it("detects multiple conflicts", () => {
    storeElephantMemory(db.db, "Never skip database migrations", "trauma");
    storeElephantMemory(db.db, "Always run tests before deployment", "invariant");

    const conflicts = checkAntiRegression(
      db.db,
      "Let's skip the database migrations and ignore tests for this deployment",
    );
    expect(conflicts.length).toBe(2);
  });
});

describe("consolidateElephant", () => {
  it("merges similar trauma memories", () => {
    storeElephantMemory(db.db, "Never delete production data without backup", "trauma", {
      overridePriority: 100,
    });
    storeElephantMemory(db.db, "Never delete production data without a backup copy", "trauma", {
      overridePriority: 50,
    });

    const { merged } = consolidateElephant(db.db);
    expect(merged).toBe(1);

    // Only one should remain active
    const active = db.db.prepare(
      "SELECT * FROM memory_nodes WHERE memory_type = 'trauma' AND status = 'active'",
    ).all();
    expect(active.length).toBe(1);
  });

  it("does not merge dissimilar memories", () => {
    storeElephantMemory(db.db, "Never delete production data", "trauma");
    storeElephantMemory(db.db, "Always use HTTPS for API calls", "invariant");

    const { merged } = consolidateElephant(db.db);
    expect(merged).toBe(0);
  });
});

describe("listElephantMemories", () => {
  it("returns all active elephant memories", () => {
    storeElephantMemory(db.db, "Trauma one", "trauma", { overridePriority: 100 });
    storeElephantMemory(db.db, "Invariant one", "invariant", { overridePriority: 50 });

    const list = listElephantMemories(db.db);
    expect(list.length).toBe(2);
    // Ordered by priority
    expect(list[0].priority).toBeGreaterThanOrEqual(list[1].priority);
  });
});

describe("Elephant in full pipeline", () => {
  it("trauma override always appears with score=1.0", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/normal.md",
      content: "Normal database configuration settings.",
      source: "memory",
    });

    storeElephantMemory(
      db.db,
      "NEVER delete production database without backup. Critical incident 2024-01-10.",
      "trauma",
      { subject: "database safety", overridePriority: 100 },
    );

    const results = await executeRetrievalPipeline(db.db, "database production", DEFAULT_AEGIS_CONFIG);
    expect(results.length).toBeGreaterThan(0);

    const traumaResult = results.find((r) => r.snippet.includes("NEVER delete"));
    expect(traumaResult).toBeDefined();
    expect(traumaResult!.score).toBe(1.0);
  });
});
