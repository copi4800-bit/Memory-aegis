/**
 * Shared benchmark helpers for Aegis-Bench.
 * Used by test_retrieval_quality_benchmark and test_stress_garbage_flood.
 */

import type Database from "better-sqlite3";
import { executeRetrievalPipeline } from "../../src/retrieval/pipeline.js";
import type { AegisConfig } from "../../src/core/models.js";
import type { MemorySearchResult } from "../../src/retrieval/packet.js";

// ============================================================
// CONSTANTS
// ============================================================

export const K_RECALL = 5;
export const K_MRR = 10;
export const K_NDCG = 10;

// ============================================================
// TYPES
// ============================================================

export interface GroundTruthItem {
  queryId: string;
  query: string;
  scope: string;
  group: "lexical" | "entity" | "graph" | "multiterm" | "anti-leak";
  primaryNodeKeys: string[];
  secondaryNodeKeys: string[];
  forbiddenNodeKeys: string[];
  relevance?: Record<string, number>; // key → grade (1/2/3)
  notes: string;
}

export interface QueryResult {
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

export interface BenchSummary {
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

// ============================================================
// METRICS
// ============================================================

export function computeMRR(retrievedIds: string[], expectedIds: Set<string>, k: number): number {
  for (let rank = 0; rank < Math.min(k, retrievedIds.length); rank++) {
    if (expectedIds.has(retrievedIds[rank])) return 1.0 / (rank + 1);
  }
  return 0;
}

export function computeNDCG(
  retrievedIds: string[],
  expectedIds: Set<string>,
  relevance: Record<string, number>,
  k: number,
): number {
  let dcg = 0;
  for (let rank = 0; rank < Math.min(k, retrievedIds.length); rank++) {
    const id = retrievedIds[rank];
    const rel = relevance[id] ?? (expectedIds.has(id) ? 1 : 0);
    if (rel > 0) dcg += (Math.pow(2, rel) - 1) / Math.log2(rank + 2);
  }

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

export function extractNodeId(resultPath: string, db: Database.Database): string | null {
  if (resultPath.startsWith("aegis://")) {
    const parts = resultPath.split("/");
    return parts[parts.length - 1] ?? null;
  }
  const row = db.prepare(
    "SELECT id FROM memory_nodes WHERE source_path = ? AND status = 'active' LIMIT 1",
  ).get(resultPath) as { id: string } | undefined;
  return row?.id ?? null;
}

export function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[idx];
}

// ============================================================
// QUERY RUNNER
// ============================================================

export async function runQuery(
  db: Database.Database,
  item: GroundTruthItem,
  seedNodeIds: Record<string, string>,
  config: AegisConfig,
  maxResults = Math.max(K_RECALL, K_MRR, K_NDCG),
): Promise<QueryResult> {
  const primaryIds = new Set(item.primaryNodeKeys.map((k) => seedNodeIds[k]).filter(Boolean));
  const secondaryIds = new Set(item.secondaryNodeKeys.map((k) => seedNodeIds[k]).filter(Boolean));
  const forbiddenIds = new Set(item.forbiddenNodeKeys.map((k) => seedNodeIds[k]).filter(Boolean));
  const expectedIds = new Set([...primaryIds, ...secondaryIds]);

  const relevance: Record<string, number> = {};
  if (item.relevance) {
    for (const [key, grade] of Object.entries(item.relevance)) {
      const nodeId = seedNodeIds[key];
      if (nodeId) relevance[nodeId] = grade;
    }
  } else {
    for (const id of primaryIds) relevance[id] = 2;
    for (const id of secondaryIds) relevance[id] = 1;
  }

  const start = performance.now();
  const results: MemorySearchResult[] = await executeRetrievalPipeline(db, item.query, config, {
    maxResults,
    scopeFilter: item.scope !== "user" ? item.scope : undefined,
  });
  const latencyMs = performance.now() - start;

  const retrievedIds: string[] = [];
  const retrievedScopes: string[] = [];

  for (const r of results) {
    const nodeId = extractNodeId(r.path, db);
    if (nodeId) {
      retrievedIds.push(nodeId);
      const row = db.prepare("SELECT scope FROM memory_nodes WHERE id = ?").get(nodeId) as
        | { scope: string }
        | undefined;
      retrievedScopes.push(row?.scope ?? "unknown");
    }
  }

  const topKIds = retrievedIds.slice(0, K_RECALL);
  const hitAtK = topKIds.some((id) => expectedIds.has(id)) ? 1 : 0;
  const relevantInTopK = topKIds.filter((id) => expectedIds.has(id)).length;
  const recallAtK = expectedIds.size > 0 ? relevantInTopK / expectedIds.size : 0;
  const mrrAtK = computeMRR(retrievedIds, expectedIds, K_MRR);
  const ndcgAtK = computeNDCG(retrievedIds, expectedIds, relevance, K_NDCG);

  const topKScopes = retrievedScopes.slice(0, K_RECALL);
  const scopeLeaks = topKScopes.filter((s) => s !== item.scope && s !== "global").length;
  const scopeLeakRate = topKScopes.length > 0 ? scopeLeaks / topKScopes.length : 0;

  const topNdcgIds = retrievedIds.slice(0, K_NDCG);
  const conflictHits = topNdcgIds.filter((id) => forbiddenIds.has(id)).length;
  const conflictLeakRate = topNdcgIds.length > 0 ? conflictHits / topNdcgIds.length : 0;

  return {
    queryId: item.queryId, query: item.query, group: item.group, scope: item.scope,
    expectedIds, primaryIds, forbiddenIds, relevance,
    retrievedIds, retrievedScopes, latencyMs,
    hitAtK, recallAtK, mrrAtK, ndcgAtK, scopeLeakRate, conflictLeakRate,
  };
}

// ============================================================
// SUMMARIZE
// ============================================================

export function summarize(results: QueryResult[]): BenchSummary {
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
    g.hit /= g.count; g.recall /= g.count; g.mrr /= g.count;
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

// ============================================================
// REPORT PRINTER
// ============================================================

export function printReport(summary: BenchSummary, label = "AEGIS-BENCH"): void {
  console.log("\n" + "=".repeat(60));
  console.log(`  ${label}`);
  console.log("=".repeat(60));
  console.log(`Queries : ${summary.queries}`);
  console.log(`Hit@${K_RECALL}    : ${(summary["Hit@5"] * 100).toFixed(1)}%`);
  console.log(`Recall@${K_RECALL} : ${(summary["Recall@5"] * 100).toFixed(1)}%`);
  console.log(`MRR@${K_MRR}   : ${summary["MRR@10"].toFixed(3)}`);
  console.log(`nDCG@${K_NDCG}  : ${summary["nDCG@10"].toFixed(3)}`);
  console.log(`ScopeLeak@${K_RECALL}: ${(summary["ScopeLeakRate@5"] * 100).toFixed(1)}%`);
  console.log(`ConflictLeak@${K_NDCG}: ${(summary["ConflictLeakRate@10"] * 100).toFixed(1)}%`);
  console.log(`Latency p50/p95/mean: ${summary.LatencyP50Ms.toFixed(1)}ms / ${summary.LatencyP95Ms.toFixed(1)}ms / ${summary.LatencyMeanMs.toFixed(1)}ms`);
  console.log("-".repeat(60));
  for (const r of summary.perQuery) {
    const status = r.hitAtK === 1 ? "PASS" : "FAIL";
    console.log(
      `  [${status}] ${r.queryId.padEnd(12)} hit=${r.hitAtK} rcl=${r.recallAtK.toFixed(2)} ` +
      `mrr=${r.mrrAtK.toFixed(2)} ndcg=${r.ndcgAtK.toFixed(2)} ` +
      `leak=${(r.scopeLeakRate*100).toFixed(0)}% cfl=${(r.conflictLeakRate*100).toFixed(0)}% ` +
      `${r.latencyMs.toFixed(0)}ms`
    );
  }
  console.log("=".repeat(60));
}

// ============================================================
// SEED DATA (dùng chung cho cả benchmark lẫn stress test)
// ============================================================

import { ingestChunk } from "../../src/core/ingest.js";

export function seedGroundTruthData(db: Database.Database): Record<string, string> {
  const ids: Record<string, string> = {};

  // Group 1: Lexical
  ids["lex_ts_backend"] = ingestChunk(db, {
    sourcePath: "starproject/backend.md",
    content: "StarProject backend API is built with TypeScript and Express running on Node.js.",
    source: "memory", scope: "user",
  });
  ids["lex_react_frontend"] = ingestChunk(db, {
    sourcePath: "starproject/frontend.md",
    content: "StarProject frontend uses React with Tailwind CSS for the user interface.",
    source: "memory", scope: "user",
  });
  ids["lex_postgres_db"] = ingestChunk(db, {
    sourcePath: "starproject/database.md",
    content: "StarProject uses PostgreSQL as the primary relational database with connection pooling via PgBouncer.",
    source: "memory", scope: "user",
  });

  // Group 2: Entity
  ids["ent_dragonhead_role"] = ingestChunk(db, {
    sourcePath: "starproject/team.md",
    content: "@DragonHead is the lead architect who oversees all technical decisions for StarProject.",
    source: "memory", scope: "user",
  });
  ids["ent_dragonhead_deploy"] = ingestChunk(db, {
    sourcePath: "starproject/ops.md",
    content: "Deployment pipeline for StarProject is managed by @DragonHead using Docker Compose and GitHub Actions.",
    source: "memory", scope: "user",
  });

  // Group 3: Graph
  ids["grp_migration"] = ingestChunk(db, {
    sourcePath: "starproject/migration.md",
    content: "Database migration strategy for StarProject uses Flyway with blue-green deployment to avoid downtime.",
    source: "memory", scope: "user",
  });
  ids["grp_bluegreen"] = ingestChunk(db, {
    sourcePath: "starproject/bluegreen.md",
    content: "Blue-green deployment keeps two identical production environments to enable zero-downtime releases.",
    source: "memory", scope: "user",
  });
  ids["grp_downtime"] = ingestChunk(db, {
    sourcePath: "starproject/sla.md",
    content: "StarProject SLA requires zero downtime for production releases and 99.9% uptime guarantee.",
    source: "memory", scope: "user",
  });

  // Group 4: Multiterm
  ids["mlt_auth_jwt"] = ingestChunk(db, {
    sourcePath: "starproject/auth.md",
    content: "Authentication in StarProject uses JWT tokens that expire after 24 hours for security compliance.",
    source: "memory", scope: "user",
  });
  ids["mlt_jwt_validate"] = ingestChunk(db, {
    sourcePath: "starproject/jwt-validate.md",
    content: "JWT token validation service checks signature, expiry timestamp, and issuer claim before granting access.",
    source: "memory", scope: "user",
  });

  // Group 5: Anti-leak / Conflict
  ids["leak_mongo_other"] = ingestChunk(db, {
    sourcePath: "otherproject/database.md",
    content: "OtherProject uses MongoDB as primary database with Mongoose ODM for document management.",
    source: "memory", scope: "other_project",
  });
  ids["leak_pg_correct"] = ingestChunk(db, {
    sourcePath: "starproject/db-correct.md",
    content: "StarProject database is PostgreSQL. MongoDB is not used anywhere in StarProject infrastructure.",
    source: "memory", scope: "user",
  });
  ids["conflict_old_deploy"] = ingestChunk(db, {
    sourcePath: "starproject/old-ops.md",
    content: "OUTDATED: StarProject deployment was previously done via FTP manually. This is now deprecated.",
    source: "memory", scope: "user",
  });
  // Mark stale
  db.prepare("UPDATE memory_nodes SET status = 'expired' WHERE id = ?").run(ids["conflict_old_deploy"]);

  return ids;
}

export const GROUND_TRUTH: GroundTruthItem[] = [
  {
    queryId: "q_lex_01", query: "TypeScript backend Express API", scope: "user", group: "lexical",
    primaryNodeKeys: ["lex_ts_backend"], secondaryNodeKeys: [], forbiddenNodeKeys: [],
    notes: "Direct FTS5 lexical match",
  },
  {
    queryId: "q_lex_02", query: "React Tailwind CSS frontend", scope: "user", group: "lexical",
    primaryNodeKeys: ["lex_react_frontend"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["lex_ts_backend"],
    notes: "FTS match, backend node is wrong",
  },
  {
    queryId: "q_ent_01", query: "DragonHead architect technical decisions", scope: "user", group: "entity",
    primaryNodeKeys: ["ent_dragonhead_role"], secondaryNodeKeys: ["ent_dragonhead_deploy"],
    forbiddenNodeKeys: [],
    relevance: { ent_dragonhead_role: 3, ent_dragonhead_deploy: 2 },
    notes: "Entity @DragonHead",
  },
  {
    queryId: "q_ent_02", query: "DragonHead deployment Docker", scope: "user", group: "entity",
    primaryNodeKeys: ["ent_dragonhead_deploy"], secondaryNodeKeys: ["ent_dragonhead_role"],
    forbiddenNodeKeys: [],
    relevance: { ent_dragonhead_deploy: 3, ent_dragonhead_role: 1 },
    notes: "Entity + lexical",
  },
  {
    queryId: "q_grp_01", query: "database migration strategy", scope: "user", group: "graph",
    primaryNodeKeys: ["grp_migration"], secondaryNodeKeys: ["grp_bluegreen"],
    forbiddenNodeKeys: [],
    relevance: { grp_migration: 3, grp_bluegreen: 2 },
    notes: "Orca spreading activation",
  },
  {
    queryId: "q_grp_02", query: "zero downtime production release", scope: "user", group: "graph",
    primaryNodeKeys: ["grp_downtime"], secondaryNodeKeys: ["grp_bluegreen", "grp_migration"],
    forbiddenNodeKeys: [],
    relevance: { grp_downtime: 3, grp_bluegreen: 2, grp_migration: 1 },
    notes: "Spreading activation chain",
  },
  {
    queryId: "q_mlt_01", query: "JWT token expiry 24 hours authentication", scope: "user", group: "multiterm",
    primaryNodeKeys: ["mlt_auth_jwt"], secondaryNodeKeys: ["mlt_jwt_validate"],
    forbiddenNodeKeys: [],
    relevance: { mlt_auth_jwt: 3, mlt_jwt_validate: 2 },
    notes: "Multi-keyword",
  },
  {
    queryId: "q_mlt_02", query: "token validation signature issuer", scope: "user", group: "multiterm",
    primaryNodeKeys: ["mlt_jwt_validate"], secondaryNodeKeys: ["mlt_auth_jwt"],
    forbiddenNodeKeys: [],
    relevance: { mlt_jwt_validate: 3, mlt_auth_jwt: 1 },
    notes: "Multi-keyword validation",
  },
  {
    queryId: "q_leak_01", query: "StarProject database PostgreSQL", scope: "user", group: "anti-leak",
    primaryNodeKeys: ["leak_pg_correct", "lex_postgres_db"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["leak_mongo_other"],
    relevance: { leak_pg_correct: 3, lex_postgres_db: 2 },
    notes: "Scope leakage guard",
  },
  {
    queryId: "q_leak_02", query: "StarProject deployment operations", scope: "user", group: "anti-leak",
    primaryNodeKeys: ["ent_dragonhead_deploy"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["conflict_old_deploy"],
    notes: "Conflict/expired node guard",
  },
];

// ============================================================
// EXTENDED SEED DATA — cross-scope traps, near-topic, temporal
// ============================================================

export function seedExtendedData(
  db: Database.Database,
  baseIds: Record<string, string>,
): Record<string, string> {
  const ids: Record<string, string> = { ...baseIds };

  // --- Cross-scope traps: same keywords, different project ---
  ids["xscope_ts_fastify"] = ingestChunk(db, {
    sourcePath: "anotherproject/backend.md",
    content: "AnotherProject backend API is built with TypeScript and Fastify framework running on Node.js.",
    source: "memory", scope: "another_project",
  });
  ids["xscope_pg_infra"] = ingestChunk(db, {
    sourcePath: "infraproject/database.md",
    content: "InfraProject database cluster runs PostgreSQL 15 with Patroni for high availability and failover.",
    source: "memory", scope: "infra_project",
  });
  ids["xscope_auth_oauth"] = ingestChunk(db, {
    sourcePath: "otherproject/auth.md",
    content: "OtherProject authentication uses OAuth2 with JWT access tokens that expire after 1 hour.",
    source: "memory", scope: "other_project",
  });
  ids["xscope_k8s_infra"] = ingestChunk(db, {
    sourcePath: "infraproject/deployment.md",
    content: "InfraProject deployment uses Kubernetes with Helm charts and ArgoCD for production container orchestration.",
    source: "memory", scope: "infra_project",
  });

  // --- Near-topic traps: same project, adjacent topic ---
  ids["near_testing"] = ingestChunk(db, {
    sourcePath: "starproject/testing.md",
    content: "StarProject uses Vitest for unit testing and Playwright for end-to-end browser testing.",
    source: "memory", scope: "user",
  });
  ids["near_caching"] = ingestChunk(db, {
    sourcePath: "starproject/caching.md",
    content: "StarProject uses Redis for session caching and API rate limiting to improve backend performance.",
    source: "memory", scope: "user",
  });
  ids["near_logging"] = ingestChunk(db, {
    sourcePath: "starproject/logging.md",
    content: "StarProject backend uses Winston for structured JSON logging with log rotation and severity levels.",
    source: "memory", scope: "user",
  });
  ids["near_monitoring"] = ingestChunk(db, {
    sourcePath: "starproject/monitoring.md",
    content: "StarProject production monitoring uses Prometheus metrics scraped by Grafana dashboards for alerts.",
    source: "memory", scope: "user",
  });

  // --- Temporal traps: outdated vs. current ---
  ids["temporal_old_auth"] = ingestChunk(db, {
    sourcePath: "starproject/auth-v1.md",
    content: "DEPRECATED: StarProject v1 used cookie-based sessions stored in Redis for user authentication.",
    source: "memory", scope: "user",
  });
  db.prepare("UPDATE memory_nodes SET status = 'expired' WHERE id = ?").run(ids["temporal_old_auth"]);

  ids["temporal_new_k8s"] = ingestChunk(db, {
    sourcePath: "starproject/deployment-v3.md",
    content: "StarProject v3 deployment migrated to Kubernetes replacing Docker Compose for production container management.",
    source: "memory", scope: "user",
  });

  ids["temporal_old_mysql"] = ingestChunk(db, {
    sourcePath: "starproject/database-v1.md",
    content: "DEPRECATED: StarProject originally used MySQL as the primary database before migrating to PostgreSQL.",
    source: "memory", scope: "user",
  });
  db.prepare("UPDATE memory_nodes SET status = 'expired' WHERE id = ?").run(ids["temporal_old_mysql"]);

  return ids;
}

// ============================================================
// EXTENDED GROUND TRUTH — 10 additional queries
// Groups: cross-scope (4), near-topic (3), temporal (3)
// ============================================================

export const EXTENDED_GROUND_TRUTH: GroundTruthItem[] = [
  // --- cross-scope: same keywords, answer must stay in user scope ---
  {
    queryId: "q_xscope_01",
    query: "TypeScript Express Node.js backend API",
    scope: "user", group: "cross-scope",
    primaryNodeKeys: ["lex_ts_backend"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["xscope_ts_fastify"],
    relevance: { lex_ts_backend: 3 },
    notes: "Express/user vs Fastify/another_project — same language, different framework and scope",
  },
  {
    queryId: "q_xscope_02",
    query: "PostgreSQL relational database connection pooling",
    scope: "user", group: "cross-scope",
    primaryNodeKeys: ["lex_postgres_db"], secondaryNodeKeys: ["leak_pg_correct"],
    forbiddenNodeKeys: ["xscope_pg_infra"],
    relevance: { lex_postgres_db: 3, leak_pg_correct: 2 },
    notes: "User PostgreSQL vs infra_project PostgreSQL cluster — keyword overlap, different scope",
  },
  {
    queryId: "q_xscope_03",
    query: "JWT token authentication expire security",
    scope: "user", group: "cross-scope",
    primaryNodeKeys: ["mlt_auth_jwt"], secondaryNodeKeys: ["mlt_jwt_validate"],
    forbiddenNodeKeys: ["xscope_auth_oauth"],
    relevance: { mlt_auth_jwt: 3, mlt_jwt_validate: 2 },
    notes: "User JWT (24h) vs other_project JWT OAuth2 (1h) — same token type, different project",
  },
  {
    queryId: "q_xscope_04",
    query: "Docker Compose GitHub Actions deployment pipeline",
    scope: "user", group: "cross-scope",
    primaryNodeKeys: ["ent_dragonhead_deploy"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["xscope_k8s_infra"],
    relevance: { ent_dragonhead_deploy: 3 },
    notes: "Docker Compose/user vs Kubernetes/infra_project — both deployment, different scope",
  },

  // --- near-topic: same project, adjacent topic is a trap ---
  {
    queryId: "q_near_01",
    query: "StarProject backend structured JSON logging",
    scope: "user", group: "near-topic",
    primaryNodeKeys: ["near_logging"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["near_monitoring", "near_testing"],
    relevance: { near_logging: 3 },
    notes: "Logging is specific; monitoring (Prometheus/Grafana) and testing are adjacent traps",
  },
  {
    queryId: "q_near_02",
    query: "StarProject production metrics Prometheus Grafana",
    scope: "user", group: "near-topic",
    primaryNodeKeys: ["near_monitoring"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["near_logging", "near_testing"],
    relevance: { near_monitoring: 3 },
    notes: "Monitoring is specific; logging (Winston) is an adjacent near-topic trap",
  },
  {
    queryId: "q_near_03",
    query: "StarProject Redis session cache rate limit",
    scope: "user", group: "near-topic",
    primaryNodeKeys: ["near_caching"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["temporal_old_auth"],
    relevance: { near_caching: 3 },
    notes: "Current Redis caching vs expired auth-v1 that also mentioned Redis sessions",
  },

  // --- temporal: must prefer current node, expired node must not appear ---
  {
    queryId: "q_temp_01",
    query: "StarProject user authentication current implementation",
    scope: "user", group: "temporal",
    primaryNodeKeys: ["mlt_auth_jwt", "mlt_jwt_validate"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["temporal_old_auth"],
    relevance: { mlt_auth_jwt: 3, mlt_jwt_validate: 2 },
    notes: "JWT (active) must rank above cookie-session auth (expired) — temporal correctness",
  },
  {
    queryId: "q_temp_02",
    query: "StarProject primary database relational",
    scope: "user", group: "temporal",
    primaryNodeKeys: ["lex_postgres_db", "leak_pg_correct"], secondaryNodeKeys: [],
    forbiddenNodeKeys: ["temporal_old_mysql"],
    relevance: { lex_postgres_db: 3, leak_pg_correct: 2 },
    notes: "PostgreSQL (active) vs MySQL (expired) — expired migration history must not appear",
  },
  {
    queryId: "q_temp_03",
    query: "StarProject container deployment Kubernetes",
    scope: "user", group: "temporal",
    primaryNodeKeys: ["temporal_new_k8s"], secondaryNodeKeys: ["ent_dragonhead_deploy"],
    forbiddenNodeKeys: ["conflict_old_deploy"],
    relevance: { temporal_new_k8s: 3, ent_dragonhead_deploy: 1 },
    notes: "New K8s migration (active/user) vs FTP deprecated (expired) — pure temporal correctness test",
  },
];
