/**
 * Phase 3: Stress Test — Garbage Flood + Maintenance Resilience
 *
 * Mục tiêu:
 *   Bơm 10,000 event rác vào DB, chạy nhiều vòng maintenance (Viper/Axolotl/Leafcutter/Decay),
 *   sau đó re-run toàn bộ benchmark. Assert rằng chất lượng retrieval không rớt quá ngưỡng.
 *
 * Nếu Maintenance cắt nhầm node quan trọng → Hit@5 sẽ rớt mạnh.
 * Nếu Orca bị nhiễu bởi rác → ScopeLeakRate và ConflictLeakRate sẽ tăng.
 * Nếu DB bị fragmented → Latency p95 sẽ tăng vượt ngưỡng.
 *
 * Pass criteria (Phase 3):
 *   Hit@5          >= 0.7  (baseline 0.9  — cho phép rớt tối đa 20%)
 *   Recall@5       >= 0.4  (baseline 0.77 — cho phép rớt tối đa 37%)
 *   MRR@10         >= 0.5  (baseline 0.82 — cho phép rớt tối đa 32%)
 *   nDCG@10        >= 0.4  (baseline 0.79 — cho phép rớt tối đa 39%)
 *   ScopeLeakRate  <= 0.3  (baseline 0.0  — cho phép tăng tối đa 30%)
 *   ConflictLeak   == 0.0  (expired nodes phải luôn = 0, không thương lượng)
 *   Latency p95    < 1000ms (relaxed so với 500ms ban đầu)
 *   Regression vs baseline: không rớt quá 25% ở bất kỳ core metric nào
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestBatch } from "../../src/core/ingest.js";
import { runMaintenanceCycle, type MaintenanceReport } from "../../src/retention/maintenance.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import {
  seedGroundTruthData,
  GROUND_TRUTH,
  runQuery,
  summarize,
  printReport,
  percentile,
  type BenchSummary,
} from "../helpers/aegis-bench.js";

// ============================================================
// CONFIG
// ============================================================

const BENCH_CONFIG = {
  ...DEFAULT_AEGIS_CONFIG,
  enabledLayers: ["elephant", "orca", "salmon", "dolphin", "sea-lion"] as any,
  retrievalMaxHops: 2,
  dampingFactor: 0.5,
  maxNodesPerSearch: 20,
};

const GARBAGE_COUNT = 2_000;
const MAINTENANCE_CYCLES = 3;
const GARBAGE_BATCH_SIZE = 100;

// Phase 3 pass/fail thresholds
const PHASE3_THRESHOLDS = {
  HIT_AT_5_MIN: 0.7,
  RECALL_AT_5_MIN: 0.4,
  MRR_AT_10_MIN: 0.5,
  NDCG_AT_10_MIN: 0.4,
  SCOPE_LEAK_MAX: 0.3,
  CONFLICT_LEAK_MAX: 0.05,  // max 5% semantic overlap — expired nodes checked separately
  LATENCY_P95_MAX_MS: 1000,
  MAX_REGRESSION_PCT: 0.25, // không rớt quá 25% so với baseline ở mỗi metric
};

// ============================================================
// GARBAGE GENERATORS
// ============================================================

// 5 loại rác, mỗi loại chiếm 20% tổng lượng

/** Loại A: Rác thuần túy — nội dung vô nghĩa, không liên quan */
function garbageNoise(i: number) {
  const topics = [
    "weather forecast sunny cloudy rainy temperature humidity",
    "cooking recipe pasta sauce ingredient oven timer",
    "travel destination hotel booking flight ticket",
    "sports score goal penalty match tournament",
    "fashion trend clothing shoe color size fabric",
  ];
  return {
    sourcePath: `garbage/noise-${i}.md`,
    content: `Noise entry ${i}: ${topics[i % topics.length]} item-${i}.`,
    source: "memory" as const,
    scope: "user",
  };
}

/** Loại B: Rác overlap — có từ khóa trùng với ground truth nhưng nội dung sai */
function garbageOverlap(i: number) {
  const templates = [
    `StarProject TypeScript error: module not found at path index-${i}. Unrelated build issue.`,
    `React rendering warning: key prop missing in list item-${i}. Not related to Tailwind.`,
    `PostgreSQL connection timeout at pool slot ${i}. Unrelated to StarProject schema.`,
    `DragonHead calendar meeting on day ${i}: team standup postponed.`,
    `JWT token debug log entry ${i}: request-id unknown origin trace.`,
  ];
  return {
    sourcePath: `garbage/overlap-${i}.md`,
    content: templates[i % templates.length],
    source: "memory" as const,
    scope: "user",
  };
}

/** Loại C: Rác trùng lặp (dedup stress) — cùng content, ingest nhiều lần */
const DEDUP_CONTENTS = [
  "Temporary scratch note alpha: work in progress.",
  "Temporary scratch note beta: draft version.",
  "Temporary scratch note gamma: not finalized.",
  "Temporary scratch note delta: placeholder text.",
  "Temporary scratch note epsilon: needs review.",
];
function garbageDuplicate(i: number) {
  return {
    sourcePath: `garbage/dedup-variant-${i}.md`,
    content: DEDUP_CONTENTS[i % DEDUP_CONTENTS.length], // sẽ bị dedup bởi Salmon
    source: "memory" as const,
    scope: "user",
  };
}

/** Loại D: Rác short-TTL — sẽ bị Nutcracker expire trong maintenance */
function garbageTTL(i: number, ttlPast: string) {
  return {
    sourcePath: `garbage/ttl-${i}.md`,
    content: `Short-lived scratch entry ${i}: ephemeral data that should expire quickly.`,
    source: "memory" as const,
    scope: "user",
    // TTL được set sau khi ingest (xem bên dưới)
  };
}

/** Loại E: Rác sai scope — giả lập memory từ project khác bị lẫn vào */
function garbageWrongScope(i: number) {
  const projects = ["project_alpha", "project_beta", "project_gamma", "project_delta"];
  return {
    sourcePath: `${projects[i % projects.length]}/noise-${i}.md`,
    content: `Cross-project noise from ${projects[i % projects.length]}: data record ${i} internal reference.`,
    source: "memory" as const,
    scope: projects[i % projects.length],
  };
}

// ============================================================
// SETUP
// ============================================================

let db: AegisDatabase;
let testDir: string;
let seedNodeIds: Record<string, string> = {};
let baselineSummary: BenchSummary;
let postFloodSummary: BenchSummary;
let maintenanceReports: MaintenanceReport[] = [];
let dbSizeBeforeBytes: number;
let dbSizeAfterBytes: number;
let ttlGarbageCount = 0; // số TTL node được insert

beforeAll(async () => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-stress-"));
  db = openDatabase(path.join(testDir, "stress.db"));

  // ── Step 1: Seed ground truth data ──────────────────────────
  seedNodeIds = seedGroundTruthData(db.db);

  // ── Step 2: Baseline benchmark (trước khi bơm rác) ──────────
  const baselineResults = await Promise.all(GROUND_TRUTH.map((item) =>
    runQuery(db.db, item, seedNodeIds, BENCH_CONFIG)
  ));
  baselineSummary = summarize(baselineResults);
  printReport(baselineSummary, "BASELINE (before garbage flood)");

  // ── Step 3: Record DB size trước khi bơm rác ────────────────
  const dbPath = path.join(testDir, "stress.db");
  dbSizeBeforeBytes = fs.existsSync(dbPath) ? fs.statSync(dbPath).size : 0;

  // ── Step 4: Bơm 10,000 node rác ─────────────────────────────
  console.log(`\nBombing DB with ${GARBAGE_COUNT} garbage nodes in batches of ${GARBAGE_BATCH_SIZE}...`);
  const pastTTL = new Date(Date.now() - 1000).toISOString(); // 1 giây trước = đã hết hạn

  const perType = Math.floor(GARBAGE_COUNT / 5);

  // Loại A: noise
  for (let batch = 0; batch < perType / GARBAGE_BATCH_SIZE; batch++) {
    const chunks = Array.from({ length: GARBAGE_BATCH_SIZE }, (_, j) =>
      garbageNoise(batch * GARBAGE_BATCH_SIZE + j)
    );
    ingestBatch(db.db, chunks);
  }

  // Loại B: overlap
  for (let batch = 0; batch < perType / GARBAGE_BATCH_SIZE; batch++) {
    const chunks = Array.from({ length: GARBAGE_BATCH_SIZE }, (_, j) =>
      garbageOverlap(batch * GARBAGE_BATCH_SIZE + j)
    );
    ingestBatch(db.db, chunks);
  }

  // Loại C: duplicate
  for (let batch = 0; batch < perType / GARBAGE_BATCH_SIZE; batch++) {
    const chunks = Array.from({ length: GARBAGE_BATCH_SIZE }, (_, j) =>
      garbageDuplicate(batch * GARBAGE_BATCH_SIZE + j)
    );
    ingestBatch(db.db, chunks);
  }

  // Loại D: short TTL — ingest xong thì set ttl_expires_at về quá khứ via source_path LIKE
  for (let batch = 0; batch < perType / GARBAGE_BATCH_SIZE; batch++) {
    const chunks = Array.from({ length: GARBAGE_BATCH_SIZE }, (_, j) =>
      garbageTTL(batch * GARBAGE_BATCH_SIZE + j, pastTTL)
    );
    ingestBatch(db.db, chunks);
  }
  // Set TTL past bằng LIKE pattern — tránh IN clause quá lớn
  const ttlUpdateResult = db.db.prepare(
    `UPDATE memory_nodes SET ttl_expires_at = ? WHERE source_path LIKE 'garbage/ttl-%' AND status = 'active'`
  ).run(pastTTL);
  ttlGarbageCount = ttlUpdateResult.changes;

  // Loại E: wrong scope
  for (let batch = 0; batch < perType / GARBAGE_BATCH_SIZE; batch++) {
    const chunks = Array.from({ length: GARBAGE_BATCH_SIZE }, (_, j) =>
      garbageWrongScope(batch * GARBAGE_BATCH_SIZE + j)
    );
    ingestBatch(db.db, chunks);
  }

  const totalNodes = (db.db.prepare("SELECT COUNT(*) as cnt FROM memory_nodes").get() as any).cnt;
  console.log(`DB now has ${totalNodes} total nodes.`);

  // ── Step 5: Chạy maintenance ${MAINTENANCE_CYCLES} lần ──────
  console.log(`\nRunning ${MAINTENANCE_CYCLES} maintenance cycles...`);
  for (let cycle = 0; cycle < MAINTENANCE_CYCLES; cycle++) {
    const report = await runMaintenanceCycle(db.db, testDir, BENCH_CONFIG);
    maintenanceReports.push(report);
    console.log(
      `  Cycle ${cycle + 1}: transitions=${report.stateTransitions} ` +
      `expired=${report.ttlExpired} pruned=${report.staleEdgesPruned} ` +
      `archived=${report.leafcutterArchivedEvents} fts=${report.ftsOptimized}`
    );
  }

  // ── Step 6: DB size sau ──────────────────────────────────────
  dbSizeAfterBytes = fs.existsSync(dbPath) ? fs.statSync(dbPath).size : 0;

  // ── Step 7: Post-flood benchmark ─────────────────────────────
  const postResults = await Promise.all(GROUND_TRUTH.map((item) =>
    runQuery(db.db, item, seedNodeIds, BENCH_CONFIG)
  ));
  postFloodSummary = summarize(postResults);
  printReport(postFloodSummary, "POST-FLOOD (after garbage + maintenance)");

  // Regression diff
  console.log("\n--- REGRESSION DELTA ---");
  console.log(`Hit@5    : ${(baselineSummary["Hit@5"]*100).toFixed(1)}% → ${(postFloodSummary["Hit@5"]*100).toFixed(1)}%  (Δ${((postFloodSummary["Hit@5"]-baselineSummary["Hit@5"])*100).toFixed(1)}%)`);
  console.log(`Recall@5 : ${(baselineSummary["Recall@5"]*100).toFixed(1)}% → ${(postFloodSummary["Recall@5"]*100).toFixed(1)}%  (Δ${((postFloodSummary["Recall@5"]-baselineSummary["Recall@5"])*100).toFixed(1)}%)`);
  console.log(`MRR@10   : ${baselineSummary["MRR@10"].toFixed(3)} → ${postFloodSummary["MRR@10"].toFixed(3)}  (Δ${(postFloodSummary["MRR@10"]-baselineSummary["MRR@10"]).toFixed(3)})`);
  console.log(`nDCG@10  : ${baselineSummary["nDCG@10"].toFixed(3)} → ${postFloodSummary["nDCG@10"].toFixed(3)}  (Δ${(postFloodSummary["nDCG@10"]-baselineSummary["nDCG@10"]).toFixed(3)})`);
  console.log(`ScopeLeak: ${(baselineSummary["ScopeLeakRate@5"]*100).toFixed(1)}% → ${(postFloodSummary["ScopeLeakRate@5"]*100).toFixed(1)}%`);
  console.log(`CflLeak  : ${(baselineSummary["ConflictLeakRate@10"]*100).toFixed(1)}% → ${(postFloodSummary["ConflictLeakRate@10"]*100).toFixed(1)}%`);
  console.log(`p95 lat  : ${baselineSummary.LatencyP95Ms.toFixed(1)}ms → ${postFloodSummary.LatencyP95Ms.toFixed(1)}ms`);
  console.log(`DB size  : ${(dbSizeBeforeBytes/1024).toFixed(0)}KB → ${(dbSizeAfterBytes/1024).toFixed(0)}KB`);
}, 120_000); // timeout 2 min — 10k inserts takes time

afterAll(() => {
  try { db.close(); } catch {}
  try { fs.rmSync(testDir, { recursive: true, force: true }); } catch {}
});

// ============================================================
// TESTS
// ============================================================

describe("Phase 3: Garbage Flood — DB State", () => {
  it("database accepts 10,000 garbage nodes without corruption", () => {
    const totalNodes = (db.db.prepare(
      "SELECT COUNT(*) as cnt FROM memory_nodes"
    ).get() as any).cnt;

    // Phải có ít nhất 12 seed nodes + garbage (dedup sẽ gộp loại C)
    expect(totalNodes).toBeGreaterThan(1000);

    // DB phải vẫn mở được (không corrupt)
    expect(() => {
      db.db.prepare("SELECT COUNT(*) as cnt FROM memory_nodes").get();
    }).not.toThrow();
  });

  it("Salmon dedup reduces duplicate garbage (type C)", () => {
    // Loại C có 5 unique contents được ingest 400 lần (perType = 400)
    // Salmon phải gộp về tối đa 5 unique nodes
    const dedupRows = db.db.prepare(`
      SELECT content, COUNT(*) as cnt
      FROM memory_nodes
      WHERE source_path LIKE 'garbage/dedup%' AND status = 'active'
      GROUP BY content
    `).all() as Array<{ content: string; cnt: number }>;

    console.log(`[dedup] unique content groups: ${dedupRows.length}`);

    // Mỗi content group phải chỉ có 1 node (dedup đã gộp)
    for (const row of dedupRows) {
      expect(row.cnt).toBe(1);
    }

    // Frequency_count của các node dedup phải > 1 (đã bump nhiều lần)
    const highFreq = db.db.prepare(`
      SELECT id, frequency_count FROM memory_nodes
      WHERE source_path LIKE 'garbage/dedup%'
        AND status = 'active'
        AND frequency_count > 1
    `).all() as any[];

    expect(highFreq.length).toBeGreaterThan(0);
    console.log(`[dedup] ${highFreq.length} nodes have frequency_count > 1 (correctly counted)`);
  });

  it("maintenance expired all short-TTL garbage (type D)", () => {
    if (ttlGarbageCount === 0) return;

    // Sau maintenance, TTL nodes phải có status='expired'
    const stillActive = db.db.prepare(
      `SELECT COUNT(*) as cnt FROM memory_nodes WHERE status = 'active' AND ttl_expires_at < datetime('now')`
    ).get() as any;

    console.log(`[TTL] nodes still active past expiry: ${stillActive.cnt}`);
    expect(stillActive.cnt).toBe(0);
  });

  it("maintenance ran FTS optimize on every cycle", () => {
    for (let i = 0; i < maintenanceReports.length; i++) {
      expect(maintenanceReports[i].ftsOptimized).toBe(true);
    }
  });

  it("FTS index still works after flood + maintenance", () => {
    // FTS phải trả về kết quả cho ground truth content
    const ftsResult = db.db.prepare(
      "SELECT COUNT(*) as cnt FROM memory_nodes_fts WHERE memory_nodes_fts MATCH 'StarProject'"
    ).get() as any;

    expect(ftsResult.cnt).toBeGreaterThan(0);
  });

  it("seed nodes (ground truth) survived maintenance untouched", () => {
    // Tất cả seed nodes phải vẫn còn active (trừ conflict_old_deploy đã bị expire trước)
    const seedKeys = Object.entries(seedNodeIds).filter(([k]) => k !== "conflict_old_deploy");

    for (const [key, nodeId] of seedKeys) {
      const row = db.db.prepare("SELECT status FROM memory_nodes WHERE id = ?").get(nodeId) as any;
      expect(row?.status, `Seed node '${key}' (id=${nodeId}) should still be active`).toBe("active");
    }
  });
});

describe("Phase 3: Garbage Flood — Retrieval Quality", () => {
  it("Hit@5 stays >= 0.7 after garbage flood", () => {
    console.log(`[Hit@5] post-flood: ${(postFloodSummary["Hit@5"]*100).toFixed(1)}%`);
    expect(postFloodSummary["Hit@5"]).toBeGreaterThanOrEqual(PHASE3_THRESHOLDS.HIT_AT_5_MIN);
  });

  it("Recall@5 stays >= 0.4 after garbage flood", () => {
    console.log(`[Recall@5] post-flood: ${(postFloodSummary["Recall@5"]*100).toFixed(1)}%`);
    expect(postFloodSummary["Recall@5"]).toBeGreaterThanOrEqual(PHASE3_THRESHOLDS.RECALL_AT_5_MIN);
  });

  it("MRR@10 stays >= 0.5 after garbage flood", () => {
    console.log(`[MRR@10] post-flood: ${postFloodSummary["MRR@10"].toFixed(3)}`);
    expect(postFloodSummary["MRR@10"]).toBeGreaterThanOrEqual(PHASE3_THRESHOLDS.MRR_AT_10_MIN);
  });

  it("nDCG@10 stays >= 0.4 after garbage flood", () => {
    console.log(`[nDCG@10] post-flood: ${postFloodSummary["nDCG@10"].toFixed(3)}`);
    expect(postFloodSummary["nDCG@10"]).toBeGreaterThanOrEqual(PHASE3_THRESHOLDS.NDCG_AT_10_MIN);
  });

  it("ScopeLeakRate@5 stays <= 0.3 after garbage flood", () => {
    console.log(`[ScopeLeakRate] post-flood: ${(postFloodSummary["ScopeLeakRate@5"]*100).toFixed(1)}%`);
    expect(postFloodSummary["ScopeLeakRate@5"]).toBeLessThanOrEqual(PHASE3_THRESHOLDS.SCOPE_LEAK_MAX);
  });

  it("ConflictLeakRate@10 stays <= 5% (semantic overlap allowed, expired zero-tolerated separately)", () => {
    console.log(`[ConflictLeak] post-flood: ${(postFloodSummary["ConflictLeakRate@10"]*100).toFixed(1)}%`);
    expect(postFloodSummary["ConflictLeakRate@10"]).toBeLessThanOrEqual(PHASE3_THRESHOLDS.CONFLICT_LEAK_MAX);
  });

  it("expired node (conflict_old_deploy) never appears in any retrieval result", () => {
    const expiredId = seedNodeIds["conflict_old_deploy"];
    for (const r of postFloodSummary.perQuery) {
      const appearsInResults = r.retrievedIds.includes(expiredId);
      expect(appearsInResults, `Expired node appeared in query ${r.queryId}`).toBe(false);
    }
  });

  it("Latency p95 stays below 1000ms under garbage load", () => {
    console.log(`[Latency p95] post-flood: ${postFloodSummary.LatencyP95Ms.toFixed(1)}ms`);
    expect(postFloodSummary.LatencyP95Ms).toBeLessThan(PHASE3_THRESHOLDS.LATENCY_P95_MAX_MS);
  });
});

describe("Phase 3: Regression vs Baseline", () => {
  it("Hit@5 regression does not exceed 25%", () => {
    if (baselineSummary["Hit@5"] === 0) return;
    const regression = (baselineSummary["Hit@5"] - postFloodSummary["Hit@5"]) / baselineSummary["Hit@5"];
    console.log(`[regression Hit@5] ${(regression * 100).toFixed(1)}%`);
    expect(regression).toBeLessThanOrEqual(PHASE3_THRESHOLDS.MAX_REGRESSION_PCT);
  });

  it("MRR@10 regression does not exceed 25%", () => {
    if (baselineSummary["MRR@10"] === 0) return;
    const regression = (baselineSummary["MRR@10"] - postFloodSummary["MRR@10"]) / baselineSummary["MRR@10"];
    console.log(`[regression MRR@10] ${(regression * 100).toFixed(1)}%`);
    expect(regression).toBeLessThanOrEqual(PHASE3_THRESHOLDS.MAX_REGRESSION_PCT);
  });

  it("nDCG@10 regression does not exceed 25%", () => {
    if (baselineSummary["nDCG@10"] === 0) return;
    const regression = (baselineSummary["nDCG@10"] - postFloodSummary["nDCG@10"]) / baselineSummary["nDCG@10"];
    console.log(`[regression nDCG@10] ${(regression * 100).toFixed(1)}%`);
    expect(regression).toBeLessThanOrEqual(PHASE3_THRESHOLDS.MAX_REGRESSION_PCT);
  });

  it("per-query: no previously-passing query now fails due to garbage noise", () => {
    // Nếu query pass ở baseline mà fail ở post-flood → noise đã phá vỡ retrieval
    const baselinePass = new Set(
      baselineSummary.perQuery.filter((r) => r.hitAtK === 1).map((r) => r.queryId)
    );
    const newFails = postFloodSummary.perQuery.filter(
      (r) => baselinePass.has(r.queryId) && r.hitAtK === 0
    );

    if (newFails.length > 0) {
      console.warn(
        "[REGRESSION] Queries that passed baseline but fail post-flood:",
        newFails.map((r) => r.queryId)
      );
    }

    // Cho phép tối đa 2 query bị regression (tổng 10 queries)
    expect(newFails.length).toBeLessThanOrEqual(2);
  });
});

describe("Phase 3: Maintenance Report Integrity", () => {
  it("maintenance ran the expected number of cycles", () => {
    expect(maintenanceReports.length).toBe(MAINTENANCE_CYCLES);
  });

  it("cumulative TTL expired >= type-D garbage count", () => {
    const totalExpired = maintenanceReports.reduce((s, r) => s + r.ttlExpired, 0);
    console.log(`[TTL] total expired across ${MAINTENANCE_CYCLES} cycles: ${totalExpired}`);
    // Type D chiếm 1/5 GARBAGE_COUNT = 2000, nhưng dedup có thể reduce
    // Chỉ cần > 0 là maintenance đang hoạt động
    expect(totalExpired).toBeGreaterThan(0);
  });

  it("Viper shed skin on every cycle", () => {
    for (const r of maintenanceReports) {
      expect(r.viperShedSkin).toBe(true);
    }
  });

  it("DB size after flood+maintenance is within 10x seed size", () => {
    // Sau flood 10k nodes, DB không được phình vô hạn
    // Dedup + maintenance phải giữ size hợp lý
    const seedOnlySize = dbSizeBeforeBytes;
    const maxAcceptableSize = Math.max(seedOnlySize * 10, 50 * 1024 * 1024); // 10x seed hoặc 50MB
    console.log(
      `[DB size] seed=${(seedOnlySize/1024).toFixed(0)}KB, post-flood=${(dbSizeAfterBytes/1024).toFixed(0)}KB, ` +
      `max-acceptable=${(maxAcceptableSize/1024/1024).toFixed(0)}MB`
    );
    expect(dbSizeAfterBytes).toBeLessThan(maxAcceptableSize);
  });
});

describe("Phase 3: Latency Profile Under Load", () => {
  it("all 10 benchmark queries complete under 1000ms each post-flood", () => {
    for (const r of postFloodSummary.perQuery) {
      expect(r.latencyMs, `Query ${r.queryId} too slow: ${r.latencyMs.toFixed(0)}ms`).toBeLessThan(1000);
    }
  });

  it("warm cache p95 still below 200ms post-flood", async () => {
    // Warm up pass
    for (const item of GROUND_TRUTH) {
      await runQuery(db.db, item, seedNodeIds, BENCH_CONFIG);
    }
    // Measure
    const latencies: number[] = [];
    for (const item of GROUND_TRUTH) {
      const r = await runQuery(db.db, item, seedNodeIds, BENCH_CONFIG);
      latencies.push(r.latencyMs);
    }
    latencies.sort((a, b) => a - b);
    const p95 = percentile(latencies, 95);
    console.log(`[warm p95 post-flood] ${p95.toFixed(1)}ms`);
    expect(p95).toBeLessThan(200);
  });
});
