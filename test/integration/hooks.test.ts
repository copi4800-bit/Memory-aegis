import { describe, it, expect, beforeEach, afterEach } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { runMigrations } from "../../src/db/migrate.js";
import { createSessionHooks } from "../../src/hooks/session-hook.js";
import { createToolHooks } from "../../src/hooks/tool-hook.js";
import { createMessageHooks } from "../../src/hooks/message-hook.js";
import { AegisMemoryManager } from "../../src/aegis-manager.js";
import { newId, nowISO } from "../../src/core/id.js";

let testDir: string;
let manager: AegisMemoryManager;

beforeEach(async () => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-hooks-"));
  // Create memory dir so manager can work
  fs.mkdirSync(path.join(testDir, "memory"), { recursive: true });
  manager = (await AegisMemoryManager.create({
    agentId: "test-hooks",
    workspaceDir: testDir,
    config: {
      enabledLayers: ["dolphin", "chimpanzee", "elephant", "orca", "sea-lion", "octopus", "salmon", "nutcracker"],
    },
  }))!;
});

afterEach(async () => {
  await manager.close();
  fs.rmSync(testDir, { recursive: true, force: true });
});

// --- Session Hooks ---

describe("createSessionHooks", () => {
  it("onSessionStart runs without error", async () => {
    const hooks = createSessionHooks(() => manager);
    await expect(hooks.onSessionStart("session-1")).resolves.toBeUndefined();
  });

  it("onSessionStart prewarms entities from session nodes", async () => {
    const db = manager.getDb();
    const now = nowISO();

    // Create a session node with entity mention
    db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, memory_state, scope, salience, created_at, updated_at)
      VALUES ('sn-1', 'semantic_fact', 'session data', 'active', 'volatile', 'session', 0.3, ?, ?)
    `).run(now, now);

    db.prepare(`
      INSERT INTO entities (id, entity_type, canonical_name, scope, status, created_at, updated_at)
      VALUES ('ent-1', 'person', 'Alice', NULL, 'active', ?, ?)
    `).run(now, now);

    db.prepare(`
      INSERT INTO memory_edges (id, src_node_id, dst_node_id, edge_type, weight, confidence, status, coactivation_count, created_at, updated_at, extension_json)
      VALUES ('edge-1', 'sn-1', 'sn-1', 'mentions_entity', 1.0, 1.0, 'active', 1, ?, ?, '{"entity_id":"ent-1"}')
    `).run(now, now);

    const hooks = createSessionHooks(() => manager);
    await hooks.onSessionStart("session-1");

    // Should have created a prewarm event
    const event = db.prepare(
      "SELECT * FROM memory_events WHERE event_type = 'prewarm'",
    ).get() as any;
    expect(event).toBeTruthy();
  });

  it("onSessionEnd consolidates and runs maintenance", async () => {
    const db = manager.getDb();
    const now = nowISO();

    // Create a scratch node with recall_count >= 2 for promotion
    db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, memory_state, scope, recall_count, salience, created_at, updated_at)
      VALUES ('hot-node', 'working_scratch', 'important note', 'active', 'volatile', 'session', 3, 0.5, ?, ?)
    `).run(now, now);

    const hooks = createSessionHooks(() => manager);
    await hooks.onSessionEnd("session-1");

    // Hot node should be promoted to stable
    const node = db.prepare("SELECT memory_state, scope FROM memory_nodes WHERE id = 'hot-node'").get() as any;
    expect(node.memory_state).toBe("stable");
    expect(node.scope).toBe("user");
  });

  it("does nothing when manager is null", async () => {
    const hooks = createSessionHooks(() => null);
    await expect(hooks.onSessionStart("x")).resolves.toBeUndefined();
    await expect(hooks.onSessionEnd("x")).resolves.toBeUndefined();
  });

  it("does nothing when dolphin layer is disabled", async () => {
    // Create a fake manager-like object that reports dolphin as disabled
    const fakeManager = {
      layerEnabled: (layer: string) => false,
      getDb: () => manager.getDb(),
      runMaintenance: () => manager.runMaintenance(),
    } as unknown as AegisMemoryManager;

    const hooks = createSessionHooks(() => fakeManager);
    // Should not throw and should not prewarm/consolidate
    await hooks.onSessionStart("s");
    await hooks.onSessionEnd("s");

    const db = manager.getDb();
    const events = (db.prepare("SELECT COUNT(*) as c FROM memory_events WHERE event_type = 'prewarm'").get() as any).c;
    expect(events).toBe(0);
  });
});

// --- Tool Hooks ---

describe("createToolHooks", () => {
  it("records successful tool calls", async () => {
    const hooks = createToolHooks(() => manager);

    await hooks.afterToolCall({
      toolName: "search_files",
      params: { query: "test" },
      result: { files: ["a.ts"] },
      success: true,
      sessionKey: "s1",
    });

    const db = manager.getDb();
    const artifact = db.prepare(
      "SELECT * FROM tool_artifacts WHERE json_extract(source_text, '$.tool') = 'search_files'",
    ).get() as any;

    expect(artifact).toBeTruthy();
    expect(artifact.success_count).toBe(1);
    expect(artifact.failure_count).toBe(0);
  });

  it("records failed tool calls", async () => {
    const hooks = createToolHooks(() => manager);

    await hooks.afterToolCall({
      toolName: "run_cmd",
      params: { cmd: "bad" },
      result: null,
      success: false,
      error: "command not found",
      sessionKey: "s1",
    });

    const db = manager.getDb();
    const artifact = db.prepare(
      "SELECT * FROM tool_artifacts WHERE json_extract(source_text, '$.tool') = 'run_cmd'",
    ).get() as any;

    expect(artifact).toBeTruthy();
    expect(artifact.failure_count).toBe(1);
    expect(artifact.success_count).toBe(0);
  });

  it("increments counts on repeated tool calls", async () => {
    const hooks = createToolHooks(() => manager);

    await hooks.afterToolCall({
      toolName: "read_file",
      params: {},
      result: "ok",
      success: true,
    });
    await hooks.afterToolCall({
      toolName: "read_file",
      params: {},
      result: "ok",
      success: true,
    });
    await hooks.afterToolCall({
      toolName: "read_file",
      params: {},
      result: null,
      success: false,
      error: "not found",
    });

    const db = manager.getDb();
    const artifact = db.prepare(
      "SELECT * FROM tool_artifacts WHERE json_extract(source_text, '$.tool') = 'read_file'",
    ).get() as any;

    expect(artifact.success_count).toBe(2);
    expect(artifact.failure_count).toBe(1);
  });

  it("does nothing when chimpanzee layer is disabled", async () => {
    const fakeManager = {
      layerEnabled: (layer: string) => false,
      getDb: () => manager.getDb(),
    } as unknown as AegisMemoryManager;

    const hooks = createToolHooks(() => fakeManager);
    await hooks.afterToolCall({
      toolName: "any",
      params: {},
      result: {},
      success: true,
    });

    const db = manager.getDb();
    const count = (db.prepare("SELECT COUNT(*) as c FROM tool_artifacts").get() as any).c;
    expect(count).toBe(0);
  });
});

// --- Message Hooks ---

describe("createMessageHooks", () => {
  it("detects corrections and records them", async () => {
    const hooks = createMessageHooks(() => manager);

    await hooks.onMessageReceived({
      message: "No, that's not right. Use the other method.",
      previousAssistantMessage: "I'll use method A to solve this.",
      sessionKey: "s1",
    });

    const db = manager.getDb();
    const trace = db.prepare(
      "SELECT * FROM correction_traces ORDER BY created_at DESC LIMIT 1",
    ).get() as any;

    expect(trace).toBeTruthy();
    expect(trace.correction_type).toBe("behavioral");
  });

  it("updates interaction state on messages", async () => {
    const hooks = createMessageHooks(() => manager);

    await hooks.onMessageReceived({
      message: "Wrong! I already told you, không phải vậy.",
      previousAssistantMessage: "Here is the result.",
      sessionKey: "s2",
    });

    const db = manager.getDb();
    const state = db.prepare(
      "SELECT * FROM interaction_states WHERE session_id = 's2'",
    ).get() as any;

    expect(state).toBeTruthy();
    expect(state.correction_pressure).toBeGreaterThan(0);
    expect(state.frustration_index).toBeGreaterThan(0);
  });

  it("handles short messages with brevity signal", async () => {
    const hooks = createMessageHooks(() => manager);

    await hooks.onMessageReceived({
      message: "ok",
      sessionKey: "s3",
    });

    const db = manager.getDb();
    const state = db.prepare(
      "SELECT * FROM interaction_states WHERE session_id = 's3'",
    ).get() as any;

    expect(state).toBeTruthy();
    // Short message = high brevity preference signal
    expect(state.brevity_preference).toBeGreaterThan(0);
  });

  it("does not record correction without previous message", async () => {
    const hooks = createMessageHooks(() => manager);

    await hooks.onMessageReceived({
      message: "No that's wrong",
      sessionKey: "s4",
    });

    const db = manager.getDb();
    const traces = db.prepare("SELECT COUNT(*) as c FROM correction_traces").get() as any;
    // Should NOT record correction when there's no previous message
    expect(traces.c).toBe(0);
  });

  it("does nothing when manager is null", async () => {
    const hooks = createMessageHooks(() => null);
    await expect(
      hooks.onMessageReceived({ message: "test", sessionKey: "x" }),
    ).resolves.toBeUndefined();
  });
});

// --- Manager maintenance ---

describe("AegisMemoryManager.runMaintenance", () => {
  it("runs full maintenance cycle", async () => {
    const db = manager.getDb();
    const now = nowISO();
    const past = new Date(Date.now() - 1000).toISOString();

    // Create expired TTL node
    db.prepare(`
      INSERT INTO memory_nodes (id, memory_type, content, status, memory_state, ttl_expires_at, salience, created_at, updated_at)
      VALUES ('maint-ttl', 'working_scratch', 'expired', 'active', 'volatile', ?, 0.5, ?, ?)
    `).run(past, now, now);

    const report = await manager.runMaintenance();

    expect(report.ttlExpired).toBeGreaterThanOrEqual(1);

    const node = db.prepare("SELECT status FROM memory_nodes WHERE id = 'maint-ttl'").get() as any;
    expect(node.status).toBe("expired");
  });

  it("returns a valid maintenance report", async () => {
    const report = await manager.runMaintenance();
    expect(report).toHaveProperty("stateTransitions");
    expect(report).toHaveProperty("archived");
    expect(report).toHaveProperty("ttlExpired");
    expect(report).toHaveProperty("staleEdgesPruned");
    expect(report).toHaveProperty("ftsOptimized");
  });
});

// --- getDb ---

describe("AegisMemoryManager.getDb", () => {
  it("returns a working database handle", () => {
    const db = manager.getDb();
    const row = db.prepare("SELECT 1 + 1 as r").get() as any;
    expect(row.r).toBe(2);
  });
});
