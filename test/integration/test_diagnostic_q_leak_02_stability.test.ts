/**
 * Diagnostic Test: q_leak_02 Ranking Stability
 *
 * Purpose: Determine whether q_leak_02 ("StarProject deployment operations")
 * is unstable due to:
 *   (a) Algorithmic non-determinism — same DB, different results each run
 *   (b) Score near-tie — correct node and forbidden node have very close scores,
 *       making rank order sensitive to tie-breaking
 *   (c) Orca over-expansion — spreading activation pulls in conflict_old_deploy
 *       via graph proximity to deployment-related nodes
 *
 * Strategy:
 *   Run 1: Confirm baseline (seed data once, run 5 times on same DB)
 *   Run 2: Score gap analysis (correct node vs. forbidden node, per run)
 *   Run 3: All 10 queries × 5 runs to find other unstable queries
 *   Run 4: Orca path trace — which edges connect conflict_old_deploy to seeds
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

import { openDatabase } from "../../src/db/connection.js";
import type { AegisDatabase } from "../../src/db/connection.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { fts5Search, findEntityMatches } from "../../src/retrieval/fts-search.js";
import { assignInitialActivation, spreadingActivation } from "../../src/retrieval/graph-walk.js";
import { DEFAULT_AEGIS_CONFIG, CONSTANTS } from "../../src/core/models.js";
import {
  seedGroundTruthData,
  GROUND_TRUTH,
  extractNodeId,
  runQuery,
  summarize,
} from "../helpers/aegis-bench.js";

// ============================================================
// Setup
// ============================================================

const STABILITY_RUNS = 5;
const QUERY_ID = "q_leak_02";
const GT = GROUND_TRUTH.find((q) => q.queryId === QUERY_ID)!;

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
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-stability-"));
  dbPath = path.join(tmpDir, "stability.db");
  dbHandle = openDatabase(dbPath);
  seedIds = seedGroundTruthData(dbHandle.db);
});

afterAll(() => {
  dbHandle.close();
  try { fs.rmSync(path.dirname(dbPath), { recursive: true }); } catch {}
});

// ============================================================
// Helper
// ============================================================

function nodeKey(nodeId: string): string {
  for (const [k, v] of Object.entries(seedIds)) {
    if (v === nodeId) return k;
  }
  return nodeId.slice(0, 12) + "…";
}

// ============================================================
// Run 1: Determinism check — same DB, 5 runs
// ============================================================

describe("q_leak_02 determinism — same DB, 5 runs", () => {
  it(`runs q_leak_02 ${STABILITY_RUNS} times and checks consistency`, async () => {
    const db = dbHandle.db;
    const results: Array<{ run: number; hit: number; topIds: string[] }> = [];

    console.log(`\n━━━ q_leak_02 Stability: ${STABILITY_RUNS} runs on same DB ━━━`);
    console.log(`  Query: "${GT.query}"`);

    for (let i = 0; i < STABILITY_RUNS; i++) {
      const qr = await runQuery(db, GT, seedIds, config, 10);
      results.push({ run: i + 1, hit: qr.hitAtK, topIds: qr.retrievedIds.slice(0, 5) });
    }

    let allSame = true;
    for (let i = 1; i < results.length; i++) {
      const r = results[i];
      const r0 = results[0];
      if (JSON.stringify(r.topIds) !== JSON.stringify(r0.topIds)) {
        allSame = false;
      }
    }

    console.log(`  Deterministic (same order every run): ${allSame ? "YES ✓" : "NO ✗"}`);
    for (const r of results) {
      const keys = r.topIds.map(nodeKey).join(", ");
      console.log(`  Run ${r.run}: hit=${r.hit}  top5=[${keys}]`);
    }

    if (!allSame) {
      console.warn("  ⚠ Non-determinism detected — SQLite BM25 or FTS tie-breaking is unstable");
    } else {
      console.log("  → Same DB result is deterministic: instability is data-sensitivity, not randomness");
    }

    const passRate = results.filter((r) => r.hit === 1).length / STABILITY_RUNS;
    console.log(`  Pass rate: ${(passRate * 100).toFixed(0)}% (${results.filter((r) => r.hit === 1).length}/${STABILITY_RUNS})`);

    expect(results.length).toBe(STABILITY_RUNS);
  });
});

// ============================================================
// Run 2: Score gap analysis
// ============================================================

describe("q_leak_02 score gap — correct vs forbidden node", () => {
  it("compares raw pipeline scores for correct vs forbidden node", async () => {
    const db = dbHandle.db;

    const correctNodeId = seedIds["ent_dragonhead_deploy"];
    const forbiddenNodeId = seedIds["conflict_old_deploy"];

    console.log(`\n━━━ q_leak_02 Score Gap Analysis ━━━`);
    console.log(`  Correct  (ent_dragonhead_deploy): ${correctNodeId?.slice(0, 16)}…`);
    console.log(`  Forbidden (conflict_old_deploy) : ${forbiddenNodeId?.slice(0, 16)}… (status=expired)`);

    // Check status of forbidden node
    const forbiddenStatus = db.prepare(
      "SELECT status, memory_state FROM memory_nodes WHERE id = ?"
    ).get(forbiddenNodeId) as { status: string; memory_state: string } | undefined;
    console.log(`  Forbidden node status: ${forbiddenStatus?.status}, state: ${forbiddenStatus?.memory_state}`);

    // Run pipeline with increased results to capture ranking signal
    const results = await executeRetrievalPipeline(db, GT.query, config, {
      maxResults: 20,
      scopeFilter: GT.scope !== "user" ? GT.scope : undefined,
    });

    let correctRank: number | null = null;
    let correctScore: number | null = null;
    let forbiddenRank: number | null = null;
    let forbiddenScore: number | null = null;

    for (let i = 0; i < results.length; i++) {
      const nodeId = extractNodeId(results[i].path, db);
      if (nodeId === correctNodeId) { correctRank = i + 1; correctScore = results[i].score; }
      if (nodeId === forbiddenNodeId) { forbiddenRank = i + 1; forbiddenScore = results[i].score; }
    }

    console.log("\n  Pipeline output (top 10):");
    for (let i = 0; i < Math.min(10, results.length); i++) {
      const nodeId = extractNodeId(results[i].path, db);
      const tag = nodeId === correctNodeId ? " ← CORRECT" :
                  nodeId === forbiddenNodeId ? " ← FORBIDDEN (expired!)" : "";
      console.log(`    rank=${i + 1}  score=${results[i].score.toFixed(4)}  [${nodeId ? nodeKey(nodeId) : "?"}]${tag}`);
    }

    console.log(`\n  Correct  node rank: ${correctRank ?? "NOT IN TOP 20"}  score: ${correctScore?.toFixed(4) ?? "N/A"}`);
    console.log(`  Forbidden node rank: ${forbiddenRank ?? "NOT IN TOP 20"}  score: ${forbiddenScore?.toFixed(4) ?? "N/A"}`);

    if (correctScore !== null && forbiddenScore !== null) {
      const gap = correctScore - forbiddenScore;
      console.log(`  Score gap (correct - forbidden): ${gap.toFixed(4)}`);
      if (Math.abs(gap) < 0.05) {
        console.warn("  ⚠ Score gap < 0.05 — near-tie, ranking is fragile");
      } else {
        console.log("  → Gap is sufficient, near-tie is not the issue");
      }
    }

    // Confirm forbidden (expired) node is filtered by status='active' check in reranker
    expect(forbiddenRank).toBeNull(); // expired nodes should NEVER appear
  });

  it("verifies conflict_old_deploy has status=expired and is NOT in FTS seeds", async () => {
    const db = dbHandle.db;
    const forbiddenId = seedIds["conflict_old_deploy"];

    const node = db.prepare("SELECT id, status, content FROM memory_nodes WHERE id = ?")
      .get(forbiddenId) as { id: string; status: string; content: string } | undefined;

    console.log(`\n━━━ conflict_old_deploy node status ━━━`);
    console.log(`  status  : ${node?.status}`);
    console.log(`  content : ${node?.content?.slice(0, 60)}…`);

    expect(node?.status).toBe("expired");

    // Check FTS5 — expired nodes should not appear (fts-search.ts filters status='active')
    const ftsResults = fts5Search(db, GT.query);
    const ftsIds = new Set(ftsResults.map((r) => r.nodeId));
    const inFts = ftsIds.has(forbiddenId);
    console.log(`  In FTS5 seeds : ${inFts ? "YES (problem!)" : "NO ✓"}`);
    expect(inFts).toBe(false);
  });
});

// ============================================================
// Run 3: All 10 queries stability across 5 runs
// ============================================================

describe("All 10 queries — multi-run stability profile", () => {
  it("identifies which queries have unstable ranking across runs", async () => {
    const db = dbHandle.db;

    console.log(`\n━━━ 10-query × ${STABILITY_RUNS}-run stability matrix ━━━`);
    console.log("  queryId       " + Array.from({ length: STABILITY_RUNS }, (_, i) => `R${i + 1}`).join("  ") + "  passRate");
    console.log("  " + "─".repeat(50));

    const unstableQueries: string[] = [];

    for (const gt of GROUND_TRUTH) {
      const runResults: number[] = [];
      const runTopNode: string[] = [];

      for (let i = 0; i < STABILITY_RUNS; i++) {
        const qr = await runQuery(db, gt, seedIds, config, 10);
        runResults.push(qr.hitAtK);
        const topId = qr.retrievedIds[0] ?? "";
        runTopNode.push(topId ? nodeKey(topId) : "—");
      }

      const passRate = runResults.filter((r) => r === 1).length / STABILITY_RUNS;
      const allSame = new Set(runTopNode).size === 1;
      const stable = allSame ? "✓" : "⚠";
      const runStr = runResults.map((r) => (r === 1 ? "✓" : "✗")).join("  ");

      console.log(`  ${gt.queryId.padEnd(14)} ${runStr}  ${(passRate * 100).toFixed(0)}%  ${stable}`);

      if (!allSame) unstableQueries.push(gt.queryId);
    }

    console.log(`\n  Determinism issues: ${unstableQueries.length === 0 ? "none ✓" : unstableQueries.join(", ")}`);

    if (unstableQueries.length > 0) {
      console.warn("  ⚠ Unstable queries detected — investigate FTS BM25 tie-breaking");
    }

    expect(GROUND_TRUTH.length).toBe(10);
  });
});

// ============================================================
// Run 4: Orca path trace — how does conflict_old_deploy get activated?
// ============================================================

describe("Orca path trace — conflict_old_deploy activation route", () => {
  it("checks edges that could propagate activation to conflict_old_deploy", async () => {
    const db = dbHandle.db;
    const forbiddenId = seedIds["conflict_old_deploy"];

    console.log(`\n━━━ Orca path to conflict_old_deploy ━━━`);

    // Check direct in-edges to forbidden node
    const inEdges = db.prepare(`
      SELECT src_node_id, edge_type, weight, confidence, status
      FROM memory_edges
      WHERE dst_node_id = ?
      ORDER BY weight DESC
    `).all(forbiddenId) as Array<{
      src_node_id: string; edge_type: string; weight: number;
      confidence: number; status: string;
    }>;

    if (inEdges.length === 0) {
      console.log("  No in-edges to conflict_old_deploy — not reachable via Orca ✓");
    } else {
      console.log(`  ${inEdges.length} in-edge(s) to conflict_old_deploy:`);
      for (const e of inEdges) {
        console.log(`    src=[${nodeKey(e.src_node_id)}]  type=${e.edge_type}  w=${e.weight.toFixed(3)}  conf=${e.confidence.toFixed(3)}  status=${e.status}`);
      }
    }

    // Check direct out-edges from forbidden node
    const outEdges = db.prepare(`
      SELECT dst_node_id, edge_type, weight, confidence, status
      FROM memory_edges
      WHERE src_node_id = ?
      ORDER BY weight DESC
    `).all(forbiddenId) as Array<{
      dst_node_id: string; edge_type: string; weight: number;
      confidence: number; status: string;
    }>;

    if (outEdges.length === 0) {
      console.log("  No out-edges from conflict_old_deploy");
    } else {
      console.log(`  ${outEdges.length} out-edge(s) from conflict_old_deploy:`);
      for (const e of outEdges) {
        console.log(`    dst=[${nodeKey(e.dst_node_id)}]  type=${e.edge_type}  w=${e.weight.toFixed(3)}  status=${e.status}`);
      }
    }

    // Run spreading activation and check if forbidden node gets activated
    const ftsResults = fts5Search(db, GT.query);
    const entityHits = findEntityMatches(db, GT.query);
    const seeds = assignInitialActivation(ftsResults, entityHits);

    if (seeds.size > 0) {
      const activated = spreadingActivation(seeds, db, {
        maxHops: config.retrievalMaxHops,
        dampingFactor: config.dampingFactor,
        activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
        maxNodes: config.maxNodesPerSearch,
        scopeFilter: undefined,
      });

      const forbiddenActivated = activated.has(forbiddenId);
      const forbiddenActivationScore = activated.get(forbiddenId);

      console.log(`\n  Seeds: ${seeds.size}, Activated: ${activated.size}`);
      console.log(`  conflict_old_deploy activated: ${forbiddenActivated}`);
      if (forbiddenActivated) {
        console.log(`  Activation score: ${forbiddenActivationScore?.toFixed(4)}`);
        console.warn("  ⚠ Forbidden node IS activated by Orca — but reranker should filter status≠active");
      } else {
        console.log("  Forbidden node NOT activated by Orca ✓");
      }
    }

    // conflict_old_deploy should not appear in final results because reranker
    // filters status !== 'active' in pipeline.ts
    const finalResults = await executeRetrievalPipeline(db, GT.query, config, {
      maxResults: 20,
      scopeFilter: undefined,
    });
    const finalIds = finalResults
      .map((r) => extractNodeId(r.path, db))
      .filter(Boolean) as string[];

    const forbiddenInFinal = finalIds.includes(forbiddenId);
    console.log(`\n  conflict_old_deploy in final results: ${forbiddenInFinal ? "YES ✗ BUG!" : "NO ✓"}`);
    expect(forbiddenInFinal).toBe(false);
  });

  it("detects if q_leak_02 failure is a Hit@5 miss (correct node ranks >5)", async () => {
    const db = dbHandle.db;

    const results = await executeRetrievalPipeline(db, GT.query, config, {
      maxResults: 20,
      scopeFilter: GT.scope !== "user" ? GT.scope : undefined,
    });

    const correctId = seedIds["ent_dragonhead_deploy"];
    const retrievedIds = results
      .map((r) => extractNodeId(r.path, db))
      .filter(Boolean) as string[];

    const rankOfCorrect = retrievedIds.indexOf(correctId);

    console.log(`\n━━━ q_leak_02 correct node rank ━━━`);
    console.log(`  ent_dragonhead_deploy rank: ${rankOfCorrect === -1 ? "NOT IN TOP 20" : rankOfCorrect + 1}`);

    if (rankOfCorrect === -1) {
      console.warn("  ⚠ Correct node not in top 20 — node is being filtered by reranker or minScore");

      // Check if it's in activation set at all
      const ftsResults = fts5Search(db, GT.query);
      const entityHits = findEntityMatches(db, GT.query);
      const seeds = assignInitialActivation(ftsResults, entityHits);
      if (seeds.size > 0) {
        const activated = spreadingActivation(seeds, db, {
          maxHops: config.retrievalMaxHops,
          dampingFactor: config.dampingFactor,
          activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
          maxNodes: config.maxNodesPerSearch,
          scopeFilter: undefined,
        });
        console.log(`  In FTS seeds: ${seeds.has(correctId)}`);
        console.log(`  In activation: ${activated.has(correctId)} (score=${activated.get(correctId)?.toFixed(4) ?? "N/A"})`);
      }
    } else if (rankOfCorrect >= 5) {
      console.warn(`  ⚠ Correct node at rank ${rankOfCorrect + 1} — below Hit@5 cutoff`);
    } else {
      console.log(`  Correct node at rank ${rankOfCorrect + 1} — within Hit@5 ✓`);
    }

    expect(retrievedIds.length).toBeGreaterThanOrEqual(0);
  });
});
