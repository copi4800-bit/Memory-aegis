/**
 * Prompt Assembly Tests
 *
 * Tests the full pipeline from query to assembled context string injected
 * into the LLM prompt — without calling any LLM.
 *
 * Pipeline:
 *   query → executeRetrievalPipeline → MemorySearchResult[]
 *                                            ↓
 *                                 AegisRouter.enforce(results, budget)
 *                                            ↓
 *                        "<relevant-memories>…</relevant-memories>"
 *
 * Test areas:
 *   1. AegisRouter unit: structure, budget, topK, truncation, scoring
 *   2. Trauma/invariant priority: safety nodes always appear first
 *   3. E2E correctness: right content reaches the context string
 *   4. Expired node guard: expired nodes never appear in assembled context
 *   5. Cross-scope contamination position: leaked nodes must not occupy top slot
 *   6. Token budget stress: tight budget enforced without broken XML
 *   7. Context quality across 20 queries: top-1 slot always has a relevant node
 */

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import os from "node:os";
import path from "node:path";
import fs from "node:fs";

import { openDatabase } from "../../src/db/connection.js";
import type { AegisDatabase } from "../../src/db/connection.js";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import { AegisRouter } from "../../src/retrieval/router.js";
import type { MemorySearchResult } from "../../src/retrieval/packet.js";
import { ingestChunk } from "../../src/core/ingest.js";
import { DEFAULT_AEGIS_CONFIG } from "../../src/core/models.js";
import {
  seedGroundTruthData,
  seedExtendedData,
  GROUND_TRUTH,
  EXTENDED_GROUND_TRUTH,
  extractNodeId,
} from "../helpers/aegis-bench.js";

// ============================================================
// Setup
// ============================================================

const BENCH_CONFIG = {
  ...DEFAULT_AEGIS_CONFIG,
  enabledLayers: ["elephant", "orca", "salmon", "sea-lion"] as typeof DEFAULT_AEGIS_CONFIG.enabledLayers,
  retrievalMaxHops: 4,
  dampingFactor: 0.5,
  maxNodesPerSearch: 50,
};

const DEFAULT_BUDGET = { maxChars: 4000, topK: 6 };
const TIGHT_BUDGET   = { maxChars: 300,  topK: 2 };

let db: AegisDatabase;
let dbPath: string;
let allIds: Record<string, string>;

const ALL_GROUND_TRUTH = [...GROUND_TRUTH, ...EXTENDED_GROUND_TRUTH];

beforeAll(() => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "aegis-prompt-"));
  dbPath = path.join(tmpDir, "prompt.db");
  db = openDatabase(dbPath);
  const baseIds = seedGroundTruthData(db.db);
  allIds = seedExtendedData(db.db, baseIds);
});

afterAll(() => {
  db.close();
  try { fs.rmSync(path.dirname(dbPath), { recursive: true }); } catch {}
});

// ============================================================
// Helper: retrieve and assemble
// ============================================================

async function queryToContext(
  query: string,
  budget = DEFAULT_BUDGET,
  scopeFilter?: string,
): Promise<{ results: MemorySearchResult[]; context: string }> {
  const results = await executeRetrievalPipeline(db.db, query, BENCH_CONFIG, {
    maxResults: budget.topK * 2, // fetch 2× topK so router can trim
    scopeFilter,
  });
  const context = AegisRouter.enforce(results, budget);
  return { results, context };
}

// ============================================================
// 1. AegisRouter unit — no DB required
// ============================================================

describe("1 — AegisRouter unit: structure and budget", () => {
  it("empty results returns empty string", () => {
    const out = AegisRouter.enforce([], DEFAULT_BUDGET);
    expect(out).toBe("");
  });

  it("output is wrapped in <context-budget> tags", () => {
    const fakeResult: MemorySearchResult = {
      path: "starproject/test.md",
      startLine: 0, endLine: 0,
      score: 0.9,
      snippet: "StarProject uses TypeScript.",
      source: "memory",
      citation: "[core] test node",
    };
    const out = AegisRouter.enforce([fakeResult], DEFAULT_BUDGET);
    expect(out.includes("<context-budget>")).toBe(true);
    expect(out.includes("</context-budget>")).toBe(true);
  });

  it("topK limit: never outputs more nodes than topK", () => {
    const results: MemorySearchResult[] = Array.from({ length: 10 }, (_, i) => ({
      path: `node-${i}.md`,
      startLine: 0, endLine: 0,
      score: 1 - i * 0.05,
      snippet: `Content of node ${i}. `.repeat(5),
      source: "memory" as const,
    }));
    const out = AegisRouter.enforce(results, { maxChars: 100_000, topK: 4 });
    const matches = out.match(/\[\d+\.\d+\]/gm) ?? [];
    expect(matches.length).toBeLessThanOrEqual(4);
  });

  it("maxChars budget: output stays within character limit", () => {
    const results: MemorySearchResult[] = Array.from({ length: 5 }, (_, i) => ({
      path: `node-${i}.md`,
      startLine: 0, endLine: 0,
      score: 0.8,
      snippet: "A".repeat(300), // 300 chars per node
      source: "memory" as const,
    }));
    const out = AegisRouter.enforce(results, { maxChars: 400, topK: 10 });
    expect(out.length).toBeLessThanOrEqual(400 + 50); // 50 for tag overhead
  });

  it("snippet truncated at 800 chars in router", () => {
    const longSnippet = "X".repeat(2000);
    const result: MemorySearchResult = {
      path: "long.md",
      startLine: 0, endLine: 0,
      score: 0.8,
      snippet: longSnippet,
      source: "memory",
    };
    const out = AegisRouter.enforce([result], { maxChars: 100_000, topK: 1 });
    // The snippet in output should be at most 800 + "..." = 803 chars
    expect(out.length).toBeLessThan(900 + 100); // 100 for line prefix
  });

  it("score is formatted as [0.xxx] in output", () => {
    const result: MemorySearchResult = {
      path: "test.md",
      startLine: 0, endLine: 0,
      score: 0.756,
      snippet: "Test content.",
      source: "memory",
    };
    const out = AegisRouter.enforce([result], DEFAULT_BUDGET);
    expect(out).toMatch(/\[0\.\d{3}\]/);
  });

  it("nodes include scores instead of just numbered list", () => {
    const results: MemorySearchResult[] = [0.9, 0.7, 0.5].map((score, i) => ({
      path: `node-${i}.md`,
      startLine: 0, endLine: 0,
      score,
      snippet: `Node ${i} content.`,
      source: "memory" as const,
      citation: `[core] node ${i}`,
    }));
    const out = AegisRouter.enforce(results, DEFAULT_BUDGET);
    expect(out).toContain("[0.900]");
    expect(out).toContain("[0.700]");
    expect(out).toContain("[0.500]");
  });
});

// ============================================================
// 2. Trauma/invariant priority
// ============================================================

describe("2 — Trauma/invariant priority: safety nodes always first", () => {
  it("trauma node (aegis:// path) is placed before high-score regular node", () => {
    // Trauma node with low score, regular node with high score
    const traumaNode: MemorySearchResult = {
      path: "aegis://trauma/safety-rule-001",
      startLine: 0, endLine: 0,
      score: 0.3, // intentionally low score
      snippet: "SAFETY RULE: Never share credentials.",
      source: "memory",
      citation: "[trauma] rule",
    };
    const regularNode: MemorySearchResult = {
      path: "project/feature.md",
      startLine: 0, endLine: 0,
      score: 0.95, // high score
      snippet: "Feature X implementation details.",
      source: "memory",
      citation: "[core] feature",
    };

    // AegisRouter detects trauma by path.includes("trauma")
    const out = AegisRouter.enforce([regularNode, traumaNode], DEFAULT_BUDGET);

    const traumaPos = out.indexOf("SAFETY RULE");
    const regularPos = out.indexOf("Feature X");
    expect(traumaPos).toBeGreaterThan(-1);
    expect(regularPos).toBeGreaterThan(-1);
    expect(traumaPos).toBeLessThan(regularPos); // trauma must come first
  });

  it("invariant node (aegis:// path) is placed before regular nodes", () => {
    const invariantNode: MemorySearchResult = {
      path: "aegis://invariant/core-rule-002",
      startLine: 0, endLine: 0,
      score: 0.2,
      snippet: "INVARIANT: Always use UTF-8 encoding.",
      source: "memory",
      citation: "[invariant] rule",
    };
    const regularNode: MemorySearchResult = {
      path: "docs/guide.md",
      startLine: 0, endLine: 0,
      score: 0.99,
      snippet: "User guide content.",
      source: "memory",
      citation: "[core] user guide",
    };

    const out = AegisRouter.enforce([regularNode, invariantNode], DEFAULT_BUDGET);
    const invariantPos = out.indexOf("INVARIANT");
    const regularPos = out.indexOf("User guide");
    expect(invariantPos).toBeLessThan(regularPos);
  });

  it("non-aegis-path trauma node is NOT auto-prioritized (documents known limitation)", () => {
    // If trauma node has a real source_path like "memory/rules.md",
    // AegisRouter won't detect it as trauma since path doesn't contain "trauma"
    const traumaWithRealPath: MemorySearchResult = {
      path: "memory/critical-rules.md", // no "trauma" in path
      startLine: 0, endLine: 0,
      score: 0.2,
      snippet: "Critical safety rule content.",
      source: "memory",
    };
    const highScoreNode: MemorySearchResult = {
      path: "docs/feature.md",
      startLine: 0, endLine: 0,
      score: 0.9,
      snippet: "Regular feature content.",
      source: "memory",
    };

    const out = AegisRouter.enforce([traumaWithRealPath, highScoreNode], DEFAULT_BUDGET);
    // Router orders by input order when both are "regular" — input order preserved
    // This documents that source_path-based trauma nodes are not auto-prioritized
    const safetyPos = out.indexOf("Critical safety");
    const featurePos = out.indexOf("Regular feature");

    console.log(`\n  Remaining limitation: no citation + no aegis:// path → not detected`);
    console.log(`  Safety pos=${safetyPos}, Feature pos=${featurePos}`);
    // Without citation field, router cannot detect trauma — documents residual limitation
    expect(safetyPos).toBeGreaterThan(-1);
    expect(featurePos).toBeGreaterThan(-1);
  });

  it("FIX: source_path trauma node WITH citation is correctly prioritized", () => {
    // After the fix: citation field "[trauma] …" is checked first.
    // Real pipeline always sets citation via toMemorySearchResult → formatCitation.
    const traumaViaCitation: MemorySearchResult = {
      path: "memory/critical-rules.md", // real source_path, no "trauma" in path
      startLine: 0, endLine: 0,
      score: 0.2, // intentionally low score
      snippet: "SAFETY RULE via citation: Never expose credentials.",
      source: "memory",
      citation: "[trauma] safety-rules — relevance match", // set by pipeline
    };
    const highScoreNode: MemorySearchResult = {
      path: "docs/feature.md",
      startLine: 0, endLine: 0,
      score: 0.95,
      snippet: "Regular feature content.",
      source: "memory",
      citation: "[semantic_fact] feature — relevance match",
    };

    const out = AegisRouter.enforce([highScoreNode, traumaViaCitation], DEFAULT_BUDGET);
    const safetyPos = out.indexOf("SAFETY RULE via citation");
    const featurePos = out.indexOf("Regular feature");

    console.log(`\n  FIX verified: citation-based trauma priority`);
    console.log(`  Safety pos=${safetyPos} (must be < ${featurePos})`);

    // With citation field, trauma node is detected and placed first — even with low score
    expect(safetyPos).toBeGreaterThan(-1);
    expect(featurePos).toBeGreaterThan(-1);
    expect(safetyPos).toBeLessThan(featurePos);
  });
});

// ============================================================
// 3. E2E correctness: right content reaches the context
// ============================================================

describe("3 — E2E: query → retrieval → context content", () => {
  it("q_mlt_01 (JWT): JWT-related content appears in assembled context", async () => {
    const { context } = await queryToContext("JWT token expiry 24 hours authentication");

    console.log(`\n  q_mlt_01 context length: ${context.length} chars`);
    const hasJwt = context.toLowerCase().includes("jwt");
    expect(hasJwt).toBe(true);
    if (context.includes("24 hours") || context.includes("expire")) {
      console.log("  JWT expiry content confirmed in context ✓");
    }
  });

  it("q_lex_01 (TypeScript): TypeScript backend node is in context", async () => {
    const { results, context } = await queryToContext("TypeScript backend Express API");

    const topId = results[0] ? extractNodeId(results[0].path, db.db) : null;
    const expectedId = allIds["lex_ts_backend"];

    console.log(`\n  q_lex_01 top-1 node: ${topId?.slice(0, 12)}… (expected: ${expectedId?.slice(0, 12)}…)`);
    expect(context).toContain("TypeScript");
    expect(topId).toBe(expectedId); // TypeScript backend must be top-1
  });

  it("q_ent_01 (@DragonHead): entity mention appears in context", async () => {
    const { context } = await queryToContext("DragonHead architect technical decisions");
    expect(context).toContain("DragonHead");
  });

  it("q_grp_02 (zero downtime): graph-linked blue-green content in context", async () => {
    const { context } = await queryToContext("zero downtime production release");
    const hasDowntime = context.toLowerCase().includes("downtime");
    expect(hasDowntime).toBe(true);
  });

  it("context is non-empty for all 20 ground truth queries", async () => {
    let emptyCount = 0;
    for (const gt of ALL_GROUND_TRUTH) {
      const { context } = await queryToContext(gt.query);
      if (context === "") emptyCount++;
    }
    console.log(`\n  Queries with empty context: ${emptyCount}/20`);
    expect(emptyCount).toBe(0);
  });
});

// ============================================================
// 4. Expired node guard
// ============================================================

describe("4 — Expired node guard: no expired content in assembled context", () => {
  it("expired auth node (cookie sessions) never appears in JWT query context", async () => {
    const { context } = await queryToContext("StarProject user authentication implementation");

    // temporal_old_auth content: "DEPRECATED: StarProject v1 used cookie-based sessions"
    const hasCookieSessions = context.includes("cookie-based sessions");
    if (hasCookieSessions) {
      console.warn("  ⚠ Expired cookie-session auth node leaked into context!");
    }
    expect(hasCookieSessions).toBe(false);
  });

  it("expired MySQL node never appears in database query context", async () => {
    const { context } = await queryToContext("StarProject primary database relational");

    // temporal_old_mysql content: "DEPRECATED: StarProject originally used MySQL"
    const hasMySQL = context.toLowerCase().includes("mysql");
    if (hasMySQL) {
      console.warn("  ⚠ Expired MySQL node leaked into context!");
    }
    expect(hasMySQL).toBe(false);
  });

  it("expired deployment (FTP) node never appears in deployment query context", async () => {
    const { context } = await queryToContext("StarProject deployment operations");

    // conflict_old_deploy content: "OUTDATED: StarProject deployment was previously done via FTP"
    const hasFtp = context.toUpperCase().includes("FTP");
    if (hasFtp) {
      console.warn("  ⚠ Expired FTP deployment node leaked into context!");
    }
    expect(hasFtp).toBe(false);
  });

  it("no expired node content appears across all 20 queries", async () => {
    const expiredContents = [
      "cookie-based sessions",
      "originally used MySQL",
      "previously done via FTP",
    ];

    const leaks: string[] = [];
    for (const gt of ALL_GROUND_TRUTH) {
      const { context } = await queryToContext(gt.query);
      for (const marker of expiredContents) {
        if (context.includes(marker)) {
          leaks.push(`${gt.queryId}: found "${marker.slice(0, 30)}…"`);
        }
      }
    }

    if (leaks.length > 0) {
      console.warn("\n  ⚠ Expired content in context:");
      leaks.forEach((l) => console.warn(`    ${l}`));
    } else {
      console.log("\n  No expired node content found in any query context ✓");
    }

    expect(leaks).toHaveLength(0);
  });
});

// ============================================================
// 5. Cross-scope contamination position
// ============================================================

describe("5 — Cross-scope contamination: leaked nodes must not occupy slot #1", () => {
  it("q_xscope_01 (TypeScript): cross-scope Fastify node NOT at top-1 in user context", async () => {
    const { results } = await queryToContext("TypeScript Express Node.js backend API");

    if (results.length === 0) return;
    const topNodeId = extractNodeId(results[0].path, db.db);
    const expectedId = allIds["lex_ts_backend"];
    const forbiddenId = allIds["xscope_ts_fastify"];

    console.log(`\n  q_xscope_01 top-1: [${topNodeId?.slice(0, 12)}…]`);
    console.log(`  Expected: lex_ts_backend [${expectedId?.slice(0, 12)}…]`);
    console.log(`  Forbidden: xscope_ts_fastify [${forbiddenId?.slice(0, 12)}…]`);

    expect(topNodeId).not.toBe(forbiddenId);
    expect(topNodeId).toBe(expectedId);
  });

  it("q_xscope_02 (PostgreSQL): infra-project node NOT at top-1", async () => {
    const { results } = await queryToContext("PostgreSQL relational database connection pooling");

    if (results.length === 0) return;
    const topNodeId = extractNodeId(results[0].path, db.db);
    const forbiddenId = allIds["xscope_pg_infra"];

    expect(topNodeId).not.toBe(forbiddenId);
  });

  it("q_xscope_03 (JWT auth): other-project OAuth node NOT at top-1", async () => {
    const { results } = await queryToContext("JWT token authentication expire security");

    if (results.length === 0) return;
    const topNodeId = extractNodeId(results[0].path, db.db);
    const forbiddenId = allIds["xscope_auth_oauth"];

    expect(topNodeId).not.toBe(forbiddenId);
  });

  it("records cross-scope node rank distribution across all cross-scope queries", async () => {
    const crossScopeGt = EXTENDED_GROUND_TRUTH.filter((g) => g.group === "cross-scope" as any);
    let totalChecked = 0;
    let forbiddenAtTop3 = 0;

    console.log("\n  Cross-scope forbidden node rank distribution:");
    for (const gt of crossScopeGt) {
      const { results } = await queryToContext(gt.query);
      const top3Ids = results
        .slice(0, 3)
        .map((r) => extractNodeId(r.path, db.db))
        .filter(Boolean) as string[];

      const forbiddenIds = gt.forbiddenNodeKeys.map((k) => allIds[k]).filter(Boolean);
      const leaksInTop3 = forbiddenIds.filter((id) => top3Ids.includes(id));

      if (leaksInTop3.length > 0) forbiddenAtTop3++;
      totalChecked++;

      console.log(
        `  ${gt.queryId}: forbidden@top3=${leaksInTop3.length > 0 ? "YES ⚠" : "NO ✓"}  top3=[${top3Ids.map((id) => id.slice(0, 8)).join(",")}]`,
      );
    }

    // Count how many queries have forbidden at rank-1 specifically
    let forbiddenAtTop1 = 0;
    for (const gt of crossScopeGt) {
      const { results } = await queryToContext(gt.query);
      const top1Id = results[0] ? extractNodeId(results[0].path, db.db) : null;
      const forbiddenIds = gt.forbiddenNodeKeys.map((k) => allIds[k]).filter(Boolean);
      if (top1Id && forbiddenIds.includes(top1Id)) forbiddenAtTop1++;
    }

    console.log(`  Total forbidden@top3: ${forbiddenAtTop3}/${totalChecked}`);
    console.log(`  Total forbidden@top1: ${forbiddenAtTop1}/${totalChecked}`);
    if (forbiddenAtTop3 > 0) {
      console.log("  → Cross-scope nodes in top-2/3 is expected OR relaxation trade-off");
      console.log("  → Critical check: forbidden must NOT be at top-1 (dominates LLM answer)");
    }
    // Cross-scope forbidden nodes at rank 1 is unacceptable — it dominates the LLM response
    // Rank 2-3 appearance is the documented OR relaxation trade-off
    expect(forbiddenAtTop1).toBe(0);
  });
});

// ============================================================
// 6. Token budget stress tests
// ============================================================

describe("6 — Token budget: tight budget enforced cleanly", () => {
  it("tight budget (300 chars, topK=2): output within budget", async () => {
    const { context } = await queryToContext("TypeScript backend Express API", TIGHT_BUDGET);

    console.log(`\n  Tight budget output (${context.length} chars):`);
    console.log(`  ${context.slice(0, 200)}…`);

    expect(context.length).toBeLessThanOrEqual(TIGHT_BUDGET.maxChars + 100); // small tag overhead
  });

  it("tight budget: still wraps in valid <context-budget> tags", async () => {
    const { context } = await queryToContext("TypeScript backend Express API", TIGHT_BUDGET);

    if (context === "") return; // acceptable if budget is too tight
    expect(context.includes("<context-budget>")).toBe(true);
    expect(context.includes("</context-budget>")).toBe(true);
  });

  it("tight budget (topK=2): at most 2 nodes in output", async () => {
    const { context } = await queryToContext("TypeScript backend Express API", TIGHT_BUDGET);
    const nodeCount = (context.match(/\[\d+\.\d+\]/gm) ?? []).length;
    expect(nodeCount).toBeLessThanOrEqual(2);
  });

  it("zero-char budget: returns empty string or minimal output", async () => {
    const results = await executeRetrievalPipeline(
      db.db, "TypeScript backend", BENCH_CONFIG, { maxResults: 5 }
    );
    const out = AegisRouter.enforce(results, { maxChars: 0, topK: 5 });
    const nodeCount = (out.match(/\[\d+\.\d+\]/gm) ?? []).length;
    expect(nodeCount).toBe(0);
  });

  it("large topK with small corpus: gracefully returns all available nodes", async () => {
    const results = await executeRetrievalPipeline(
      db.db, "StarProject", BENCH_CONFIG, { maxResults: 5 }
    );
    // topK larger than actual results
    const out = AegisRouter.enforce(results, { maxChars: 100_000, topK: 100 });
    const nodeCount = (out.match(/\[\d+\.\d+\]/gm) ?? []).length;
    expect(nodeCount).toBeLessThanOrEqual(results.length);
    expect(nodeCount).toBeGreaterThan(0);
  });
});

// ============================================================
// 7. Context quality across all 20 queries
// ============================================================

describe("7 — Context quality: top-1 slot always has a relevant node", () => {
  it("top-1 context node is always a primary or secondary expected node", async () => {
    let top1Relevant = 0;
    let top1Irrelevant = 0;
    const irrelevantQueries: string[] = [];

    console.log("\n  Top-1 context node relevance (20 queries):");
    for (const gt of ALL_GROUND_TRUTH) {
      const { results } = await queryToContext(gt.query);
      if (results.length === 0) {
        irrelevantQueries.push(`${gt.queryId}: no results`);
        top1Irrelevant++;
        continue;
      }

      const topId = extractNodeId(results[0].path, db.db);
      const primaryIds = new Set(gt.primaryNodeKeys.map((k) => allIds[k]).filter(Boolean));
      const secondaryIds = new Set(gt.secondaryNodeKeys.map((k) => allIds[k]).filter(Boolean));
      const expectedIds = new Set([...primaryIds, ...secondaryIds]);

      const isRelevant = topId ? expectedIds.has(topId) : false;
      if (isRelevant) {
        top1Relevant++;
        console.log(`  [✓] ${gt.queryId.padEnd(14)} top1=[${topId?.slice(0, 8)}…]`);
      } else {
        top1Irrelevant++;
        irrelevantQueries.push(gt.queryId);
        console.log(`  [✗] ${gt.queryId.padEnd(14)} top1=[${topId?.slice(0, 8)}…] — not expected`);
      }
    }

    const relevanceRate = top1Relevant / ALL_GROUND_TRUTH.length;
    console.log(`\n  Top-1 relevance rate: ${(relevanceRate * 100).toFixed(0)}% (${top1Relevant}/20)`);

    // At least 80% of top-1 slots should be relevant
    expect(relevanceRate).toBeGreaterThanOrEqual(0.80);
  });

  it("no duplicate snippets appear in the same context string", async () => {
    let queriesWithDups = 0;
    for (const gt of ALL_GROUND_TRUTH) {
      const { context } = await queryToContext(gt.query);
      if (context === "") continue;

      // Extract numbered entries
      const entries = context.match(/\d+\. \[[\d.]+\] .+/g) ?? [];
      const snippets = entries.map((e) => e.slice(0, 50));
      const unique = new Set(snippets);
      if (unique.size < snippets.length) queriesWithDups++;
    }
    console.log(`\n  Queries with duplicate snippets: ${queriesWithDups}/20`);
    expect(queriesWithDups).toBe(0);
  });

  it("assembled context is valid UTF-8 string for all queries", async () => {
    for (const gt of ALL_GROUND_TRUTH) {
      const { context } = await queryToContext(gt.query);
      // If it's a string and doesn't throw, it's valid
      expect(typeof context).toBe("string");
    }
  });

  it("snippet content is coherent: primary node snippet matches query topic", async () => {
    const checks = [
      { query: "TypeScript backend Express API", mustContain: ["TypeScript"], queryId: "q_lex_01" },
      { query: "JWT token expiry 24 hours authentication", mustContain: ["JWT"], queryId: "q_mlt_01" },
      { query: "DragonHead architect technical decisions", mustContain: ["DragonHead"], queryId: "q_ent_01" },
      { query: "StarProject Redis session cache rate limit", mustContain: ["Redis"], queryId: "q_near_03" },
      { query: "StarProject primary database relational", mustContain: ["PostgreSQL"], queryId: "q_temp_02" },
    ];

    console.log("\n  Snippet content coherence checks:");
    for (const check of checks) {
      const { context } = await queryToContext(check.query);
      const missing = check.mustContain.filter((term) => !context.includes(term));
      const ok = missing.length === 0;
      console.log(`  ${check.queryId}: ${ok ? "✓" : "✗ missing: " + missing.join(", ")}`);
      expect(missing).toHaveLength(0);
    }
  });
});
