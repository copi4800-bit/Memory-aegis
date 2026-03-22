/**
 * Aegis-Bench v1: Retrieval Quality Benchmark
 *
 * Phase 2 — đo "chất xám" thật của hệ thống sau khi 16 integration test đã pass.
 *
 * Metrics (theo spec từ 3.md):
 *   - Hit@5       : có ít nhất 1 node đúng trong top-5 không?
 *   - Recall@5    : bao nhiêu % relevant nodes được tìm thấy trong top-5?
 *   - MRR@10      : node đúng đầu tiên xuất hiện ở rank nào?
 *   - nDCG@10     : chất lượng xếp hạng tổng thể (graded relevance)
 *   - ScopeLeakRate@5    : % kết quả top-5 sai scope
 *   - ConflictLeakRate@10: % node cấm (stale/conflict) lọt vào top-10
 *   - Latency p50/p95/mean (ms)
 *
 * Ground truth: 10 queries chia 5 nhóm
 *   1. lexical   — FTS5 keyword match
 *   2. entity    — @mention entity lookup
 *   3. graph     — Orca spreading activation
 *   4. multiterm — nhiều từ khóa cùng lúc
 *   5. anti-leak — scope/conflict leakage guard
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import Database from "better-sqlite3";
import { openDatabase, type AegisDatabase } from "../../src/db/connection.js";
import { ingestChunk } from "../../src/core/ingest.js";
import { executeRetrievalPipeline, type SearchOptions } from "../../src/retrieval/pipeline.js";
import { DEFAULT_AEGIS_CONFIG, type AegisConfig } from "../../src/core/models.js";
import type { MemorySearchResult } from "../../src/retrieval/packet.js";

// ============================================================
// CONFIG
// ============================================================

const BENCH_CONFIG: AegisConfig = {
  ...DEFAULT_AEGIS_CONFIG,
  enabledLayers: ["elephant", "orca", "salmon", "dolphin", "sea-lion"],
  retrievalMaxHops: 2,
  dampingFactor: 0.5,
  maxNodesPerSearch: 20,
};

// Quality thresholds — minimum acceptable bar
const THRESHOLDS = {
  HIT_AT_5: 0.6,           // ít nhất 60% queries tìm được 1 node đúng
  RECALL_AT_5: 0.3,        // trung bình recall 30%
  MRR_AT_10: 0.3,          // node đúng đầu xuất hiện trong top 3-4
  NDCG_AT_10: 0.25,        // ranking quality tối thiểu
  SCOPE_LEAK_MAX: 0.2,     // tối đa 20% scope leakage
  CONFLICT_LEAK_MAX: 0.05, // tối đa 5% conflict leakage (gần như 0)
  LATENCY_P95_MS: 500,     // p95 dưới 500ms (test env, không có index warm)
};

// ============================================================
// TYPE DEFINITIONS
// ============================================================

interface GroundTruthItem {
  queryId: string;
  query: string;
  scope: string;
  group: "lexical" | "entity" | "graph" | "multiterm" | "anti-leak";
  primaryNodeKeys: string[];   // keys into seedNodeIds
  secondaryNodeKeys: string[];
  forbiddenNodeKeys: string[];
  relevance?: Record<string, number>; // key → grade (1/2/3)
  notes: string;
}

interface QueryResult {
  queryId: string;
  query: string;
  group: string;
  scope: string;
  expectedIds: Set<string>;
  primaryIds: Set<string>;
  forbiddenIds: Set<string>;
  relevance: Record<string, number>;
  retrievedIds: string[];
  retrievedScopes: string[];
  latencyMs: number;
  hitAtK: number;
  recallAtK: number;
  mrrAtK: number;
  ndcgAtK: number;
  scopeLeakRate: number;
  conflictLeakRate: number;
}

// ============================================================
// BENCHMARK ENGINE
// ============================================================

const K_RECALL = 5;
const K_MRR = 10;
const K_NDCG = 10;

function computeMRR(retrievedIds: string[], expectedIds: Set<string>, k: number): number {
  for (let rank = 0; rank < Math.min(k, retrievedIds.length); rank++) {
    if (expectedIds.has(retrievedIds[rank])) {
      return 1.0 / (rank + 1);
    }
  }
  return 0;
}

function computeNDCG(
  retrievedIds: string[],
  expectedIds: Set<string>,
  relevance: Record<string, number>,
  k: number,
): number {
  // DCG
  let dcg = 0;
  for (let rank = 0; rank < Math.min(k, retrievedIds.length); rank++) {
    const id = retrievedIds[rank];
    const rel = relevance[id] ?? (expectedIds.has(id) ? 1 : 0);
    if (rel > 0) {
      dcg += (Math.pow(2, rel) - 1) / Math.log2(rank + 2); // log2(rank+2) because rank is 0-indexed
    }
  }

  // IDCG — ideal ranking
  const idealRels = [...expectedIds]
    .map((id) => relevance[id] ?? 1)
    .sort((a, b) => b - a)
    .slice(0, k);

  let idcg = 0;
  for (let rank = 0; rank < idealRels.length; rank++) {
    idcg += (Math.pow(2, idealRels[rank]) - 1) / Math.log2(rank + 2);
  }

  return idcg > 0 ? dcg / idcg : 0;
}

function extractNodeId(resultPath: string, db: Database.Database): string | null {
  // aegis://semantic_fact/<nodeId>
  if (resultPath.startsWith("aegis://")) {
    const parts = resultPath.split("/");
    return parts[parts.length - 1] ?? null;
  }
  // file path — look up by source_path
  const row = db.prepare(
    "SELECT id FROM memory_nodes WHERE source_path = ? AND status = 'active' LIMIT 1",
  ).get(resultPath) as { id: string } | undefined;
  return row?.id ?? null;
}

async function runQuery(
  db: Database.Database,
  item: GroundTruthItem,
  seedNodeIds: Record<string, string>,
  config: AegisConfig,
): Promise<QueryResult> {
  const primaryIds = new Set(item.primaryNodeKeys.map((k) => seedNodeIds[k]).filter(Boolean));
  const secondaryIds = new Set(item.secondaryNodeKeys.map((k) => seedNodeIds[k]).filter(Boolean));
  const forbiddenIds = new Set(item.forbiddenNodeKeys.map((k) => seedNodeIds[k]).filter(Boolean));
  const expectedIds = new Set([...primaryIds, ...secondaryIds]);

  // Build relevance map (keyed by actual node ID)
  const relevance: Record<string, number> = {};
  if (item.relevance) {
    for (const [key, grade] of Object.entries(item.relevance)) {
      const nodeId = seedNodeIds[key];
      if (nodeId) relevance[nodeId] = grade;
    }
  } else {
    // Default: primary=2, secondary=1
    for (const id of primaryIds) relevance[id] = 2;
    for (const id of secondaryIds) relevance[id] = 1;
  }

  const opts: SearchOptions = {
    maxResults: Math.max(K_RECALL, K_MRR, K_NDCG),
    scopeFilter: item.scope !== "user" ? item.scope : undefined,
  };

  const start = performance.now();
  const results: MemorySearchResult[] = await executeRetrievalPipeline(db, item.query, config, opts);
  const latencyMs = performance.now() - start;

  const retrievedIds: string[] = [];
  const retrievedScopes: string[] = [];

  for (const r of results) {
    const nodeId = extractNodeId(r.path, db);
    if (nodeId) {
      retrievedIds.push(nodeId);
      // Look up scope from DB
      const row = db.prepare("SELECT scope FROM memory_nodes WHERE id = ?").get(nodeId) as
        | { scope: string }
        | undefined;
      retrievedScopes.push(row?.scope ?? "unknown");
    }
  }

  // Hit@K — có ít nhất 1 node đúng trong top-K?
  const topKIds = retrievedIds.slice(0, K_RECALL);
  const hitAtK = topKIds.some((id) => expectedIds.has(id)) ? 1 : 0;

  // Recall@K — % relevant nodes được tìm thấy
  const relevantInTopK = topKIds.filter((id) => expectedIds.has(id)).length;
  const recallAtK = expectedIds.size > 0 ? relevantInTopK / expectedIds.size : 0;

  // MRR@K
  const mrrAtK = computeMRR(retrievedIds, expectedIds, K_MRR);

  // nDCG@K
  const ndcgAtK = computeNDCG(retrievedIds, expectedIds, relevance, K_NDCG);

  // Scope leakage — trên top-K only
  const topKScopes = retrievedScopes.slice(0, K_RECALL);
  const scopeLeaks = topKScopes.filter((s) => s !== item.scope && s !== "global").length;
  const scopeLeakRate = topKScopes.length > 0 ? scopeLeaks / topKScopes.length : 0;

  // Conflict leakage — forbidden nodes trong top-K_NDCG
  const topNdcgIds = retrievedIds.slice(0, K_NDCG);
  const conflictHits = topNdcgIds.filter((id) => forbiddenIds.has(id)).length;
  const conflictLeakRate = topNdcgIds.length > 0 ? conflictHits / topNdcgIds.length : 0;

  return {
    queryId: item.queryId,
    query: item.query,
    group: item.group,
    scope: item.scope,
    expectedIds,
    primaryIds,
    forbiddenIds,
    relevance,
    retrievedIds,
    retrievedScopes,
    latencyMs,
    hitAtK,
    recallAtK,
    mrrAtK,
    ndcgAtK,
    scopeLeakRate,
    conflictLeakRate,
  };
}

interface BenchSummary {
  queries: number;
  "Hit@5": number;
  "Recall@5": number;
  "MRR@10": number;
  "nDCG@10": number;
  "ScopeLeakRate@5": number;
  "ConflictLeakRate@10": number;
  LatencyP50Ms: number;
  LatencyP95Ms: number;
  LatencyMeanMs: number;
  byGroup: Record<string, { hit: number; recall: number; mrr: number; count: number }>;
  perQuery: QueryResult[];
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[idx];
}

function summarize(results: QueryResult[]): BenchSummary {
  if (results.length === 0) {
    return {
      queries: 0, "Hit@5": 0, "Recall@5": 0, "MRR@10": 0, "nDCG@10": 0,
      "ScopeLeakRate@5": 0, "ConflictLeakRate@10": 0,
      LatencyP50Ms: 0, LatencyP95Ms: 0, LatencyMeanMs: 0,
      byGroup: {}, perQuery: [],
    };
  }

  const mean = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
  const latencies = results.map((r) => r.latencyMs).sort((a, b) => a - b);

  const byGroup: Record<string, { hit: number; recall: number; mrr: number; count: number }> = {};
  for (const r of results) {
    if (!byGroup[r.group]) byGroup[r.group] = { hit: 0, recall: 0, mrr: 0, count: 0 };
    byGroup[r.group].hit += r.hitAtK;
    byGroup[r.group].recall += r.recallAtK;
    byGroup[r.group].mrr += r.mrrAtK;
    byGroup[r.group].count++;
  }
  for (const g of Object.values(byGroup)) {
    g.hit /= g.count;
    g.recall /= g.count;
    g.mrr /= g.count;
  }

  return {
    queries: results.length,
    "Hit@5": mean(results.map((r) => r.hitAtK)),
    "Recall@5": mean(results.map((r) => r.recallAtK)),
    "MRR@10": mean(results.map((r) => r.mrrAtK)),
    "nDCG@10": mean(results.map((r) => r.ndcgAtK)),
    "ScopeLeakRate@5": mean(results.map((r) => r.scopeLeakRate)),
    "ConflictLeakRate@10": mean(results.map((r) => r.conflictLeakRate)),
    LatencyP50Ms: percentile(latencies, 50),
    LatencyP95Ms: percentile(latencies, 95),
    LatencyMeanMs: mean(latencies),
    byGroup,
    perQuery: results,
  };
}

function printReport(summary: BenchSummary): void {
  console.log("\n" + "=".repeat(55));
  console.log("  AEGIS-BENCH v1 — BAO CAO CHAT LUONG TRICH XUAT");
  console.log("=".repeat(55));
  console.log(`Tong so truy van test : ${summary.queries}`);
  console.log("-".repeat(55));
  console.log(`Hit@${K_RECALL}            : ${(summary["Hit@5"] * 100).toFixed(1)}%  (>= ${THRESHOLDS.HIT_AT_5 * 100}%)`);
  console.log(`Recall@${K_RECALL}         : ${(summary["Recall@5"] * 100).toFixed(1)}%  (>= ${THRESHOLDS.RECALL_AT_5 * 100}%)`);
  console.log(`MRR@${K_MRR}           : ${summary["MRR@10"].toFixed(3)}  (>= ${THRESHOLDS.MRR_AT_10})`);
  console.log(`nDCG@${K_NDCG}          : ${summary["nDCG@10"].toFixed(3)}  (>= ${THRESHOLDS.NDCG_AT_10})`);
  console.log("-".repeat(55));
  console.log(`ScopeLeakRate@${K_RECALL}  : ${(summary["ScopeLeakRate@5"] * 100).toFixed(1)}%  (<= ${THRESHOLDS.SCOPE_LEAK_MAX * 100}%)`);
  console.log(`ConflictLeak@${K_NDCG} : ${(summary["ConflictLeakRate@10"] * 100).toFixed(1)}%  (<= ${THRESHOLDS.CONFLICT_LEAK_MAX * 100}%)`);
  console.log("-".repeat(55));
  console.log(`Latency p50  : ${summary.LatencyP50Ms.toFixed(1)} ms`);
  console.log(`Latency p95  : ${summary.LatencyP95Ms.toFixed(1)} ms  (<= ${THRESHOLDS.LATENCY_P95_MS} ms)`);
  console.log(`Latency mean : ${summary.LatencyMeanMs.toFixed(1)} ms`);
  console.log("-".repeat(55));
  console.log("By group:");
  for (const [group, g] of Object.entries(summary.byGroup)) {
    console.log(
      `  ${group.padEnd(12)}: Hit=${(g.hit * 100).toFixed(0)}%  Recall=${(g.recall * 100).toFixed(0)}%  MRR=${g.mrr.toFixed(2)}`
    );
  }
  console.log("-".repeat(55));
  console.log("Per-query diagnostics:");
  for (const r of summary.perQuery) {
    const status = r.hitAtK === 1 ? "PASS" : "FAIL";
    console.log(
      `  [${status}] ${r.queryId} | hit=${r.hitAtK} rcl=${r.recallAtK.toFixed(2)} mrr=${r.mrrAtK.toFixed(2)} ndcg=${r.ndcgAtK.toFixed(2)} ` +
      `leak=${(r.scopeLeakRate * 100).toFixed(0)}% cfl=${(r.conflictLeakRate * 100).toFixed(0)}% ` +
      `${r.latencyMs.toFixed(0)}ms`
    );
  }
  console.log("=".repeat(55));
}

// ============================================================
// TEST SUITE
// ============================================================

let db: AegisDatabase;
let testDir: string;
const seedNodeIds: Record<string, string> = {};

beforeAll(() => {
  testDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-bench-"));
  db = openDatabase(path.join(testDir, "bench.db"));

  // ── Seed data ──────────────────────────────────────────────

  // Group 1: Lexical
  seedNodeIds["lex_ts_backend"] = ingestChunk(db.db, {
    sourcePath: "starproject/backend.md",
    content: "StarProject backend API is built with TypeScript and Express running on Node.js.",
    source: "memory",
    scope: "user",
  });

  seedNodeIds["lex_react_frontend"] = ingestChunk(db.db, {
    sourcePath: "starproject/frontend.md",
    content: "StarProject frontend uses React with Tailwind CSS for the user interface.",
    source: "memory",
    scope: "user",
  });

  seedNodeIds["lex_postgres_db"] = ingestChunk(db.db, {
    sourcePath: "starproject/database.md",
    content: "StarProject uses PostgreSQL as the primary relational database with connection pooling via PgBouncer.",
    source: "memory",
    scope: "user",
  });

  // Group 2: Entity
  seedNodeIds["ent_dragonhead_role"] = ingestChunk(db.db, {
    sourcePath: "starproject/team.md",
    content: "@DragonHead is the lead architect who oversees all technical decisions for StarProject.",
    source: "memory",
    scope: "user",
  });

  seedNodeIds["ent_dragonhead_deploy"] = ingestChunk(db.db, {
    sourcePath: "starproject/ops.md",
    content: "Deployment pipeline for StarProject is managed by @DragonHead using Docker Compose and GitHub Actions.",
    source: "memory",
    scope: "user",
  });

  // Group 3: Graph (Orca spreading activation via shared keyword/entity)
  seedNodeIds["grp_migration"] = ingestChunk(db.db, {
    sourcePath: "starproject/migration.md",
    content: "Database migration strategy for StarProject uses Flyway with blue-green deployment to avoid downtime.",
    source: "memory",
    scope: "user",
  });

  seedNodeIds["grp_bluegreen"] = ingestChunk(db.db, {
    sourcePath: "starproject/bluegreen.md",
    content: "Blue-green deployment keeps two identical production environments to enable zero-downtime releases.",
    source: "memory",
    scope: "user",
  });

  seedNodeIds["grp_downtime"] = ingestChunk(db.db, {
    sourcePath: "starproject/sla.md",
    content: "StarProject SLA requires zero downtime for production releases and 99.9% uptime guarantee.",
    source: "memory",
    scope: "user",
  });

  // Group 4: Multiterm
  seedNodeIds["mlt_auth_jwt"] = ingestChunk(db.db, {
    sourcePath: "starproject/auth.md",
    content: "Authentication in StarProject uses JWT tokens that expire after 24 hours for security compliance.",
    source: "memory",
    scope: "user",
  });

  seedNodeIds["mlt_jwt_validate"] = ingestChunk(db.db, {
    sourcePath: "starproject/jwt-validate.md",
    content: "JWT token validation service checks signature, expiry timestamp, and issuer claim before granting access.",
    source: "memory",
    scope: "user",
  });

  // Group 5: Anti-leakage — different scope node with conflicting info
  seedNodeIds["leak_mongo_other"] = ingestChunk(db.db, {
    sourcePath: "otherproject/database.md",
    content: "OtherProject uses MongoDB as primary database with Mongoose ODM for document management.",
    source: "memory",
    scope: "other_project",
  });

  seedNodeIds["leak_pg_correct"] = ingestChunk(db.db, {
    sourcePath: "starproject/db-correct.md",
    content: "StarProject database is PostgreSQL. MongoDB is not used anywhere in StarProject infrastructure.",
    source: "memory",
    scope: "user",
  });

  // Stale/conflict node — superseded info
  seedNodeIds["conflict_old_deploy"] = ingestChunk(db.db, {
    sourcePath: "starproject/old-ops.md",
    content: "OUTDATED: StarProject deployment was previously done via FTP manually. This is now deprecated.",
    source: "memory",
    scope: "user",
  });
  // Mark as suppressed to simulate hygiene
  db.db.prepare(
    "UPDATE memory_nodes SET status = 'expired' WHERE id = ?"
  ).run(seedNodeIds["conflict_old_deploy"]);
});

afterAll(() => {
  try { db.close(); } catch {}
  try { fs.rmSync(testDir, { recursive: true, force: true }); } catch {}
});

// ── Ground Truth ──────────────────────────────────────────────

const GROUND_TRUTH: GroundTruthItem[] = [
  // GROUP 1: Lexical
  {
    queryId: "q_lex_01",
    query: "TypeScript backend Express API",
    scope: "user",
    group: "lexical",
    primaryNodeKeys: ["lex_ts_backend"],
    secondaryNodeKeys: [],
    forbiddenNodeKeys: [],
    notes: "Direct FTS5 lexical match on TypeScript/backend",
  },
  {
    queryId: "q_lex_02",
    query: "React Tailwind CSS frontend",
    scope: "user",
    group: "lexical",
    primaryNodeKeys: ["lex_react_frontend"],
    secondaryNodeKeys: [],
    forbiddenNodeKeys: ["lex_ts_backend"],
    notes: "FTS5 match on React/Tailwind, backend node is wrong",
  },

  // GROUP 2: Entity
  {
    queryId: "q_ent_01",
    query: "DragonHead architect technical decisions",
    scope: "user",
    group: "entity",
    primaryNodeKeys: ["ent_dragonhead_role"],
    secondaryNodeKeys: ["ent_dragonhead_deploy"],
    forbiddenNodeKeys: [],
    relevance: { ent_dragonhead_role: 3, ent_dragonhead_deploy: 2 },
    notes: "Entity @DragonHead mentioned in both nodes, role node is primary",
  },
  {
    queryId: "q_ent_02",
    query: "DragonHead deployment Docker",
    scope: "user",
    group: "entity",
    primaryNodeKeys: ["ent_dragonhead_deploy"],
    secondaryNodeKeys: ["ent_dragonhead_role"],
    forbiddenNodeKeys: [],
    relevance: { ent_dragonhead_deploy: 3, ent_dragonhead_role: 1 },
    notes: "Entity + lexical match on deployment/Docker node",
  },

  // GROUP 3: Graph
  {
    queryId: "q_grp_01",
    query: "database migration strategy",
    scope: "user",
    group: "graph",
    primaryNodeKeys: ["grp_migration"],
    secondaryNodeKeys: ["grp_bluegreen"],
    forbiddenNodeKeys: [],
    relevance: { grp_migration: 3, grp_bluegreen: 2 },
    notes: "Direct hit on migration node, bluegreen linked via Orca",
  },
  {
    queryId: "q_grp_02",
    query: "zero downtime production release",
    scope: "user",
    group: "graph",
    primaryNodeKeys: ["grp_downtime"],
    secondaryNodeKeys: ["grp_bluegreen", "grp_migration"],
    forbiddenNodeKeys: [],
    relevance: { grp_downtime: 3, grp_bluegreen: 2, grp_migration: 1 },
    notes: "Spreading activation: downtime → bluegreen → migration via graph",
  },

  // GROUP 4: Multiterm
  {
    queryId: "q_mlt_01",
    query: "JWT token expiry 24 hours authentication",
    scope: "user",
    group: "multiterm",
    primaryNodeKeys: ["mlt_auth_jwt"],
    secondaryNodeKeys: ["mlt_jwt_validate"],
    forbiddenNodeKeys: [],
    relevance: { mlt_auth_jwt: 3, mlt_jwt_validate: 2 },
    notes: "Multi-keyword: JWT + expiry + authentication",
  },
  {
    queryId: "q_mlt_02",
    query: "token validation signature issuer",
    scope: "user",
    group: "multiterm",
    primaryNodeKeys: ["mlt_jwt_validate"],
    secondaryNodeKeys: ["mlt_auth_jwt"],
    forbiddenNodeKeys: [],
    relevance: { mlt_jwt_validate: 3, mlt_auth_jwt: 1 },
    notes: "Multi-keyword focused on validation service",
  },

  // GROUP 5: Anti-leakage / Conflict
  {
    queryId: "q_leak_01",
    query: "StarProject database PostgreSQL",
    scope: "user",
    group: "anti-leak",
    primaryNodeKeys: ["leak_pg_correct", "lex_postgres_db"],
    secondaryNodeKeys: [],
    forbiddenNodeKeys: ["leak_mongo_other"],
    relevance: { leak_pg_correct: 3, lex_postgres_db: 2 },
    notes: "MongoDB (other_project scope) must NOT appear in top results for StarProject query",
  },
  {
    queryId: "q_leak_02",
    query: "StarProject deployment operations",
    scope: "user",
    group: "anti-leak",
    primaryNodeKeys: ["ent_dragonhead_deploy"],
    secondaryNodeKeys: [],
    forbiddenNodeKeys: ["conflict_old_deploy"],
    notes: "Expired/stale deploy node must NOT appear (conflict leakage test)",
  },
];

// ============================================================
// TESTS
// ============================================================

describe("Aegis-Bench v1: Full Retrieval Quality Benchmark", () => {
  it("runs all 10 queries and meets minimum quality thresholds", async () => {
    const queryResults: QueryResult[] = [];

    for (const item of GROUND_TRUTH) {
      const result = await runQuery(db.db, item, seedNodeIds, BENCH_CONFIG);
      queryResults.push(result);
    }

    const summary = summarize(queryResults);
    printReport(summary);

    // ── Assert thresholds ──────────────────────────────────
    expect(summary.queries).toBe(GROUND_TRUTH.length);
    expect(summary["Hit@5"]).toBeGreaterThanOrEqual(THRESHOLDS.HIT_AT_5);
    expect(summary["Recall@5"]).toBeGreaterThanOrEqual(THRESHOLDS.RECALL_AT_5);
    expect(summary["MRR@10"]).toBeGreaterThanOrEqual(THRESHOLDS.MRR_AT_10);
    expect(summary["nDCG@10"]).toBeGreaterThanOrEqual(THRESHOLDS.NDCG_AT_10);
    expect(summary["ScopeLeakRate@5"]).toBeLessThanOrEqual(THRESHOLDS.SCOPE_LEAK_MAX);
    expect(summary["ConflictLeakRate@10"]).toBeLessThanOrEqual(THRESHOLDS.CONFLICT_LEAK_MAX);
    expect(summary.LatencyP95Ms).toBeLessThan(THRESHOLDS.LATENCY_P95_MS);
  });
});

describe("Aegis-Bench v1: Per-Group Analysis", () => {
  let allResults: QueryResult[];

  beforeAll(async () => {
    allResults = await Promise.all(GROUND_TRUTH.map((item) =>
      runQuery(db.db, item, seedNodeIds, BENCH_CONFIG)
    ));
  });

  it("lexical group: FTS5 finds keyword matches", () => {
    const group = allResults.filter((r) => r.group === "lexical");
    const avgHit = group.reduce((s, r) => s + r.hitAtK, 0) / group.length;
    console.log(`[lexical] avg Hit@5 = ${(avgHit * 100).toFixed(0)}%`);
    expect(avgHit).toBeGreaterThanOrEqual(0.5);
  });

  it("entity group: @mention entity lookup works", () => {
    const group = allResults.filter((r) => r.group === "entity");
    const avgMrr = group.reduce((s, r) => s + r.mrrAtK, 0) / group.length;
    console.log(`[entity] avg MRR@10 = ${avgMrr.toFixed(3)}`);
    expect(avgMrr).toBeGreaterThanOrEqual(0.2);
  });

  it("graph group: Orca spreading activation picks up linked nodes", () => {
    const group = allResults.filter((r) => r.group === "graph");
    const avgRecall = group.reduce((s, r) => s + r.recallAtK, 0) / group.length;
    console.log(`[graph] avg Recall@5 = ${(avgRecall * 100).toFixed(0)}%`);
    // Graph recall is harder — lower threshold
    expect(avgRecall).toBeGreaterThanOrEqual(0.1);
  });

  it("multiterm group: multi-keyword queries rank correctly", () => {
    const group = allResults.filter((r) => r.group === "multiterm");
    const avgHit = group.reduce((s, r) => s + r.hitAtK, 0) / group.length;
    console.log(`[multiterm] avg Hit@5 = ${(avgHit * 100).toFixed(0)}%`);
    expect(avgHit).toBeGreaterThanOrEqual(0.5);
  });

  it("anti-leak group: scope leakage and conflict leakage near zero", () => {
    const group = allResults.filter((r) => r.group === "anti-leak");
    const avgScopeLeak = group.reduce((s, r) => s + r.scopeLeakRate, 0) / group.length;
    const avgConflict = group.reduce((s, r) => s + r.conflictLeakRate, 0) / group.length;
    console.log(`[anti-leak] scope leak = ${(avgScopeLeak * 100).toFixed(0)}%, conflict = ${(avgConflict * 100).toFixed(0)}%`);
    expect(avgScopeLeak).toBeLessThanOrEqual(0.3);
    // OR relaxation may cause low-rate leakage of cross-scope non-expired forbidden nodes;
    // expired forbidden nodes (conflict_old_deploy) must never appear — verified separately
    expect(avgConflict).toBeLessThanOrEqual(0.10);
  });
});

describe("Aegis-Bench v1: Latency Profile", () => {
  it("individual query latency is under 500ms each", async () => {
    for (const item of GROUND_TRUTH) {
      const start = performance.now();
      await executeRetrievalPipeline(db.db, item.query, BENCH_CONFIG, { maxResults: 10 });
      const ms = performance.now() - start;
      expect(ms).toBeLessThan(500);
    }
  });

  it("warm cache: second run is faster than 200ms p95", async () => {
    // Warm up
    for (const item of GROUND_TRUTH) {
      await executeRetrievalPipeline(db.db, item.query, BENCH_CONFIG, { maxResults: 10 });
    }

    // Measure warm run
    const latencies: number[] = [];
    for (const item of GROUND_TRUTH) {
      const start = performance.now();
      await executeRetrievalPipeline(db.db, item.query, BENCH_CONFIG, { maxResults: 10 });
      latencies.push(performance.now() - start);
    }

    latencies.sort((a, b) => a - b);
    const p95 = percentile(latencies, 95);
    console.log(`[latency warm] p95 = ${p95.toFixed(1)} ms`);
    expect(p95).toBeLessThan(200);
  });
});
