import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestChunk, ingestBatch } from "../../src/core/ingest.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { DEFAULT_AEGIS_CONFIG, type AegisConfig } from "../../src/core/models.js";
import { storeElephantMemory } from "../../src/cognitive/elephant.js";
import { runMaintenanceCycle } from "../../src/retention/maintenance.js";

let db: AegisDatabase;
let testDir: string;
const config: AegisConfig = { ...DEFAULT_AEGIS_CONFIG };

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-pipeline-"));
  const dbPath = path.join(testDir, "test.db");
  db = openDatabase(dbPath);
});

afterEach(() => {
  db.close();
  fs.rmSync(testDir, { recursive: true, force: true });
});

describe("Ingest → Search round-trip", () => {
  it("ingests content and finds it via FTS5", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/2024-01-15.md",
      content: "The SkyClaw project uses TypeScript and SQLite for local-first AI memory.",
      source: "memory",
    });

    const results = await executeRetrievalPipeline(db.db, "SkyClaw TypeScript", config);
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].snippet).toContain("SkyClaw");
  });

  it("returns results with valid MemorySearchResult shape", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/test.md",
      content: "OpenClaw is a personal AI assistant platform.",
      source: "memory",
    });

    const results = await executeRetrievalPipeline(db.db, "OpenClaw assistant", config);
    expect(results.length).toBeGreaterThan(0);

    const result = results[0];
    expect(result).toHaveProperty("path");
    expect(result).toHaveProperty("startLine");
    expect(result).toHaveProperty("endLine");
    expect(result).toHaveProperty("score");
    expect(result).toHaveProperty("snippet");
    expect(result).toHaveProperty("source");
    expect(typeof result.score).toBe("number");
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(1);
    expect(["memory", "sessions"]).toContain(result.source);
  });

  it("respects maxResults limit", async () => {
    // Ingest many items
    for (let i = 0; i < 20; i++) {
      ingestChunk(db.db, {
        sourcePath: `memory/item-${i}.md`,
        content: `Memory item number ${i} about artificial intelligence and machine learning.`,
        source: "memory",
      });
    }

    const results = await executeRetrievalPipeline(db.db, "artificial intelligence", config, {
      maxResults: 3,
    });
    expect(results.length).toBeLessThanOrEqual(3);
  });

  it("deduplicates identical content", () => {
    const content = "This is exactly the same content for dedup testing.";

    const id1 = ingestChunk(db.db, { sourcePath: "a.md", content, source: "memory" });
    const id2 = ingestChunk(db.db, { sourcePath: "b.md", content, source: "memory" });

    // Should reuse the same node
    expect(id1).toBe(id2);

    // Node should have frequency_count = 2
    const node = db.db.prepare("SELECT frequency_count FROM memory_nodes WHERE id = ?").get(id1) as {
      frequency_count: number;
    };
    expect(node.frequency_count).toBe(2);
  });

  it("finds content via partial query", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/deploy.md",
      content: "Deploy the application to production using Docker containers on AWS EC2.",
      source: "memory",
    });

    // "Docker container" — "container*" prefix matches "containers" via FTS5
    const results = await executeRetrievalPipeline(db.db, "Docker container", config);
    expect(results.length).toBeGreaterThan(0);
  });

  it("returns empty for unrelated query", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/cats.md",
      content: "Cats are wonderful pets that love to sleep.",
      source: "memory",
    });

    const results = await executeRetrievalPipeline(db.db, "quantum physics thermodynamics", config);
    // May return 0 or low-score results
    for (const r of results) {
      // If any results returned, they should have low scores
      expect(r.score).toBeLessThan(0.8);
    }
  });
});

describe("Batch ingest", () => {
  it("ingests multiple chunks in one transaction", async () => {
    const chunks = [
      { sourcePath: "memory/a.md", content: "First chunk about React components.", source: "memory" as const },
      { sourcePath: "memory/b.md", content: "Second chunk about Vue.js framework.", source: "memory" as const },
      { sourcePath: "memory/c.md", content: "Third chunk about Angular services.", source: "memory" as const },
    ];

    const ids = ingestBatch(db.db, chunks);
    expect(ids.length).toBe(3);

    // All should be searchable
    const results = await executeRetrievalPipeline(db.db, "React components", config);
    expect(results.length).toBeGreaterThan(0);
  });
});

describe("Elephant override", () => {
  it("trauma memory always appears in results", async () => {
    // Store normal memory
    ingestChunk(db.db, {
      sourcePath: "memory/normal.md",
      content: "Normal database configuration settings for production.",
      source: "memory",
    });

    // Store trauma memory
    storeElephantMemory(db.db, "NEVER delete production database without backup. Critical incident on 2024-01-10.", "trauma", {
      subject: "database safety",
      scope: "global",
      overridePriority: 100,
    });

    // Search for database topic
    const results = await executeRetrievalPipeline(db.db, "database production", config);
    expect(results.length).toBeGreaterThan(0);

    // Trauma memory should be present with high score
    const traumaResult = results.find((r) => r.snippet.includes("NEVER delete"));
    expect(traumaResult).toBeDefined();
    expect(traumaResult!.score).toBe(1.0);
    expect(traumaResult!.citation).toContain("trauma");
  });
});

describe("Session vs Memory scope", () => {
  it("session-scoped content returns source=sessions", async () => {
    ingestChunk(db.db, {
      sourcePath: "sessions/2024-01-15.json",
      content: "User discussed their preference for dark mode interfaces.",
      source: "sessions",
    });

    const results = await executeRetrievalPipeline(db.db, "dark mode preference", config);
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].source).toBe("sessions");
  });

  it("memory-scoped content returns source=memory", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/prefs.md",
      content: "Preferred IDE is VS Code with Vim keybindings.",
      source: "memory",
    });

    const results = await executeRetrievalPipeline(db.db, "VS Code Vim", config);
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].source).toBe("memory");
  });
});

describe("Entity extraction during ingest", () => {
  it("creates entities from @mentions", () => {
    ingestChunk(db.db, {
      sourcePath: "memory/team.md",
      content: "@john and @jane are working on the SkyClaw project together.",
      source: "memory",
    });

    const entities = db.db.prepare("SELECT * FROM entities WHERE status = 'active'").all() as Array<{
      canonical_name: string;
    }>;
    const names = entities.map((e) => e.canonical_name.toLowerCase());
    expect(names).toContain("john");
    expect(names).toContain("jane");
  });

  it("creates entity aliases", () => {
    ingestChunk(db.db, {
      sourcePath: "memory/people.md",
      content: "@boss is the project lead.",
      source: "memory",
    });

    const aliases = db.db.prepare("SELECT * FROM entity_aliases").all();
    expect(aliases.length).toBeGreaterThan(0);
  });
});

describe("Fingerprint dedup", () => {
  it("normalized dedup catches formatting differences", () => {
    const id1 = ingestChunk(db.db, {
      sourcePath: "a.md",
      content: "Hello,  world!  This is a test.",
      source: "memory",
    });

    const id2 = ingestChunk(db.db, {
      sourcePath: "b.md",
      content: "Hello, world! This is a test.",
      source: "memory",
    });

    // Should be same node (normalized hash matches)
    expect(id1).toBe(id2);
  });
});

describe("Maintenance cycle", () => {
  it("runs without errors on empty database", async () => {
    const report = await runMaintenanceCycle(db.db, testDir, DEFAULT_AEGIS_CONFIG);
    expect(report.stateTransitions).toBe(0);
    expect(report.ftsOptimized).toBe(true);
  });

  it("expires TTL nodes", async () => {
    // Insert a node with expired TTL
    const pastDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    db.db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, ttl_expires_at, created_at, updated_at)
      VALUES ('ttl-expired', 'working_scratch', 'temporary data', 'active', ?, datetime('now'), datetime('now'))
    `).run(pastDate);

    const report = await runMaintenanceCycle(db.db, testDir, DEFAULT_AEGIS_CONFIG);
    expect(report.ttlExpired).toBe(1);

    // Node should be expired
    const node = db.db.prepare("SELECT status FROM memory_nodes WHERE id = 'ttl-expired'").get() as {
      status: string;
    };
    expect(node.status).toBe("expired");
  });
});

describe("Citation format", () => {
  it("citation includes memory type", async () => {
    ingestChunk(db.db, {
      sourcePath: "memory/facts.md",
      content: "The speed of light is approximately 299792458 meters per second.",
      source: "memory",
    });

    const results = await executeRetrievalPipeline(db.db, "speed of light", config);
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].citation).toContain("[");
    expect(results[0].citation).toContain("]");
  });
});

describe("Recall count tracking", () => {
  it("increments recall_count on search hit", async () => {
    const nodeId = ingestChunk(db.db, {
      sourcePath: "memory/recall.md",
      content: "Unique zaphodbeeblebrox content for recall tracking test.",
      source: "memory",
    });

    // First search
    await executeRetrievalPipeline(db.db, "zaphodbeeblebrox", config);

    const after1 = db.db.prepare("SELECT recall_count FROM memory_nodes WHERE id = ?").get(nodeId) as {
      recall_count: number;
    };

    // Second search
    await executeRetrievalPipeline(db.db, "zaphodbeeblebrox", config);

    const after2 = db.db.prepare("SELECT recall_count FROM memory_nodes WHERE id = ?").get(nodeId) as {
      recall_count: number;
    };

    expect(after2.recall_count).toBeGreaterThan(after1.recall_count);
  });
});

describe("Pipeline Stage 4 — Sea Lion inference", () => {
  it("discovers nodes via concept inheritance during search", async () => {
    // Import sea-lion functions
    const { upsertConcept, addInheritance } = await import("../../src/cognitive/sea-lion.js");

    // Ingest two nodes
    const nodeA = ingestChunk(db.db, {
      sourcePath: "memory/ts-config.md",
      content: "TypeScript strict mode configuration for the SkyClaw project.",
      source: "memory",
    });

    const nodeB = ingestChunk(db.db, {
      sourcePath: "memory/ts-patterns.md",
      content: "Common TypeScript design patterns including dependency injection.",
      source: "memory",
    });

    // Create concept and link both nodes
    const tsConceptId = upsertConcept(db.db, "TypeScript", "language", {
      rulePayload: { always_lint: true },
      confidence: 0.9,
    });

    addInheritance(db.db, { kind: "node", id: nodeA }, { kind: "concept", id: tsConceptId }, "uses");
    addInheritance(db.db, { kind: "node", id: nodeB }, { kind: "concept", id: tsConceptId }, "uses");

    // Search with sea-lion enabled
    const configWithSeaLion: AegisConfig = {
      ...DEFAULT_AEGIS_CONFIG,
      enabledLayers: ["elephant", "orca", "sea-lion", "salmon", "dolphin"],
    };

    const results = await executeRetrievalPipeline(db.db, "SkyClaw project", configWithSeaLion);
    expect(results.length).toBeGreaterThan(0);
  });
});

describe("Pipeline Stage 5 — Salmon dedup", () => {
  it("deduplicates nodes with same normalized content in results", async () => {
    // Manually insert nodes with same normalized_hash
    const now = new Date().toISOString();
    const normalizedHash = "test_dedup_normalized_hash_abc123";

    db.db.prepare(`
      INSERT INTO memory_nodes (
        id, memory_type, content, scope, status, importance, salience, memory_state,
        raw_hash, normalized_hash, frequency_count, created_at, updated_at,
        source_path, source_start_line, source_end_line
      ) VALUES (
        'dup-node-1', 'semantic_fact', 'Aegis memory engine uses FTS5 for search.', 'user', 'active',
        0.5, 0.3, 'volatile', 'raw_unique_1', ?, 1, ?, ?, 'dedup1.md', 0, 0
      )
    `).run(normalizedHash, now, now);

    db.db.prepare(`
      INSERT INTO memory_nodes (
        id, memory_type, content, scope, status, importance, salience, memory_state,
        raw_hash, normalized_hash, frequency_count, created_at, updated_at,
        source_path, source_start_line, source_end_line
      ) VALUES (
        'dup-node-2', 'semantic_fact', 'Aegis  memory engine  uses FTS5 for search!', 'user', 'active',
        0.5, 0.3, 'volatile', 'raw_unique_2', ?, 1, ?, ?, 'dedup2.md', 0, 0
      )
    `).run(normalizedHash, now, now);

    // Index into FTS5
    db.db.prepare(`
      INSERT INTO memory_nodes_fts (rowid, content, canonical_subject)
      SELECT rowid, content, canonical_subject FROM memory_nodes WHERE id IN ('dup-node-1', 'dup-node-2')
    `).run();

    // Search with salmon enabled
    const configWithSalmon: AegisConfig = {
      ...DEFAULT_AEGIS_CONFIG,
      enabledLayers: ["elephant", "orca", "salmon"],
    };

    const results = await executeRetrievalPipeline(db.db, "Aegis memory FTS5", configWithSalmon);

    // Count how many results match our dup nodes
    const dupResults = results.filter((r) =>
      r.snippet.includes("Aegis") && r.snippet.includes("FTS5"),
    );

    // Should have at most 1 — dedup removed the other
    expect(dupResults.length).toBeLessThanOrEqual(1);
  });
});
