/**
 * Diagnostic Test: q_mlt_01 Pipeline Trace
 *
 * Purpose: Trace "JWT token expiry 24 hours authentication" through every
 * pipeline stage to identify exactly where the expected nodes drop out.
 *
 * Stages traced:
 *   0. FTS query string built by buildFtsQuery
 *   1. FTS5 seed results (raw BM25 scores)
 *   2. Entity matching results
 *   3. Seeds after assignInitialActivation
 *   4. Spreading activation output
 *   5. Final reranked pipeline output
 *
 * This is a diagnostic/logging test — all assertions are soft checks to
 * document the actual observed behaviour rather than enforce correctness.
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
import { buildFtsQuery } from "../../src/core/normalize.js";
import { DEFAULT_AEGIS_CONFIG, CONSTANTS } from "../../src/core/models.js";
import {
  seedGroundTruthData,
  GROUND_TRUTH,
  extractNodeId,
} from "../helpers/aegis-bench.js";

// ============================================================
// Setup
// ============================================================

const QUERY = "JWT token expiry 24 hours authentication";
const QUERY_ID = "q_mlt_01";
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
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-trace-mlt01-"));
  dbPath = path.join(tmpDir, "trace.db");
  dbHandle = openDatabase(dbPath);
  seedIds = seedGroundTruthData(dbHandle.db);
});

afterAll(() => {
  dbHandle.close();
  try { fs.rmSync(path.dirname(dbPath), { recursive: true }); } catch {}
});

// ============================================================
// Helper: resolve node key from node ID
// ============================================================

function nodeKey(nodeId: string): string {
  for (const [k, v] of Object.entries(seedIds)) {
    if (v === nodeId) return k;
  }
  return nodeId.slice(0, 12) + "…";
}

// ============================================================
// Stage 0: FTS Query Builder
// ============================================================

describe("Stage 0 — FTS query builder", () => {
  it("buildFtsQuery produces a non-null query string", () => {
    const ftsQuery = buildFtsQuery(QUERY);

    console.log("\n━━━ Stage 0: buildFtsQuery ━━━");
    console.log(`  Raw query : "${QUERY}"`);
    console.log(`  FTS query : ${ftsQuery}`);

    expect(ftsQuery).not.toBeNull();
    expect(ftsQuery!.length).toBeGreaterThan(0);
  });

  it("FTS query contains all major tokens from the query", () => {
    const ftsQuery = buildFtsQuery(QUERY)!;
    // Tokens extracted from QUERY: JWT, token, expiry, 24, hours, authentication
    const important = ["JWT", "token", "expiry", "authentication"];

    const missing: string[] = [];
    for (const tok of important) {
      // Check case-insensitively — FTS query may lowercase tokens
      if (!ftsQuery.toLowerCase().includes(tok.toLowerCase())) {
        missing.push(tok);
      }
    }

    console.log(`  Tokens checked : ${important.join(", ")}`);
    console.log(`  Missing        : ${missing.length === 0 ? "none" : missing.join(", ")}`);

    // Document the result — not a hard failure
    if (missing.length > 0) {
      console.warn(`  ⚠ Some tokens missing from FTS query: ${missing.join(", ")}`);
    }
    expect(missing).toEqual([]); // Hard assert — if this fails, we found the root cause
  });

  it("FTS query uses NEAR or AND for multi-token query", () => {
    const ftsQuery = buildFtsQuery(QUERY)!;
    const hasNear = ftsQuery.includes("NEAR(");
    const hasAnd = ftsQuery.includes(" AND ");

    console.log(`  Has NEAR : ${hasNear}`);
    console.log(`  Has AND  : ${hasAnd}`);

    expect(hasNear || hasAnd).toBe(true);
  });
});

// ============================================================
// Stage 1: FTS5 Seed Results
// ============================================================

describe("Stage 1 — FTS5 seed results", () => {
  it("FTS5 returns results for the query", () => {
    const db = dbHandle.db;
    const ftsResults = fts5Search(db, QUERY);

    console.log("\n━━━ Stage 1: FTS5 results ━━━");
    if (ftsResults.length === 0) {
      console.log("  ⚠ FTS5 returned NO results!");
    } else {
      for (const r of ftsResults) {
        const key = nodeKey(r.nodeId);
        console.log(`  score=${r.score.toFixed(4)}  [${key}]  ${r.content.slice(0, 60)}…`);
      }
    }

    // Diagnostic: FTS5 may return 0 if the AND/NEAR query is too strict — that IS the finding
    if (ftsResults.length === 0) {
      console.warn("  ⚠ ROOT CAUSE CONFIRMED: FTS5 AND/NEAR query too strict, 0 results returned");
    }
    expect(ftsResults.length).toBeGreaterThanOrEqual(0);
  });

  it("expected nodes mlt_auth_jwt and mlt_jwt_validate appear in FTS5 seeds", () => {
    const db = dbHandle.db;
    const ftsResults = fts5Search(db, QUERY);
    const retrievedNodeIds = new Set(ftsResults.map((r) => r.nodeId));

    const authJwtId = seedIds["mlt_auth_jwt"];
    const jwtValidateId = seedIds["mlt_jwt_validate"];

    const authJwtInFts = retrievedNodeIds.has(authJwtId);
    const jwtValidateInFts = retrievedNodeIds.has(jwtValidateId);

    console.log("\n━━━ Stage 1: Expected node presence ━━━");
    console.log(`  mlt_auth_jwt    (${authJwtId?.slice(0, 12)}…) in FTS5 : ${authJwtInFts}`);
    console.log(`  mlt_jwt_validate (${jwtValidateId?.slice(0, 12)}…) in FTS5 : ${jwtValidateInFts}`);

    if (!authJwtInFts) {
      // Check what FTS query was built
      const ftsQuery = buildFtsQuery(QUERY);
      console.log(`  ↳ FTS query was: ${ftsQuery}`);
      // Try direct content match to confirm the node exists and is active
      const directRow = db.prepare(
        "SELECT id, content, status FROM memory_nodes WHERE id = ?"
      ).get(authJwtId) as { id: string; content: string; status: string } | undefined;
      console.log(`  ↳ mlt_auth_jwt node direct lookup: ${JSON.stringify(directRow)}`);
    }
    if (!jwtValidateInFts) {
      const directRow = db.prepare(
        "SELECT id, content, status FROM memory_nodes WHERE id = ?"
      ).get(jwtValidateId) as { id: string; content: string; status: string } | undefined;
      console.log(`  ↳ mlt_jwt_validate node direct lookup: ${JSON.stringify(directRow)}`);
    }

    // Document findings
    if (!authJwtInFts || !jwtValidateInFts) {
      console.warn("  ⚠ One or both expected nodes ABSENT from FTS5 — this is the root cause!");
    }
  });

  it("scores of expected nodes vs. top result gap", () => {
    const db = dbHandle.db;
    const ftsResults = fts5Search(db, QUERY);
    if (ftsResults.length === 0) return;

    const scoreMap = new Map(ftsResults.map((r) => [r.nodeId, r.score]));
    const topScore = ftsResults[0]?.score ?? 0;

    const authJwtScore = scoreMap.get(seedIds["mlt_auth_jwt"]);
    const jwtValidateScore = scoreMap.get(seedIds["mlt_jwt_validate"]);

    console.log("\n━━━ Stage 1: Score gap analysis ━━━");
    console.log(`  Top FTS5 score   : ${topScore.toFixed(4)}`);
    console.log(`  mlt_auth_jwt     : ${authJwtScore !== undefined ? authJwtScore.toFixed(4) : "NOT IN RESULTS"}`);
    console.log(`  mlt_jwt_validate : ${jwtValidateScore !== undefined ? jwtValidateScore.toFixed(4) : "NOT IN RESULTS"}`);
  });
});

// ============================================================
// Stage 2: Entity Matching
// ============================================================

describe("Stage 2 — Entity matching", () => {
  it("entity matching runs without error", () => {
    const db = dbHandle.db;
    const entityHits = findEntityMatches(db, QUERY);

    console.log("\n━━━ Stage 2: Entity matches ━━━");
    if (entityHits.length === 0) {
      console.log("  No entity matches (expected — JWT/authentication are not @entity tokens)");
    } else {
      for (const h of entityHits) {
        console.log(`  nodeId=${nodeKey(h.nodeId)}  confidence=${h.confidence.toFixed(3)}`);
      }
    }

    expect(Array.isArray(entityHits)).toBe(true);
  });
});

// ============================================================
// Stage 3: Seeds after assignInitialActivation
// ============================================================

describe("Stage 3 — Seed assignment", () => {
  it("seeds map contains nodes from FTS5 with correct scores", () => {
    const db = dbHandle.db;
    const ftsResults = fts5Search(db, QUERY);
    const entityHits = findEntityMatches(db, QUERY);
    const seeds = assignInitialActivation(ftsResults, entityHits);

    console.log("\n━━━ Stage 3: Seeds (top 10) ━━━");
    const sorted = [...seeds.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
    for (const [id, score] of sorted) {
      console.log(`  score=${score.toFixed(4)}  [${nodeKey(id)}]`);
    }

    const authJwtInSeeds = seeds.has(seedIds["mlt_auth_jwt"]);
    const jwtValidateInSeeds = seeds.has(seedIds["mlt_jwt_validate"]);
    console.log(`\n  mlt_auth_jwt in seeds    : ${authJwtInSeeds}`);
    console.log(`  mlt_jwt_validate in seeds: ${jwtValidateInSeeds}`);

    expect(seeds.size).toBeGreaterThanOrEqual(0);
  });
});

// ============================================================
// Stage 4: Spreading Activation
// ============================================================

describe("Stage 4 — Spreading activation (Orca)", () => {
  it("spreading activation expands from seeds and includes expected nodes", () => {
    const db = dbHandle.db;
    const ftsResults = fts5Search(db, QUERY);
    const entityHits = findEntityMatches(db, QUERY);
    const seeds = assignInitialActivation(ftsResults, entityHits);

    if (seeds.size === 0) {
      console.log("\n━━━ Stage 4: SKIPPED — no seeds ━━━");
      return;
    }

    const activated = spreadingActivation(seeds, db, {
      maxHops: config.retrievalMaxHops,
      dampingFactor: config.dampingFactor,
      activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
      maxNodes: config.maxNodesPerSearch,
      scopeFilter: GT.scope !== "user" ? GT.scope : undefined,
    });

    console.log("\n━━━ Stage 4: Spreading activation ━━━");
    console.log(`  Seeds: ${seeds.size} → Activated: ${activated.size}`);

    const sorted = [...activated.entries()].sort((a, b) => b[1] - a[1]).slice(0, 15);
    for (const [id, score] of sorted) {
      const isSeed = seeds.has(id) ? " (seed)" : "";
      console.log(`  score=${score.toFixed(4)}  [${nodeKey(id)}]${isSeed}`);
    }

    const authJwtActivated = activated.has(seedIds["mlt_auth_jwt"]);
    const jwtValidateActivated = activated.has(seedIds["mlt_jwt_validate"]);
    console.log(`\n  mlt_auth_jwt activated    : ${authJwtActivated} (score=${activated.get(seedIds["mlt_auth_jwt"])?.toFixed(4) ?? "N/A"})`);
    console.log(`  mlt_jwt_validate activated: ${jwtValidateActivated} (score=${activated.get(seedIds["mlt_jwt_validate"])?.toFixed(4) ?? "N/A"})`);

    expect(activated.size).toBeGreaterThanOrEqual(seeds.size);
  });
});

// ============================================================
// Stage 5: Full Pipeline Output
// ============================================================

describe("Stage 5 — Full pipeline output", () => {
  it("pipeline returns results with ranking details", async () => {
    const db = dbHandle.db;
    const results = await executeRetrievalPipeline(db, QUERY, config, {
      maxResults: 10,
      scopeFilter: GT.scope !== "user" ? GT.scope : undefined,
    });

    const primaryIds = GT.primaryNodeKeys.map((k) => seedIds[k]).filter(Boolean);
    const secondaryIds = GT.secondaryNodeKeys.map((k) => seedIds[k]).filter(Boolean);
    const allExpectedIds = new Set([...primaryIds, ...secondaryIds]);

    console.log("\n━━━ Stage 5: Pipeline final output ━━━");
    console.log(`  Results returned: ${results.length}`);
    for (let i = 0; i < results.length; i++) {
      const nodeId = extractNodeId(results[i].path, db);
      const isExpected = nodeId && allExpectedIds.has(nodeId) ? " ✓ EXPECTED" : "";
      console.log(`  rank=${i + 1}  score=${results[i].score.toFixed(4)}  [${nodeId ? nodeKey(nodeId) : results[i].path}]${isExpected}`);
    }

    const retrievedIds = results.map((r) => extractNodeId(r.path, db)).filter(Boolean) as string[];
    const topKIds = retrievedIds.slice(0, 5);
    const hit = topKIds.some((id) => allExpectedIds.has(id));

    console.log(`\n  Hit@5          : ${hit ? "PASS ✓" : "FAIL ✗"}`);
    console.log(`  Expected nodes : ${[...allExpectedIds].map(nodeKey).join(", ")}`);

    const missing = [...allExpectedIds].filter((id) => !retrievedIds.includes(id));
    if (missing.length > 0) {
      console.log(`  Missing nodes  : ${missing.map(nodeKey).join(", ")}`);
    }
  });

  it("identifies at which stage expected nodes first go missing", async () => {
    const db = dbHandle.db;

    const authJwtId = seedIds["mlt_auth_jwt"];
    const jwtValidateId = seedIds["mlt_jwt_validate"];

    // Stage 1: FTS5
    const ftsResults = fts5Search(db, QUERY);
    const ftsIds = new Set(ftsResults.map((r) => r.nodeId));

    // Stage 3: Seeds
    const entityHits = findEntityMatches(db, QUERY);
    const seeds = assignInitialActivation(ftsResults, entityHits);

    // Stage 4: Activation
    let activated = seeds;
    if (seeds.size > 0) {
      activated = spreadingActivation(seeds, db, {
        maxHops: config.retrievalMaxHops,
        dampingFactor: config.dampingFactor,
        activationThreshold: CONSTANTS.DEFAULT_ACTIVATION_THRESHOLD,
        maxNodes: config.maxNodesPerSearch,
        scopeFilter: undefined,
      });
    }

    // Stage 5: Pipeline
    const results = await executeRetrievalPipeline(db, QUERY, config, { maxResults: 10 });
    const pipelineIds = new Set(
      results.map((r) => extractNodeId(r.path, db)).filter(Boolean) as string[]
    );

    console.log("\n━━━ Stage trace summary ━━━");
    console.log("  Stage → mlt_auth_jwt present? → mlt_jwt_validate present?");
    console.log(`  FTS5 seed     : ${ftsIds.has(authJwtId) ? "YES" : "NO "} | ${ftsIds.has(jwtValidateId) ? "YES" : "NO "}`);
    console.log(`  Seeds (init)  : ${seeds.has(authJwtId) ? "YES" : "NO "} | ${seeds.has(jwtValidateId) ? "YES" : "NO "}`);
    console.log(`  Activation    : ${activated.has(authJwtId) ? "YES" : "NO "} | ${activated.has(jwtValidateId) ? "YES" : "NO "}`);
    console.log(`  Pipeline out  : ${pipelineIds.has(authJwtId) ? "YES" : "NO "} | ${pipelineIds.has(jwtValidateId) ? "YES" : "NO "}`);
    console.log("\n  → Root cause is at the FIRST stage that shows NO.");

    // The test just documents — no strict assertion on pass/fail
    expect(true).toBe(true);
  });
});

// ============================================================
// FTS Diagnostics — direct SQL
// ============================================================

describe("FTS5 direct diagnostics", () => {
  it("manual FTS5 MATCH with the actual generated query returns expected nodes", () => {
    const db = dbHandle.db;
    const ftsQuery = buildFtsQuery(QUERY);
    if (!ftsQuery) return;

    console.log("\n━━━ FTS5 raw MATCH diagnostic ━━━");
    console.log(`  Query: ${ftsQuery}`);

    let rows: Array<{ nodeId: string; rank: number; content: string }> = [];
    try {
      rows = db.prepare(`
        SELECT mn.id as nodeId, rank, mn.content
        FROM memory_nodes_fts fts
        JOIN memory_nodes mn ON mn.rowid = fts.rowid
        WHERE memory_nodes_fts MATCH ?
          AND mn.status = 'active'
        ORDER BY rank
        LIMIT 20
      `).all(ftsQuery) as typeof rows;

      console.log(`  Returned ${rows.length} rows`);
      for (const r of rows) {
        console.log(`  rank=${r.rank.toFixed(3)}  [${nodeKey(r.nodeId)}]  ${r.content.slice(0, 55)}…`);
      }
    } catch (err) {
      console.error(`  FTS MATCH ERROR: ${(err as Error).message}`);
      console.log("  → FTS query syntax is invalid for this content!");
    }

    expect(rows).toBeDefined();
  });

  it("individual token MATCH for JWT and authentication", () => {
    const db = dbHandle.db;
    const tokens = ["JWT", "token", "expiry", "authentication", "24"];

    console.log("\n━━━ Per-token FTS5 MATCH ━━━");
    for (const tok of tokens) {
      try {
        const rows = db.prepare(`
          SELECT mn.id as nodeId
          FROM memory_nodes_fts fts
          JOIN memory_nodes mn ON mn.rowid = fts.rowid
          WHERE memory_nodes_fts MATCH ?
            AND mn.status = 'active'
          ORDER BY rank LIMIT 10
        `).all(`"${tok}"`) as Array<{ nodeId: string }>;

        const nodeKeys = rows.map((r) => nodeKey(r.nodeId)).join(", ");
        console.log(`  "${tok}" → ${rows.length} hits: [${nodeKeys || "none"}]`);
      } catch (err) {
        console.log(`  "${tok}" → ERROR: ${(err as Error).message}`);
      }
    }

    expect(true).toBe(true);
  });
});
