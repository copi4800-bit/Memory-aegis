import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { AegisMemoryManager, closeAllManagers } from "../../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import { resolve } from "node:path";

describe("E2E Pipeline: Retrieval-Focused", () => {
  let manager: AegisMemoryManager;
  const workspaceDir = resolve(process.cwd(), ".tmp_e2e_retrieval");

  beforeEach(async () => {
    manager = await AegisMemoryManager.create({
      agentId: "test_e2e",
      workspaceDir,
      config: {
        ...DEFAULT_AEGIS_CONFIG,
        // Make sure all target layers are explicitly enabled
        enabledLayers: ["weaver-bird", "elephant", "orca"]
      }
    });

    const db = manager.getDb();
    // Clear out any old data from filesystem persistence
    db.prepare("DELETE FROM memory_nodes").run();
    db.prepare("DELETE FROM episodes").run();
  });

  afterEach(async () => {
    await closeAllManagers();
  });

  it("should successfully run Ingest -> Hybrid Search -> Rerank -> Chameleon Router", async () => {
    const db = manager.getDb();
    const insertNode = db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, created_at, updated_at, source_path)
      VALUES (?, ?, ?, ?, ?, 'active', 0.8, datetime('now'), datetime('now'), ?)
    `);

    insertNode.run(
      "node1", "semantic_fact", 
      "GraphQL is a query language for your API, and a server-side runtime for executing queries by using a type system you define for your data.",
      "technical.graphql", "workspace", "/docs/graphql.md"
    );

    insertNode.run(
      "node2", "procedural",
      "# Cách cấu hình GraphQL\\n1. Cài đặt npm i graphql\\n2. Tạo schema",
      "workflow.graphql", "workspace", "/docs/graphql_setup.md"
    );

    insertNode.run(
      "node3", "invariant",
      "Luôn phải xác thực (Authentication) mọi GraphQL mutations.",
      "rules.security.graphql", "global", null
    );

    insertNode.run(
      "node4", "identity",
      "Bot là một Senior GraphQL Developer.",
      "identity.persona", "global", null
    );

    // Verify it was saved (using search first directly)
    const rawResults = await manager.search("graphql auth", { maxResults: 10, minScore: 0 });
    expect(rawResults.length).toBeGreaterThanOrEqual(1);

    // 2. Retrieval End-to-End simulation via Context Assembly (Chameleon)
    // We mock the "agent_start" hook logic here by fetching search hits and routing them.
    const query = "GraphQL";
    const searchedNodes = await manager.search(query, { maxResults: 10, minScore: 0 });
    
    expect(searchedNodes.length).toBeGreaterThanOrEqual(4);

    // Call Chameleon router directly
    const { ChameleonBudgeter } = await import("../../src/cognitive/chameleon.js");
    const xmlContext = ChameleonBudgeter.assemble(searchedNodes, {
      maxChars: 1000, // Tight budget to force zone truncations
      topK: 4,
      query
    });

    // 3. Assertions on the Chameleon XML Output
    expect(xmlContext).toContain("<context-budget>");
    expect(xmlContext).toContain("<core-directives>");
    expect(xmlContext).toContain("<task-memory>");

    // Core Identity and Safety MUST be present in core-directives
    expect(xmlContext).toContain("rules.security.graphql");
    expect(xmlContext).toContain("identity.persona");

    // Task Memory should contain the procedural step (workflow)
    expect(xmlContext).toContain("workflow.graphql");
  });
});
