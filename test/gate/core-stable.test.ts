/**
 * Phase 0 Gate Test — aegis-core-stable
 *
 * Bộ gate bắt buộc trước khi release. Chạy tất cả benchmark với ngưỡng tối thiểu.
 * Nếu bất kỳ metric nào dưới ngưỡng → FAIL → không release.
 *
 * Metrics thresholds:
 * - Hit@5 >= 70%
 * - Recall@5 >= 40%
 * - MRR@10 >= 0.4
 * - ScopeLeakRate@5 <= 20%
 * - ConflictLeakRate@10 <= 10%
 * - Latency p95 <= 500ms
 * - Bowerbird classification rate >= 80%
 * - Meerkat scan does not crash
 * - Eagle report generates successfully
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { AegisMemoryManager, closeAllManagers } from "../../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import { resolve } from "node:path";
import {
  seedGroundTruthData,
  seedExtendedData,
  GROUND_TRUTH,
  EXTENDED_GROUND_TRUTH,
  runQuery,
  summarize,
  printReport,
  type BenchSummary,
} from "../helpers/aegis-bench.js";
import { BowerbirdTaxonomist } from "../../src/cognitive/bowerbird.js";
import { MeerkatSentry } from "../../src/cognitive/meerkat.js";
import { EagleEye } from "../../src/cognitive/eagle.js";
import { DragonflySentry } from "../../src/retrieval/dragonfly.js";
import { WeaverBird } from "../../src/cognitive/weaver-bird.js";
import { ChameleonBudgeter, ZONE_POLICIES } from "../../src/cognitive/chameleon.js";
import { newId } from "../../src/core/id.js";

describe("Phase 0 Gate: aegis-core-stable", () => {
  let manager: AegisMemoryManager;
  const workspaceDir = resolve(process.cwd(), ".tmp_gate_test");
  let benchSummary: BenchSummary;

  beforeAll(async () => {
    manager = await AegisMemoryManager.create({
      agentId: "gate_test",
      workspaceDir,
      config: {
        ...DEFAULT_AEGIS_CONFIG,
        enabledLayers: [
          "elephant", "orca", "dolphin", "salmon",
          "bowerbird", "meerkat", "zebra-finch", "eagle",
          "scrub-jay", "dragonfly", "weaver-bird", "chameleon",
        ],
      },
    });

    const db = manager.getDb();
    // Clean slate
    db.prepare("DELETE FROM archive_log").run();
    db.prepare("DELETE FROM interaction_states").run();
    db.prepare("DELETE FROM tool_artifacts").run();
    db.prepare("DELETE FROM procedure_steps").run();
    db.prepare("DELETE FROM procedures").run();
    db.prepare("DELETE FROM drift_events").run();
    db.prepare("DELETE FROM entity_aliases").run();
    db.prepare("DELETE FROM entities").run();
    db.prepare("DELETE FROM dedup_routes").run();
    db.prepare("DELETE FROM memory_events").run();
    db.prepare("DELETE FROM fingerprints").run();
    db.prepare("DELETE FROM memory_edges").run();
    db.prepare("DELETE FROM memory_nodes").run();
    db.prepare("DELETE FROM episodes").run();

    // Seed benchmark data
    const baseIds = seedGroundTruthData(db);
    const allIds = seedExtendedData(db, baseIds);

    // Run all benchmark queries
    const allQueries = [...GROUND_TRUTH, ...EXTENDED_GROUND_TRUTH];
    const results = await Promise.all(
      allQueries.map((item) => runQuery(db, item, allIds, DEFAULT_AEGIS_CONFIG)),
    );

    benchSummary = summarize(results);
    printReport(benchSummary, "PHASE 0 GATE — aegis-core-stable");
  });

  afterAll(async () => {
    await closeAllManagers();
  });

  // ========== Retrieval Quality ==========

  it("Hit@5 >= 70%", () => {
    expect(benchSummary["Hit@5"]).toBeGreaterThanOrEqual(0.7);
  });

  it("Recall@5 >= 40%", () => {
    expect(benchSummary["Recall@5"]).toBeGreaterThanOrEqual(0.4);
  });

  it("MRR@10 >= 0.4", () => {
    expect(benchSummary["MRR@10"]).toBeGreaterThanOrEqual(0.4);
  });

  it("ScopeLeakRate@5 <= 20%", () => {
    expect(benchSummary["ScopeLeakRate@5"]).toBeLessThanOrEqual(0.2);
  });

  it("ConflictLeakRate@10 <= 10%", () => {
    expect(benchSummary["ConflictLeakRate@10"]).toBeLessThanOrEqual(0.1);
  });

  it("Latency p95 <= 500ms", () => {
    expect(benchSummary.LatencyP95Ms).toBeLessThanOrEqual(500);
  });

  // ========== Bowerbird Taxonomy ==========

  it("Bowerbird classifies >= 80% of active nodes", () => {
    const db = manager.getDb();
    const bird = new BowerbirdTaxonomist(db);

    // First clear any existing subjects to test fresh classification
    db.prepare("UPDATE memory_nodes SET canonical_subject = NULL WHERE status = 'active'").run();

    const classified = bird.classifyAllUnknownNodes();
    const total = (db.prepare("SELECT count(*) as c FROM memory_nodes WHERE status = 'active'").get() as any).c;

    const rate = total > 0 ? classified / total : 0;
    expect(rate).toBeGreaterThanOrEqual(0.8);
  });

  it("Bowerbird confidence scores are valid (0-1)", () => {
    const db = manager.getDb();
    const invalid = db.prepare(`
      SELECT count(*) as c FROM memory_nodes
      WHERE taxonomy_confidence IS NOT NULL
        AND (taxonomy_confidence < 0 OR taxonomy_confidence > 1)
    `).get() as any;
    expect(invalid.c).toBe(0);
  });

  it("Bowerbird has no stray labels", () => {
    const db = manager.getDb();
    const bird = new BowerbirdTaxonomist(db);
    const stray = bird.findStrayLabels();
    expect(stray.length).toBe(0);
  });

  // ========== Meerkat Conflict Detection ==========

  it("Meerkat scan runs without crash", async () => {
    const conflicts = await manager.runMeerkatScan();
    expect(Array.isArray(conflicts)).toBe(true);
  });

  // ========== Eagle Observability ==========

  it("Eagle summary generates successfully", () => {
    const db = manager.getDb();
    const eagle = new EagleEye(db);
    const summary = eagle.summarize();
    expect(summary).toBeDefined();
    expect(summary.healthScore).toBeGreaterThanOrEqual(0);
    expect(summary.healthScore).toBeLessThanOrEqual(100);
  });

  it("Eagle report renders without error", () => {
    const db = manager.getDb();
    const eagle = new EagleEye(db);
    const summary = eagle.summarize();
    const text = eagle.renderSummary(summary);
    expect(text.length).toBeGreaterThan(50);
  });

  // ========== Dragonfly Rescue ==========

  it("Dragonfly shouldRescue returns false for strong FTS hits", () => {
    const strongResults = [{ nodeId: "a", score: 0.8, content: "", memoryType: "", scope: "" }];
    expect(DragonflySentry.shouldRescue(strongResults)).toBe(false);
  });

  it("Dragonfly shouldRescue returns true for empty results", () => {
    expect(DragonflySentry.shouldRescue([])).toBe(true);
  });

  it("Dragonfly shouldRescue returns true for weak FTS hits", () => {
    const weakResults = [{ nodeId: "a", score: 0.1, content: "", memoryType: "", scope: "" }];
    expect(DragonflySentry.shouldRescue(weakResults)).toBe(true);
  });

  // ========== Weaver Bird Procedural ==========

  it("Weaver Bird extracts null for single-tool sequences (fact, not procedure)", () => {
    const messages = [
      { role: "assistant", content: [{ type: "tool_use", name: "read_file", input: {} }] },
    ];
    const result = WeaverBird.extractProceduralBlueprint(messages, "Read a file");
    expect(result).toBeNull();
  });

  it("Weaver Bird extracts blueprint for multi-tool sequences", () => {
    const messages = [
      { role: "assistant", content: [{ type: "tool_use", name: "read_file", input: {} }] },
      { role: "assistant", content: [{ type: "tool_use", name: "edit_file", input: {} }] },
      { role: "assistant", content: [{ type: "tool_use", name: "run_command", input: {} }] },
    ];
    const result = WeaverBird.extractProceduralBlueprint(messages, "Fix a bug");
    expect(result).not.toBeNull();
    expect(result).toContain("read_file");
    expect(result).toContain("edit_file");
  });

  // ========== Chameleon Context Budgeting ==========

  it("Chameleon respects topK limit", () => {
    const results = Array.from({ length: 10 }, (_, i) => ({
      path: `aegis://test/${i}`,
      startLine: 0, endLine: 0,
      score: 0.5, snippet: `Content ${i}`,
      source: "memory" as const,
      citation: "knowledge.fact",
    }));

    const output = ChameleonBudgeter.assemble(results, {
      maxChars: 5000, topK: 3,
    });

    // Count entries in output
    const matches = output.match(/\[\d+\.\d+\]/g) || [];
    expect(matches.length).toBeLessThanOrEqual(3);
  });

  it("Chameleon never drops zone 0 (trauma/invariant)", () => {
    const results = [
      { path: "aegis://trauma/1", startLine: 0, endLine: 0, score: 0.3, snippet: "Critical safety rule", source: "memory" as const, citation: "[trauma] policy.safety" },
      ...Array.from({ length: 5 }, (_, i) => ({
        path: `aegis://task/${i}`, startLine: 0, endLine: 0,
        score: 0.9, snippet: `High-score task memory ${i}`,
        source: "memory" as const, citation: "knowledge.fact",
      })),
    ];

    const output = ChameleonBudgeter.assemble(results, {
      maxChars: 1000, topK: 3,
    });

    expect(output).toContain("[trauma]");
    expect(output).toContain("core-directives");
  });

  it("Chameleon zone policies exist for all presets", () => {
    expect(ZONE_POLICIES["minimal"]).toBeDefined();
    expect(ZONE_POLICIES["balanced"]).toBeDefined();
    expect(ZONE_POLICIES["local-safe"]).toBeDefined();
    expect(ZONE_POLICIES["max-memory"]).toBeDefined();
  });
});
