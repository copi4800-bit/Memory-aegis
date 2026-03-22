import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { getSchemaVersion } from "../../src/db/migrate.js";

let testDb: AegisDatabase;
let testDir: string;

beforeEach(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-test-"));
  const dbPath = path.join(testDir, "test-aegis.db");
  testDb = openDatabase(dbPath);
});

afterEach(() => {
  testDb.close();
  fs.rmSync(testDir, { recursive: true, force: true });
});

describe("Database initialization", () => {
  it("creates database file", () => {
    expect(fs.existsSync(path.join(testDir, "test-aegis.db"))).toBe(true);
  });

  it("creates all 21 tables", () => {
    const tables = testDb.db.prepare(
      "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
    ).all() as Array<{ name: string }>;

    const tableNames = tables.map((t) => t.name);
    expect(tableNames).toContain("memory_nodes");
    expect(tableNames).toContain("memory_edges");
    expect(tableNames).toContain("fingerprints");
    expect(tableNames).toContain("drift_events");
    expect(tableNames).toContain("dedup_routes");
    expect(tableNames).toContain("entities");
    expect(tableNames).toContain("entity_aliases");
    expect(tableNames).toContain("concept_nodes");
    expect(tableNames).toContain("concept_inheritance");
    expect(tableNames).toContain("derived_relations");
    expect(tableNames).toContain("temporal_patterns");
    expect(tableNames).toContain("procedures");
    expect(tableNames).toContain("procedure_steps");
    expect(tableNames).toContain("tool_artifacts");
    expect(tableNames).toContain("correction_traces");
    expect(tableNames).toContain("interaction_states");
    expect(tableNames).toContain("context_textures");
    expect(tableNames).toContain("subgraph_partitions");
    expect(tableNames).toContain("subgraph_memberships");
    expect(tableNames).toContain("memory_events");
    expect(tableNames).toContain("schema_version");
  });

  it("creates FTS5 virtual table", () => {
    const vtables = testDb.db.prepare(
      "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'",
    ).all() as Array<{ name: string }>;
    expect(vtables.some((t) => t.name === "memory_nodes_fts")).toBe(true);
  });

  it("has latest schema version", () => {
    const version = getSchemaVersion(testDb.db);
    expect(version).toBe(6);
  });

  it("WAL mode is enabled", () => {
    const mode = testDb.db.pragma("journal_mode") as Array<{ journal_mode: string }>;
    expect(mode[0].journal_mode).toBe("wal");
  });

  it("foreign keys are enabled", () => {
    const fk = testDb.db.pragma("foreign_keys") as Array<{ foreign_keys: number }>;
    expect(fk[0].foreign_keys).toBe(1);
  });
});

describe("CHECK constraints", () => {
  it("rejects invalid memory_state", () => {
    expect(() => {
      testDb.db.prepare(`
        INSERT INTO memory_nodes (id, memory_type, content, status, memory_state, created_at, updated_at)
        VALUES ('test1', 'semantic_fact', 'test', 'active', 'INVALID', datetime('now'), datetime('now'))
      `).run();
    }).toThrow();
  });

  it("rejects importance > 1", () => {
    expect(() => {
      testDb.db.prepare(`
        INSERT INTO memory_nodes (id, memory_type, content, status, importance, created_at, updated_at)
        VALUES ('test2', 'semantic_fact', 'test', 'active', 1.5, datetime('now'), datetime('now'))
      `).run();
    }).toThrow();
  });

  it("rejects negative importance", () => {
    expect(() => {
      testDb.db.prepare(`
        INSERT INTO memory_nodes (id, memory_type, content, status, importance, created_at, updated_at)
        VALUES ('test3', 'semantic_fact', 'test', 'active', -0.1, datetime('now'), datetime('now'))
      `).run();
    }).toThrow();
  });

  it("accepts valid memory_state values", () => {
    const states = ["volatile", "stable", "crystallized", "suppressed", "archived"];
    for (const state of states) {
      expect(() => {
        testDb.db.prepare(`
          INSERT INTO memory_nodes (id, memory_type, content, status, memory_state, created_at, updated_at)
          VALUES (?, 'semantic_fact', 'test', 'active', ?, datetime('now'), datetime('now'))
        `).run(`valid-${state}`, state);
      }).not.toThrow();
    }
  });
});

describe("FTS5 sync triggers", () => {
  it("INSERT auto-updates FTS", () => {
    testDb.db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, created_at, updated_at)
      VALUES ('fts-test-1', 'semantic_fact', 'quantum computing research paper', 'quantum', 'user', 'active', datetime('now'), datetime('now'))
    `).run();

    const results = testDb.db.prepare(
      "SELECT rowid FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'quantum'",
    ).all();
    expect(results.length).toBe(1);
  });

  it("DELETE auto-removes from FTS", () => {
    testDb.db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, created_at, updated_at)
      VALUES ('fts-del-1', 'semantic_fact', 'deletable unique content xyzzy', 'active', datetime('now'), datetime('now'))
    `).run();

    // Verify it's in FTS
    let results = testDb.db.prepare(
      "SELECT rowid FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'xyzzy'",
    ).all();
    expect(results.length).toBe(1);

    // Delete
    testDb.db.prepare("DELETE FROM memory_nodes WHERE id = 'fts-del-1'").run();

    // Verify it's gone from FTS
    results = testDb.db.prepare(
      "SELECT rowid FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'xyzzy'",
    ).all();
    expect(results.length).toBe(0);
  });

  it("UPDATE auto-refreshes FTS", () => {
    testDb.db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, created_at, updated_at)
      VALUES ('fts-upd-1', 'semantic_fact', 'original alpha content', 'active', datetime('now'), datetime('now'))
    `).run();

    // Update content
    testDb.db.prepare(
      "UPDATE memory_nodes SET content = 'modified beta content' WHERE id = 'fts-upd-1'",
    ).run();

    // Old content gone
    const oldResults = testDb.db.prepare(
      "SELECT rowid FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'alpha'",
    ).all();
    expect(oldResults.length).toBe(0);

    // New content searchable
    const newResults = testDb.db.prepare(
      "SELECT rowid FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'beta'",
    ).all();
    expect(newResults.length).toBe(1);
  });
});

describe("Foreign key cascades", () => {
  it("deleting a node cascades to edges", () => {
    // Create two nodes and an edge
    testDb.db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, created_at, updated_at)
      VALUES ('fk-a', 'semantic_fact', 'node a', 'active', datetime('now'), datetime('now'))
    `).run();
    testDb.db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, created_at, updated_at)
      VALUES ('fk-b', 'semantic_fact', 'node b', 'active', datetime('now'), datetime('now'))
    `).run();
    testDb.db.prepare(`
      INSERT INTO memory_edges (id, src_node_id, dst_node_id, edge_type, status, created_at, updated_at)
      VALUES ('edge-1', 'fk-a', 'fk-b', 'related_to', 'active', datetime('now'), datetime('now'))
    `).run();

    // Delete source node
    testDb.db.prepare("DELETE FROM memory_nodes WHERE id = 'fk-a'").run();

    // Edge should be cascade-deleted
    const edges = testDb.db.prepare("SELECT * FROM memory_edges WHERE id = 'edge-1'").all();
    expect(edges.length).toBe(0);
  });
});

describe("Unique constraints", () => {
  it("entity alias is unique per entity", () => {
    testDb.db.prepare(`
      INSERT INTO entities (id, entity_type, canonical_name, status, created_at, updated_at)
      VALUES ('e1', 'person', 'John', 'active', datetime('now'), datetime('now'))
    `).run();
    testDb.db.prepare(`
      INSERT INTO entity_aliases (id, entity_id, alias_text, confidence, created_at, updated_at)
      VALUES ('a1', 'e1', 'Johnny', 0.8, datetime('now'), datetime('now'))
    `).run();

    // Duplicate alias should fail
    expect(() => {
      testDb.db.prepare(`
        INSERT INTO entity_aliases (id, entity_id, alias_text, confidence, created_at, updated_at)
        VALUES ('a2', 'e1', 'Johnny', 0.9, datetime('now'), datetime('now'))
      `).run();
    }).toThrow();
  });
});
