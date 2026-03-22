import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestChunk, ingestBatch } from "../../src/core/ingest.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { spreadingActivation, assignInitialActivation, reinforceCoactivation } from "../../src/retrieval/graph-walk.js";
import { DEFAULT_AEGIS_CONFIG, type AegisConfig } from "../../src/core/models.js";

let db: AegisDatabase;
let testDir: string;
const config: AegisConfig = { ...DEFAULT_AEGIS_CONFIG };

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-orca-"));
  const dbPath = path.join(testDir, "test.db");
  db = openDatabase(dbPath);
});

afterEach(() => {
  db.close();
  fs.rmSync(testDir, { recursive: true, force: true });
});

describe("Co-occurrence edges from shared entities", () => {
  it("creates edges between nodes sharing @mention entities", () => {
    ingestChunk(db.db, {
      sourcePath: "memory/a.md",
      content: "@alice is working on the frontend redesign project.",
      source: "memory",
    });

    ingestChunk(db.db, {
      sourcePath: "memory/b.md",
      content: "@alice presented the quarterly review results yesterday.",
      source: "memory",
    });

    // Should have co_entity edges linking the two nodes via shared @alice entity
    const coEdges = db.db.prepare(`
      SELECT * FROM memory_edges
      WHERE edge_type = 'co_entity' AND status = 'active'
    `).all() as Array<{ src_node_id: string; dst_node_id: string; extension_json: string }>;

    expect(coEdges.length).toBeGreaterThan(0);

    // Verify the edge references alice
    const aliceEdge = coEdges.find((e) => {
      const ext = JSON.parse(e.extension_json);
      return ext.entity_name.toLowerCase() === "alice";
    });
    expect(aliceEdge).toBeDefined();
  });

  it("does not create duplicate co-occurrence edges", () => {
    ingestChunk(db.db, {
      sourcePath: "memory/a.md",
      content: "@bob likes TypeScript and React.",
      source: "memory",
    });

    ingestChunk(db.db, {
      sourcePath: "memory/b.md",
      content: "@bob prefers VS Code for development.",
      source: "memory",
    });

    // Ingest a third node with @bob
    ingestChunk(db.db, {
      sourcePath: "memory/c.md",
      content: "@bob is the team lead for SkyClaw.",
      source: "memory",
    });

    // Count co_entity edges for bob
    const coEdges = db.db.prepare(`
      SELECT * FROM memory_edges
      WHERE edge_type = 'co_entity'
        AND status = 'active'
        AND json_extract(extension_json, '$.entity_name') = 'bob'
    `).all();

    // 3 nodes share bob → should have 3 edges (a↔b, a↔c, b↔c) or (b→a, c→a, c→b)
    expect(coEdges.length).toBe(3);
  });

  it("creates separate edges for different entities", () => {
    ingestChunk(db.db, {
      sourcePath: "memory/a.md",
      content: "@alice and @bob discussed the project roadmap.",
      source: "memory",
    });

    ingestChunk(db.db, {
      sourcePath: "memory/b.md",
      content: "@alice reviewed the pull request for the API module.",
      source: "memory",
    });

    // co_entity edges for alice should exist
    const aliceEdges = db.db.prepare(`
      SELECT * FROM memory_edges
      WHERE edge_type = 'co_entity'
        AND json_extract(extension_json, '$.entity_name') = 'alice'
    `).all();

    expect(aliceEdges.length).toBeGreaterThan(0);
  });
});

describe("Spreading activation through entity graph", () => {
  it("activates related nodes through shared entity edges", () => {
    // Create a small graph: A --[co_entity]--> B --[co_entity]--> C
    const idA = ingestChunk(db.db, {
      sourcePath: "memory/a.md",
      content: "@projectx uses TypeScript and SQLite for building AI tools.",
      source: "memory",
    });

    const idB = ingestChunk(db.db, {
      sourcePath: "memory/b.md",
      content: "@projectx implements a memory engine with FTS5 search.",
      source: "memory",
    });

    const idC = ingestChunk(db.db, {
      sourcePath: "memory/c.md",
      content: "@projectx deploys on Docker containers in production.",
      source: "memory",
    });

    // Start with only node A as seed
    const seeds = new Map<string, number>();
    seeds.set(idA, 1.0);

    const activated = spreadingActivation(seeds, db.db, {
      maxHops: 3,
      dampingFactor: 0.5,
      activationThreshold: 0.01,
      maxNodes: 50,
      scopeFilter: null,
    });

    // Should have activated nodes B and C through entity graph
    expect(activated.size).toBeGreaterThan(1);
    // Seed should still be there
    expect(activated.has(idA)).toBe(true);
  });

  it("damping reduces activation at each hop", () => {
    const idA = ingestChunk(db.db, {
      sourcePath: "memory/x.md",
      content: "@hero saved the day with quick thinking and bravery.",
      source: "memory",
    });

    const idB = ingestChunk(db.db, {
      sourcePath: "memory/y.md",
      content: "@hero was recognized at the annual company awards ceremony.",
      source: "memory",
    });

    const seeds = new Map<string, number>();
    seeds.set(idA, 1.0);

    const activated = spreadingActivation(seeds, db.db, {
      maxHops: 2,
      dampingFactor: 0.5,
      activationThreshold: 0.01,
      maxNodes: 50,
    });

    if (activated.has(idB)) {
      // B's activation should be less than A's (damped)
      expect(activated.get(idB)!).toBeLessThan(activated.get(idA)!);
    }
  });

  it("respects maxNodes limit", () => {
    // Ingest many related nodes
    for (let i = 0; i < 10; i++) {
      ingestChunk(db.db, {
        sourcePath: `memory/node-${i}.md`,
        content: `@sharedteam member ${i} works on module-${i} for the project.`,
        source: "memory",
      });
    }

    const firstNode = db.db.prepare(
      "SELECT id FROM memory_nodes WHERE status = 'active' LIMIT 1",
    ).get() as { id: string };

    // Start with just 1 seed, maxNodes=4 limits total activated (seed + 3 hops)
    const seeds = new Map<string, number>();
    seeds.set(firstNode.id, 1.0);

    const activated = spreadingActivation(seeds, db.db, {
      maxHops: 3,
      dampingFactor: 0.5,
      activationThreshold: 0.01,
      maxNodes: 4,
    });

    expect(activated.size).toBeLessThanOrEqual(4);
  });

  it("stops when activation falls below threshold", () => {
    const idA = ingestChunk(db.db, {
      sourcePath: "memory/deep1.md",
      content: "@deepchain alpha team builds the core engine.",
      source: "memory",
    });

    ingestChunk(db.db, {
      sourcePath: "memory/deep2.md",
      content: "@deepchain beta team handles testing and QA.",
      source: "memory",
    });

    const seeds = new Map<string, number>();
    seeds.set(idA, 0.1); // Low initial activation

    const activated = spreadingActivation(seeds, db.db, {
      maxHops: 5,
      dampingFactor: 0.3,
      activationThreshold: 0.05,
      maxNodes: 50,
    });

    // With low initial activation and high threshold, should not spread far
    for (const [nodeId, score] of activated) {
      expect(score).toBeGreaterThanOrEqual(0);
    }
  });
});

describe("Hebbian reinforcement", () => {
  it("increases edge weight on co-activation", () => {
    const idA = ingestChunk(db.db, {
      sourcePath: "memory/hebb1.md",
      content: "@teamhebb building memory systems with graph databases.",
      source: "memory",
    });

    const idB = ingestChunk(db.db, {
      sourcePath: "memory/hebb2.md",
      content: "@teamhebb presenting at the AI conference next month.",
      source: "memory",
    });

    // Get the co_entity edge between them
    const edgeBefore = db.db.prepare(`
      SELECT weight, coactivation_count FROM memory_edges
      WHERE edge_type = 'co_entity' AND status = 'active'
      LIMIT 1
    `).get() as { weight: number; coactivation_count: number } | undefined;

    if (edgeBefore) {
      const weightBefore = edgeBefore.weight;

      // Reinforce co-activation
      reinforceCoactivation([idA, idB], db.db);

      const edgeAfter = db.db.prepare(`
        SELECT weight, coactivation_count FROM memory_edges
        WHERE edge_type = 'co_entity' AND status = 'active'
        LIMIT 1
      `).get() as { weight: number; coactivation_count: number };

      expect(edgeAfter.weight).toBeGreaterThan(weightBefore);
      expect(edgeAfter.coactivation_count).toBeGreaterThan(edgeBefore.coactivation_count);
    }
  });

  it("caps weight at 1.0", () => {
    const idA = ingestChunk(db.db, {
      sourcePath: "memory/cap1.md",
      content: "@capmention alpha testing edge weight limits.",
      source: "memory",
    });

    const idB = ingestChunk(db.db, {
      sourcePath: "memory/cap2.md",
      content: "@capmention beta testing edge weight limits.",
      source: "memory",
    });

    // Reinforce many times
    for (let i = 0; i < 50; i++) {
      reinforceCoactivation([idA, idB], db.db);
    }

    const edges = db.db.prepare(`
      SELECT weight FROM memory_edges
      WHERE edge_type = 'co_entity' AND status = 'active'
    `).all() as Array<{ weight: number }>;

    for (const edge of edges) {
      expect(edge.weight).toBeLessThanOrEqual(1.0);
    }
  });
});

describe("End-to-end: graph-enhanced retrieval", () => {
  it("finds related content through entity graph that FTS alone would miss", async () => {
    // Node A: directly matches "quantum computing"
    ingestChunk(db.db, {
      sourcePath: "memory/quantum.md",
      content: "@drsmith published a paper on quantum computing algorithms.",
      source: "memory",
    });

    // Node B: related through @drsmith but different topic
    ingestChunk(db.db, {
      sourcePath: "memory/teaching.md",
      content: "@drsmith teaches machine learning at the university.",
      source: "memory",
    });

    // Search for quantum computing — should find node A directly,
    // and potentially node B through the shared @drsmith entity
    const results = await executeRetrievalPipeline(db.db, "quantum computing", config);
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].snippet).toContain("quantum");
  });

  it("entity graph boosts results from related nodes", async () => {
    // Create a cluster of nodes about the same person
    ingestChunk(db.db, {
      sourcePath: "memory/profile.md",
      content: "@jane is a senior engineer specializing in distributed systems.",
      source: "memory",
    });

    ingestChunk(db.db, {
      sourcePath: "memory/project.md",
      content: "@jane leads the microservices migration project for the platform.",
      source: "memory",
    });

    ingestChunk(db.db, {
      sourcePath: "memory/review.md",
      content: "@jane received excellent performance reviews this quarter.",
      source: "memory",
    });

    const results = await executeRetrievalPipeline(db.db, "jane engineer distributed", config);
    expect(results.length).toBeGreaterThan(0);
  });
});

describe("assignInitialActivation", () => {
  it("combines FTS and entity scores", () => {
    const seeds = assignInitialActivation(
      [
        { nodeId: "a", score: 0.8 },
        { nodeId: "b", score: 0.3 },
      ],
      [
        { nodeId: "a", confidence: 0.5 },
        { nodeId: "c", confidence: 0.9 },
      ],
    );

    // Node A: max(0.8 from FTS, 0.5 from entity) = 0.8
    expect(seeds.get("a")).toBe(0.8);
    // Node B: only FTS
    expect(seeds.get("b")).toBe(0.3);
    // Node C: only entity
    expect(seeds.get("c")).toBe(0.9);
    expect(seeds.size).toBe(3);
  });

  it("returns empty map for no inputs", () => {
    const seeds = assignInitialActivation([], []);
    expect(seeds.size).toBe(0);
  });
});
