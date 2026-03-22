#!/usr/bin/env npx tsx
/**
 * Phase 6.1 — Public Benchmark Pack
 *
 * Chạy toàn bộ benchmark suite và xuất kết quả JSON + human-readable report.
 *
 * Usage: npx tsx benchmark/run-all.ts [--json] [--output <path>]
 *
 * Benchmarks included:
 * 1. Retrieval Quality (Hit@5, Recall@5, MRR@10, nDCG@10)
 * 2. Scope Leak & Conflict Leak
 * 3. Dragonfly Semantic Rescue
 * 4. Bowerbird Taxonomy Classification
 * 5. Weaver Bird Procedural Extraction
 * 6. Chameleon Context Budgeting
 * 7. Latency Profile
 */

import { AegisMemoryManager, closeAllManagers } from "../src/aegis-manager.js";
import { DEFAULT_AEGIS_CONFIG } from "../src/core/models.js";
import { resolve } from "node:path";
import fs from "node:fs";
import {
  seedGroundTruthData,
  seedExtendedData,
  GROUND_TRUTH,
  EXTENDED_GROUND_TRUTH,
  runQuery,
  summarize,
  printReport,
} from "../test/helpers/aegis-bench.js";
import { BowerbirdTaxonomist } from "../src/cognitive/bowerbird.js";
import { DragonflySentry } from "../src/retrieval/dragonfly.js";
import { WeaverBird } from "../src/cognitive/weaver-bird.js";
import { ChameleonBudgeter, ZONE_POLICIES } from "../src/cognitive/chameleon.js";
import { EagleEye } from "../src/cognitive/eagle.js";
import { newId, nowISO } from "../src/core/id.js";

interface BenchmarkReport {
  timestamp: string;
  version: string;
  system: {
    platform: string;
    arch: string;
    nodeVersion: string;
  };
  retrieval: {
    queries: number;
    hitAt5: number;
    recallAt5: number;
    mrrAt10: number;
    ndcgAt10: number;
    scopeLeakRate: number;
    conflictLeakRate: number;
    latencyP50Ms: number;
    latencyP95Ms: number;
    latencyMeanMs: number;
    byGroup: Record<string, { hit: number; recall: number; mrr: number; count: number }>;
  };
  dragonfly: {
    rescueTests: number;
    rescueHits: number;
    rescueRate: number;
    avgLatencyMs: number;
  };
  bowerbird: {
    totalNodes: number;
    classified: number;
    classifyRate: number;
    strayLabels: string[];
    avgConfidence: number;
  };
  weaverBird: {
    factFilterWorks: boolean;
    blueprintExtraction: boolean;
    versioningWorks: boolean;
  };
  chameleon: {
    zone0Preserved: boolean;
    topKRespected: boolean;
    presetPoliciesValid: boolean;
  };
  eagle: {
    healthScore: number;
    reportGenerated: boolean;
  };
  verdict: "PASS" | "FAIL";
  failures: string[];
}

async function runBenchmarks(): Promise<BenchmarkReport> {
  const workspaceDir = resolve(process.cwd(), ".tmp_benchmark_public");
  const failures: string[] = [];

  const manager = await AegisMemoryManager.create({
    agentId: "benchmark",
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
  db.prepare("DELETE FROM memory_events").run();
  db.prepare("DELETE FROM memory_edges").run();
  db.prepare("DELETE FROM memory_nodes").run();

  // ===== 1. Retrieval Benchmark =====
  console.log("\n▸ Running retrieval benchmark...");
  const baseIds = seedGroundTruthData(db);
  const allIds = seedExtendedData(db, baseIds);
  const allQueries = [...GROUND_TRUTH, ...EXTENDED_GROUND_TRUTH];
  const results = await Promise.all(
    allQueries.map((item) => runQuery(db, item, allIds, DEFAULT_AEGIS_CONFIG)),
  );
  const summary = summarize(results);
  printReport(summary, "PUBLIC BENCHMARK — Retrieval Quality");

  if (summary["Hit@5"] < 0.7) failures.push(`Hit@5 = ${(summary["Hit@5"]*100).toFixed(1)}% < 70%`);
  if (summary["Recall@5"] < 0.4) failures.push(`Recall@5 = ${(summary["Recall@5"]*100).toFixed(1)}% < 40%`);
  if (summary["MRR@10"] < 0.4) failures.push(`MRR@10 = ${summary["MRR@10"].toFixed(3)} < 0.4`);
  if (summary["ScopeLeakRate@5"] > 0.2) failures.push(`ScopeLeakRate = ${(summary["ScopeLeakRate@5"]*100).toFixed(1)}% > 20%`);
  if (summary["ConflictLeakRate@10"] > 0.1) failures.push(`ConflictLeakRate = ${(summary["ConflictLeakRate@10"]*100).toFixed(1)}% > 10%`);

  // ===== 2. Dragonfly Rescue Benchmark =====
  console.log("\n▸ Running Dragonfly rescue benchmark...");
  const dragonflyQueries = [
    "setup dự án",         // synonym: setup → cài đặt
    "huong dan cai dat",   // typo/diacritics missing
    "khởi động backend",   // synonym: khởi động → start
    "sửa lỗi bảo mật",    // direct Vietnamese
  ];

  // Add rescue test nodes
  const now = nowISO();
  const insertNode = db.prepare(`
    INSERT INTO memory_nodes (id, memory_type, content, canonical_subject, scope, status, importance, salience, memory_state, created_at, updated_at)
    VALUES (?, 'semantic_fact', ?, 'technical.infra', 'user', 'active', 0.9, 0.8, 'stable', ?, ?)
  `);
  insertNode.run(newId(), "Hướng dẫn cài đặt môi trường phát triển trên Linux.", now, now);
  insertNode.run(newId(), "Sử dụng lệnh npm run start để khởi động backend.", now, now);
  insertNode.run(newId(), "Cần sửa lỗi bảo mật trong module auth trước release.", now, now);

  const dragonfly = new DragonflySentry(db);
  let rescueHits = 0;
  const rescueLatencies: number[] = [];

  for (const q of dragonflyQueries) {
    const start = performance.now();
    const rescued = await dragonfly.rescue(q, 5);
    rescueLatencies.push(performance.now() - start);
    if (rescued.length > 0) rescueHits++;
  }

  const avgRescueLatency = rescueLatencies.reduce((a, b) => a + b, 0) / rescueLatencies.length;
  console.log(`  Rescue rate: ${rescueHits}/${dragonflyQueries.length}, avg latency: ${avgRescueLatency.toFixed(1)}ms`);

  // ===== 3. Bowerbird Taxonomy Benchmark =====
  console.log("\n▸ Running Bowerbird taxonomy benchmark...");
  db.prepare("UPDATE memory_nodes SET canonical_subject = NULL WHERE status = 'active'").run();

  const bird = new BowerbirdTaxonomist(db);
  const classified = bird.classifyAllUnknownNodes();
  const totalActive = (db.prepare("SELECT count(*) as c FROM memory_nodes WHERE status = 'active'").get() as any).c;
  const classifyRate = totalActive > 0 ? classified / totalActive : 0;
  const stray = bird.findStrayLabels();

  // Compute avg confidence
  const confRow = db.prepare(`
    SELECT AVG(taxonomy_confidence) as avg_conf FROM memory_nodes
    WHERE taxonomy_confidence IS NOT NULL AND status = 'active'
  `).get() as any;
  const avgConfidence = confRow?.avg_conf ?? 0;

  console.log(`  Classified: ${classified}/${totalActive} (${(classifyRate*100).toFixed(1)}%), avg confidence: ${avgConfidence.toFixed(2)}, stray: ${stray.length}`);
  if (classifyRate < 0.8) failures.push(`Bowerbird classify rate = ${(classifyRate*100).toFixed(1)}% < 80%`);

  // ===== 4. Weaver Bird Benchmark =====
  console.log("\n▸ Running Weaver Bird benchmark...");
  const singleToolMsgs = [
    { role: "assistant", content: [{ type: "tool_use", name: "read_file", input: {} }] },
  ];
  const multiToolMsgs = [
    { role: "assistant", content: [{ type: "tool_use", name: "read_file", input: {} }] },
    { role: "assistant", content: [{ type: "tool_use", name: "edit_file", input: {} }] },
    { role: "assistant", content: [{ type: "tool_use", name: "run_command", input: {} }] },
  ];

  const factFilterWorks = WeaverBird.extractProceduralBlueprint(singleToolMsgs, "Read a file") === null;
  const blueprintExtraction = WeaverBird.extractProceduralBlueprint(multiToolMsgs, "Fix a bug") !== null;

  // Test versioning
  const bp1 = WeaverBird.extractProceduralBlueprint(multiToolMsgs, "Fix a bug in auth");
  if (bp1) {
    const meta1 = WeaverBird.saveBlueprint(db, bp1, "fix a bug in auth");
    const meta2 = WeaverBird.saveBlueprint(db, bp1, "fix a bug in auth");
    var versioningWorks = meta2.version > meta1.version;
  } else {
    var versioningWorks = false;
  }

  console.log(`  Fact filter: ${factFilterWorks ? "OK" : "FAIL"}, Blueprint: ${blueprintExtraction ? "OK" : "FAIL"}, Versioning: ${versioningWorks ? "OK" : "FAIL"}`);

  // ===== 5. Chameleon Benchmark =====
  console.log("\n▸ Running Chameleon benchmark...");
  const mockResults = [
    { path: "aegis://trauma/1", startLine: 0, endLine: 0, score: 0.3, snippet: "Critical safety rule: never delete production data", source: "memory" as const, citation: "[trauma] policy.safety" },
    { path: "aegis://identity/1", startLine: 0, endLine: 0, score: 0.7, snippet: "User is a senior TypeScript developer", source: "memory" as const, citation: "identity.persona" },
    ...Array.from({ length: 8 }, (_, i) => ({
      path: `aegis://task/${i}`, startLine: 0, endLine: 0,
      score: 0.9 - i * 0.05, snippet: `Task memory content #${i} with enough length to test truncation behavior`,
      source: "memory" as const, citation: "knowledge.fact",
    })),
  ];

  const budgetOutput = ChameleonBudgeter.assemble(mockResults, { maxChars: 2000, topK: 5 });
  const zone0Preserved = budgetOutput.includes("[trauma]");
  const scoreMatches = budgetOutput.match(/\[\d+\.\d+\]/g) || [];
  const topKRespected = scoreMatches.length <= 5;
  const presetPoliciesValid = ["minimal", "balanced", "local-safe", "max-memory"].every(p => ZONE_POLICIES[p] !== undefined);

  console.log(`  Zone 0 preserved: ${zone0Preserved ? "OK" : "FAIL"}, TopK respected: ${topKRespected ? "OK" : "FAIL"}, Presets valid: ${presetPoliciesValid ? "OK" : "FAIL"}`);

  if (!zone0Preserved) failures.push("Chameleon dropped zone 0 (trauma)");

  // ===== 6. Eagle Summary =====
  console.log("\n▸ Running Eagle summary...");
  const eagle = new EagleEye(db);
  const eagleSummary = eagle.summarize();
  const reportText = eagle.renderSummary(eagleSummary);
  const reportGenerated = reportText.length > 50;
  console.log(`  Health score: ${eagleSummary.healthScore}, Report length: ${reportText.length} chars`);

  await closeAllManagers();

  // ===== Build Report =====
  const report: BenchmarkReport = {
    timestamp: new Date().toISOString(),
    version: "4.0.0",
    system: {
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.version,
    },
    retrieval: {
      queries: summary.queries,
      hitAt5: summary["Hit@5"],
      recallAt5: summary["Recall@5"],
      mrrAt10: summary["MRR@10"],
      ndcgAt10: summary["nDCG@10"],
      scopeLeakRate: summary["ScopeLeakRate@5"],
      conflictLeakRate: summary["ConflictLeakRate@10"],
      latencyP50Ms: summary.LatencyP50Ms,
      latencyP95Ms: summary.LatencyP95Ms,
      latencyMeanMs: summary.LatencyMeanMs,
      byGroup: summary.byGroup,
    },
    dragonfly: {
      rescueTests: dragonflyQueries.length,
      rescueHits,
      rescueRate: rescueHits / dragonflyQueries.length,
      avgLatencyMs: avgRescueLatency,
    },
    bowerbird: {
      totalNodes: totalActive,
      classified,
      classifyRate,
      strayLabels: stray,
      avgConfidence,
    },
    weaverBird: {
      factFilterWorks,
      blueprintExtraction,
      versioningWorks,
    },
    chameleon: {
      zone0Preserved,
      topKRespected,
      presetPoliciesValid,
    },
    eagle: {
      healthScore: eagleSummary.healthScore,
      reportGenerated,
    },
    verdict: failures.length === 0 ? "PASS" : "FAIL",
    failures,
  };

  return report;
}

// ===== Main =====
async function main() {
  const args = process.argv.slice(2);
  const jsonMode = args.includes("--json");
  const outputIdx = args.indexOf("--output");
  const outputPath = outputIdx >= 0 ? args[outputIdx + 1] : null;

  const report = await runBenchmarks();

  // Print summary
  console.log("\n" + "═".repeat(60));
  console.log(`  VERDICT: ${report.verdict}`);
  console.log("═".repeat(60));

  if (report.failures.length > 0) {
    console.log("  Failures:");
    for (const f of report.failures) console.log(`    ✗ ${f}`);
  }

  console.log(`\n  Retrieval:  Hit@5=${(report.retrieval.hitAt5*100).toFixed(1)}%  Recall@5=${(report.retrieval.recallAt5*100).toFixed(1)}%  MRR@10=${report.retrieval.mrrAt10.toFixed(3)}`);
  console.log(`  Dragonfly:  Rescue=${(report.dragonfly.rescueRate*100).toFixed(0)}%  Latency=${report.dragonfly.avgLatencyMs.toFixed(1)}ms`);
  console.log(`  Bowerbird:  Classify=${(report.bowerbird.classifyRate*100).toFixed(0)}%  Confidence=${report.bowerbird.avgConfidence.toFixed(2)}  Stray=${report.bowerbird.strayLabels.length}`);
  console.log(`  Chameleon:  Zone0=${report.chameleon.zone0Preserved ? "OK" : "FAIL"}  TopK=${report.chameleon.topKRespected ? "OK" : "FAIL"}`);
  console.log(`  Eagle:      Health=${report.eagle.healthScore}`);
  console.log("═".repeat(60));

  // Output JSON
  if (jsonMode || outputPath) {
    const json = JSON.stringify(report, null, 2);
    if (outputPath) {
      fs.writeFileSync(outputPath, json);
      console.log(`\n  Report saved to: ${outputPath}`);
    } else {
      console.log("\n" + json);
    }
  }

  process.exit(report.verdict === "PASS" ? 0 : 1);
}

main().catch((err) => {
  console.error("Benchmark failed:", err);
  process.exit(1);
});
