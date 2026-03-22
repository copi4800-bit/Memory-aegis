/**
 * Diagnostic Test: Latency Profile & Index Analysis
 *
 * Purpose: Profile per-stage latency and check index coverage for the
 * spreading activation bottleneck identified in Phase 3 (p95=149ms @ 1600 nodes).
 *
 * Covers:
 *   1. Index inventory — what indexes exist on memory_edges and memory_nodes
 *   2. EXPLAIN QUERY PLAN — spreading activation out-edges and in-edges queries
 *   3. Per-stage latency breakdown: FTS / entity / activation / rerank
 *   4. Full benchmark latency profile: all 10 queries with per-stage timings
 *   5. Scaling probe: add 300 extra nodes, re-measure p95
 *
 * Indexes to check (correct column names):
 *   - idx_edges_src     ON memory_edges(src_node_id)
 *   - idx_edges_dst     ON memory_edges(dst_node_id)
 *   - idx_nodes_status  ON memory_nodes(status)
 *   - idx_nodes_scope   ON memory_nodes(scope)
 *   - idx_nodes_ttl     ON memory_nodes(ttl_expires_at)
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

import { openDatabase } from "../../src/db/connection.js";
import type { AegisDatabase } from "../../src/db/connection.js";
import { fts5Search, findEntityMatches } from "../../src/retrieval/fts-search.js";
import { assignInitialActivation, spreadingActivation } from "../../src/retrieval/graph-walk.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { DEFAULT_AEGIS_CONFIG, CONSTANTS } from "../../src/core/models.js";
import { ingestChunk } from "../../src/core/ingest.js";
import {
  seedGroundTruthData,
  GROUND_TRUTH,
  runQuery,
  percentile,
  summarize,
  printReport,
} from "../helpers/aegis-bench.js";

// ============================================================
// Setup
// ============================================================

let dbHandle: AegisDatabase;
let dbPath: string;
let seedIds: Record<string, string>;

const config = {
  ...DEFAULT_AEGIS_CONFIG,
  enabledLayers: ["elephant", "orca", "salmon", "sea-lion"] as typeof DEFAULT_AEGIS_CONFIG.enabledLayers,
  retrievalMaxHops: 4,
  dampingFactor: 0.5,
  maxNodesPerSearch: 50,
};

beforeAll(() => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-latency-"));
  dbPath = path.join(tmpDir, "latency.db");
  dbHandle = openDatabase(dbPath);
  seedIds = seedGroundTruthData(dbHandle.db);
});

afterAll(() => {
  dbHandle.close();
  try { fs.rmSync(path.dirname(dbPath), { recursive: true }); } catch {}
});

// ============================================================
// 1. Index Inventory
// ============================================================

describe("1 — Index inventory", () => {
  it("lists all indexes on memory_edges", () => {
    const db = dbHandle.db;
    const indexes = db.prepare("PRAGMA index_list('memory_edges')").all() as Array<{
      seq: number; name: string; unique: number; origin: string; partial: number;
    }>;

    console.log("\n━━━ Indexes on memory_edges ━━━");
    if (indexes.length === 0) {
      console.log("  ⚠ NO indexes on memory_edges!");
      console.log("  → Spreading activation (Orca) does full table scans — this is the bottleneck");
    } else {
      for (const idx of indexes) {
        const info = db.prepare(`PRAGMA index_info('${idx.name}')`).all() as Array<{
          seqno: number; cid: number; name: string;
        }>;
        const cols = info.map((c) => c.name).join(", ");
        console.log(`  ${idx.name}  cols=[${cols}]  unique=${idx.unique}`);
      }
    }

    // Document what we found
    const hasEdgeSrcIndex = indexes.some((idx) => {
      const info = db.prepare(`PRAGMA index_info('${idx.name}')`).all() as Array<{ name: string }>;
      return info.some((c) => c.name === "src_node_id");
    });
    const hasEdgeDstIndex = indexes.some((idx) => {
      const info = db.prepare(`PRAGMA index_info('${idx.name}')`).all() as Array<{ name: string }>;
      return info.some((c) => c.name === "dst_node_id");
    });

    console.log(`\n  src_node_id indexed: ${hasEdgeSrcIndex ? "YES ✓" : "NO ✗ (needs idx_edges_src)"}`);
    console.log(`  dst_node_id indexed: ${hasEdgeDstIndex ? "YES ✓" : "NO ✗ (needs idx_edges_dst)"}`);

    expect(Array.isArray(indexes)).toBe(true);
  });

  it("lists all indexes on memory_nodes", () => {
    const db = dbHandle.db;
    const indexes = db.prepare("PRAGMA index_list('memory_nodes')").all() as Array<{
      seq: number; name: string; unique: number; origin: string; partial: number;
    }>;

    console.log("\n━━━ Indexes on memory_nodes ━━━");
    for (const idx of indexes) {
      const info = db.prepare(`PRAGMA index_info('${idx.name}')`).all() as Array<{
        seqno: number; cid: number; name: string;
      }>;
      const cols = info.map((c) => c.name).join(", ");
      console.log(`  ${idx.name}  cols=[${cols}]  unique=${idx.unique}`);
    }

    // Check for the indexes we want to add
    const allIndexCols = new Set<string>();
    for (const idx of indexes) {
      const info = db.prepare(`PRAGMA index_info('${idx.name}')`).all() as Array<{ name: string }>;
      for (const c of info) allIndexCols.add(c.name);
    }

    const wanted = ["status", "scope", "memory_type", "ttl_expires_at"];
    for (const col of wanted) {
      console.log(`  ${col} indexed: ${allIndexCols.has(col) ? "YES ✓" : "NO ✗"}`);
    }

    expect(Array.isArray(indexes)).toBe(true);
  });
});

// ============================================================
// 2. EXPLAIN QUERY PLAN — Spreading Activation
// ============================================================

describe("2 — EXPLAIN QUERY PLAN: spreading activation", () => {
  it("shows query plan for out-edges scan (src_node_id lookup)", () => {
    const db = dbHandle.db;

    const plan = db.prepare(`
      EXPLAIN QUERY PLAN
      SELECT dst_node_id as neighborId, edge_type, weight, confidence, scope
      FROM memory_edges
      WHERE src_node_id = ? AND status = 'active'
    `).all("dummy-id") as Array<{ id: number; parent: number; notused: number; detail: string }>;

    console.log("\n━━━ EXPLAIN QUERY PLAN: out-edges (src_node_id = ?) ━━━");
    for (const row of plan) {
      console.log(`  ${row.detail}`);
    }

    const usesIndex = plan.some((r) => r.detail.toLowerCase().includes("index"));
    const usesScan = plan.some((r) => r.detail.toLowerCase().includes("scan"));

    console.log(`\n  Uses index : ${usesIndex ? "YES ✓" : "NO"}`);
    console.log(`  Full scan  : ${usesScan ? "YES ✗ (bottleneck!)" : "NO ✓"}`);

    if (!usesIndex) {
      console.warn("  ⚠ No index on src_node_id — add: CREATE INDEX idx_edges_src ON memory_edges(src_node_id)");
    }

    expect(Array.isArray(plan)).toBe(true);
  });

  it("shows query plan for in-edges scan (dst_node_id lookup)", () => {
    const db = dbHandle.db;

    const plan = db.prepare(`
      EXPLAIN QUERY PLAN
      SELECT src_node_id as neighborId, edge_type, weight, confidence, scope
      FROM memory_edges
      WHERE dst_node_id = ? AND status = 'active'
    `).all("dummy-id") as Array<{ id: number; parent: number; notused: number; detail: string }>;

    console.log("\n━━━ EXPLAIN QUERY PLAN: in-edges (dst_node_id = ?) ━━━");
    for (const row of plan) {
      console.log(`  ${row.detail}`);
    }

    const usesIndex = plan.some((r) => r.detail.toLowerCase().includes("index"));
    console.log(`  Uses index: ${usesIndex ? "YES ✓" : "NO ✗ (add idx_edges_dst)"}`);

    expect(Array.isArray(plan)).toBe(true);
  });

  it("shows query plan for memory_nodes status filter (reranker stage)", () => {
    const db = dbHandle.db;

    const plan = db.prepare(`
      EXPLAIN QUERY PLAN
      SELECT * FROM memory_nodes WHERE id = ?
    `).all("dummy-id") as Array<{ detail: string }>;

    const planStatus = db.prepare(`
      EXPLAIN QUERY PLAN
      SELECT * FROM memory_nodes WHERE status = 'active' AND scope = ?
    `).all("user") as Array<{ detail: string }>;

    console.log("\n━━━ EXPLAIN QUERY PLAN: memory_nodes by id ━━━");
    for (const row of plan) console.log(`  ${row.detail}`);

    console.log("\n━━━ EXPLAIN QUERY PLAN: memory_nodes by status+scope ━━━");
    for (const row of planStatus) console.log(`  ${row.detail}`);

    expect(Array.isArray(plan)).toBe(true);
  });
});

// ============================================================
// 3. Per-Stage Latency Breakdown
// ============================================================

describe("3 — Per-stage latency breakdown", () => {
  it("measures FTS / entity / activation / rerank timing separately", async () => {
    const db = dbHandle.db;
    const REPS = 5;

    // Use q_mlt_01 (the problematic query) for stage-level timing
    const query = "JWT token expiry 24 hours authentication";

    const timings = {
      fts: [] as number[],
      entity: [] as number[],
      activation: [] as number[],
      rerank: [] as number[],
      total: [] as number[],
    };

    for (let i = 0; i < REPS; i++) {
      // Stage 1: FTS
      let t0 = performance.now();
      const ftsResults = fts5Search(db, query);
      timings.fts.push(performance.now() - t0);

      // Stage 2: Entity
      t0 = performance.now();
      const entityHits = findEntityMatches(db, query);
      timings.entity.push(performance.now() - t0);

      // Stage 3: Seeds + Activation
      const seeds = assignInitialActivation(ftsResults, entityHits);
      t0 = performance.now();
      if (seeds.size > 0) {
        spreadingActivation(seeds, db, {
          maxHops: config.retrievalMaxHops,
          dampingFactor: config.dampingFactor,
          activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
          maxNodes: config.maxNodesPerSearch,
          scopeFilter: undefined,
        });
      }
      timings.activation.push(performance.now() - t0);

      // Total pipeline (includes rerank+packet)
      t0 = performance.now();
      await executeRetrievalPipeline(db, query, config, { maxResults: 10 });
      const total = performance.now() - t0;
      timings.total.push(total);

      // Rerank = total - (fts + entity + activation) approximately
      timings.rerank.push(Math.max(0, total - timings.fts[i] - timings.entity[i] - timings.activation[i]));
    }

    const mean = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
    const p95 = (arr: number[]) => percentile([...arr].sort((a, b) => a - b), 95);

    console.log("\n━━━ Per-stage latency breakdown (5 reps) ━━━");
    console.log(`  Query: "${query}"`);
    console.log(`  ${"Stage".padEnd(12)} ${"mean(ms)".padStart(10)} ${"p95(ms)".padStart(10)}`);
    console.log("  " + "─".repeat(36));
    for (const [stage, vals] of Object.entries(timings)) {
      console.log(`  ${stage.padEnd(12)} ${mean(vals).toFixed(2).padStart(10)} ${p95(vals).toFixed(2).padStart(10)}`);
    }

    const activationFrac = mean(timings.activation) / mean(timings.total);
    const ftsFrac = mean(timings.fts) / mean(timings.total);
    console.log(`\n  FTS % of total      : ${(ftsFrac * 100).toFixed(1)}%`);
    console.log(`  Activation % of total: ${(activationFrac * 100).toFixed(1)}%`);

    if (activationFrac > 0.5) {
      console.warn("  ⚠ Spreading activation dominates latency — index src/dst_node_id");
    } else if (ftsFrac > 0.5) {
      console.warn("  ⚠ FTS5 dominates latency — PRAGMA optimize or rebuild fts index");
    } else {
      console.log("  → Latency is balanced — no single stage dominates");
    }

    expect(mean(timings.total)).toBeGreaterThanOrEqual(0);
  });
});

// ============================================================
// 4. Full Benchmark Latency Profile
// ============================================================

describe("4 — Full benchmark latency profile (10 queries × 3 reps)", () => {
  it("measures latency per query and reports p50/p95", async () => {
    const db = dbHandle.db;
    const REPS = 3;

    console.log("\n━━━ Per-query latency profile (3 reps) ━━━");
    console.log(`  ${"queryId".padEnd(14)} ${"mean(ms)".padStart(10)} ${"p95(ms)".padStart(10)} ${"group".padEnd(12)} ftsMs  actMs`);
    console.log("  " + "─".repeat(60));

    const allLatencies: number[] = [];

    for (const gt of GROUND_TRUTH) {
      const repLatencies: number[] = [];
      const repFts: number[] = [];
      const repAct: number[] = [];

      for (let i = 0; i < REPS; i++) {
        // Sub-stage timing
        let t0 = performance.now();
        const ftsResults = fts5Search(db, gt.query);
        const ftsMs = performance.now() - t0;

        const entityHits = findEntityMatches(db, gt.query);
        const seeds = assignInitialActivation(ftsResults, entityHits);

        t0 = performance.now();
        if (seeds.size > 0) {
          spreadingActivation(seeds, db, {
            maxHops: config.retrievalMaxHops,
            dampingFactor: config.dampingFactor,
            activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
            maxNodes: config.maxNodesPerSearch,
            scopeFilter: undefined,
          });
        }
        const actMs = performance.now() - t0;

        // Full pipeline
        t0 = performance.now();
        await executeRetrievalPipeline(db, gt.query, config, { maxResults: 10 });
        const totalMs = performance.now() - t0;

        repLatencies.push(totalMs);
        repFts.push(ftsMs);
        repAct.push(actMs);
        allLatencies.push(totalMs);
      }

      const mean = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
      const meanTotal = mean(repLatencies);
      const p95Total = percentile([...repLatencies].sort((a, b) => a - b), 95);

      console.log(
        `  ${gt.queryId.padEnd(14)} ${meanTotal.toFixed(2).padStart(10)} ${p95Total.toFixed(2).padStart(10)} ` +
        `${gt.group.padEnd(12)} ${mean(repFts).toFixed(1).padStart(5)} ${mean(repAct).toFixed(1).padStart(5)}`
      );
    }

    const sortedAll = [...allLatencies].sort((a, b) => a - b);
    console.log(`\n  Overall p50: ${percentile(sortedAll, 50).toFixed(2)}ms`);
    console.log(`  Overall p95: ${percentile(sortedAll, 95).toFixed(2)}ms`);
    console.log(`  Overall p99: ${percentile(sortedAll, 99).toFixed(2)}ms`);
    console.log(`  Overall mean: ${(allLatencies.reduce((a, b) => a + b, 0) / allLatencies.length).toFixed(2)}ms`);

    expect(allLatencies.length).toBe(GROUND_TRUTH.length * REPS);
  });
});

// ============================================================
// 5. Scaling probe — add 300 extra nodes, re-measure p95
// ============================================================

describe("5 — Scaling probe: 300 extra nodes", () => {
  it("inserts 300 noise nodes and measures latency degradation", async () => {
    const db = dbHandle.db;
    const EXTRA_NODES = 300;
    const REPS = 3;
    const PROBE_QUERY = "StarProject database PostgreSQL"; // q_leak_01

    // Baseline (seed data only, ~14 nodes)
    const baselineLatencies: number[] = [];
    for (let i = 0; i < REPS; i++) {
      const t0 = performance.now();
      await executeRetrievalPipeline(db, PROBE_QUERY, config, { maxResults: 10 });
      baselineLatencies.push(performance.now() - t0);
    }
    const baselineP95 = percentile([...baselineLatencies].sort((a, b) => a - b), 95);

    // Insert noise nodes
    const batchSize = 50;
    let inserted = 0;
    while (inserted < EXTRA_NODES) {
      const batch = Math.min(batchSize, EXTRA_NODES - inserted);
      for (let j = 0; j < batch; j++) {
        const n = inserted + j;
        ingestChunk(db, {
          sourcePath: `noise/scale-probe-${n}.md`,
          content: `Scale probe node ${n}. Random content about software development and system architecture patterns.`,
          source: "memory",
          scope: "user",
        });
      }
      inserted += batch;
    }

    const countAfter = db.prepare("SELECT COUNT(*) as n FROM memory_nodes WHERE status = 'active'")
      .get() as { n: number };

    // After scaling
    const scaledLatencies: number[] = [];
    for (let i = 0; i < REPS; i++) {
      const t0 = performance.now();
      await executeRetrievalPipeline(db, PROBE_QUERY, config, { maxResults: 10 });
      scaledLatencies.push(performance.now() - t0);
    }
    const scaledP95 = percentile([...scaledLatencies].sort((a, b) => a - b), 95);

    const ratio = scaledP95 / Math.max(baselineP95, 0.1);

    console.log("\n━━━ Scaling probe: latency vs node count ━━━");
    console.log(`  Baseline (~14 nodes): p95=${baselineP95.toFixed(2)}ms`);
    console.log(`  After +${EXTRA_NODES} nodes (total active=${countAfter.n}): p95=${scaledP95.toFixed(2)}ms`);
    console.log(`  Degradation ratio: ${ratio.toFixed(2)}x`);

    if (ratio > 10) {
      console.warn("  ⚠ Severe degradation (>10x) — full table scan in spreading activation");
      console.warn("  → Add: CREATE INDEX idx_edges_src_dst ON memory_edges(src_node_id, dst_node_id)");
    } else if (ratio > 3) {
      console.warn(`  ⚠ Moderate degradation (${ratio.toFixed(1)}x) — indexes would help`);
    } else {
      console.log(`  → Degradation within acceptable range (${ratio.toFixed(1)}x) for this node count`);
    }

    // Staged degradation expectation — at 300 extra nodes the ratio should not exceed 30x
    expect(ratio).toBeLessThan(30);
  });

  it("re-runs full benchmark on scaled DB and compares p95 with phase-3 baseline", async () => {
    const db = dbHandle.db;

    const activeCount = (db.prepare("SELECT COUNT(*) as n FROM memory_nodes WHERE status = 'active'")
      .get() as { n: number }).n;

    console.log(`\n━━━ Full benchmark on scaled DB (${activeCount} active nodes) ━━━`);

    const results = await Promise.all(GROUND_TRUTH.map((gt) => runQuery(db, gt, seedIds, config, 10)));
    const summary = summarize(results);
    printReport(summary, `AEGIS-BENCH (scaled DB, ${activeCount} nodes)`);

    const p95 = summary.LatencyP95Ms;
    console.log(`\n  p95 baseline (Phase 3, 1600 nodes): 149ms`);
    console.log(`  p95 current  (${activeCount} nodes)      : ${p95.toFixed(1)}ms`);

    // At ~320 nodes (14 seed + 300 extra), p95 should be faster than Phase 3's 149ms
    // Phase 3 had ~1600 nodes — we have much fewer here
    if (activeCount < 1600) {
      console.log(`  → Fewer nodes than Phase 3 baseline, p95 should be lower`);
      if (p95 > 149) {
        console.warn("  ⚠ p95 higher than Phase 3 even with fewer nodes — index issue");
      }
    }

    expect(summary.queries).toBe(10);
    expect(p95).toBeGreaterThan(0);
  });
});

// ============================================================
// 6. SQLite PRAGMA state check
// ============================================================

describe("6 — SQLite PRAGMA state verification", () => {
  it("confirms current PRAGMA values match recommended settings", () => {
    const db = dbHandle.db;

    const pragmas = [
      "journal_mode",
      "synchronous",
      "cache_size",
      "busy_timeout",
      "foreign_keys",
      "page_size",
      "wal_autocheckpoint",
    ] as const;

    const recommended: Record<string, string | number> = {
      journal_mode: "wal",
      synchronous: 1,    // NORMAL
      cache_size: -64000,
      busy_timeout: 5000,
      foreign_keys: 1,
    };

    console.log("\n━━━ PRAGMA state ━━━");
    for (const p of pragmas) {
      const val = (db.pragma(p, { simple: true }) as string | number | undefined) ?? "N/A";
      const expected = recommended[p];
      const ok = expected === undefined || String(val) === String(expected);
      const tag = expected !== undefined ? (ok ? " ✓" : ` ✗ (want ${expected})`) : "";
      console.log(`  ${p.padEnd(22)}: ${val}${tag}`);
    }

    // Confirm WAL is active
    const journalMode = db.pragma("journal_mode", { simple: true }) as string;
    expect(journalMode).toBe("wal");

    // Confirm busy_timeout is set (non-zero)
    const busyTimeout = db.pragma("busy_timeout", { simple: true }) as number;
    expect(busyTimeout).toBeGreaterThan(0);
  });

  it("checks DB file size and WAL size", () => {
    const dbSize = fs.existsSync(dbPath) ? fs.statSync(dbPath).size : 0;
    const walPath = dbPath + "-wal";
    const walSize = fs.existsSync(walPath) ? fs.statSync(walPath).size : 0;

    console.log("\n━━━ DB file sizes ━━━");
    console.log(`  DB  : ${(dbSize / 1024).toFixed(1)} KB`);
    console.log(`  WAL : ${(walSize / 1024).toFixed(1)} KB`);
    console.log(`  Total: ${((dbSize + walSize) / 1024).toFixed(1)} KB`);

    expect(dbSize).toBeGreaterThan(0);
  });
});
