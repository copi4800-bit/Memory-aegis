/**
 * AegisMemoryManager — implements OpenClaw's MemorySearchManager interface.
 *
 * Main bridge between Memory Aegis v4 and OpenClaw.
 */

import fs from "node:fs";
import path from "node:path";
import type Database from "better-sqlite3";
import { openDatabase, resolveDbPath, type AegisDatabase } from "./db/connection.js";
import { runMigrations } from "./db/migrate.js";
import { executeRetrievalPipeline } from "./retrieval/pipeline.js";
import { ingestBatch } from "./core/ingest.js";
import { microChunk } from "./cognitive/nutcracker.js";
import { flushPending } from "./cognitive/dolphin.js";
import { runMaintenanceCycle } from "./retention/maintenance.js";
import { autoPartition } from "./cognitive/octopus.js";
import { autoSetScratchTTL } from "./cognitive/nutcracker.js";
import { createSnapshot, exportLogicalData, type BackupResult, type ExportResult } from "./cognitive/tardigrade.js";
import { restoreFromSnapshot, type RestoreResult } from "./cognitive/planarian.js";
import { 
  type AegisConfig, 
  DEFAULT_AEGIS_CONFIG, 
  type CognitiveLayers, 
  type AegisTelemetry,
  type MemorySource 
} from "./core/models.js";
import { resolveConfig, type AegisPreset } from "./core/presets.js";
import type { MemorySearchResult } from "./retrieval/packet.js";
import { Honeybee } from "./telemetry/honeybee.js";
import { Axolotl } from "./maintenance/axolotl.js";
import { MeerkatSentry } from "./cognitive/meerkat.js";
import { EagleEye, type GraphData, type EagleSummary } from "./cognitive/eagle.js";
import { BowerbirdTaxonomist } from "./cognitive/bowerbird.js";
import { ZebraFinch } from "./cognitive/zebra-finch.js";
import { AegisDoctor, type DoctorReport } from "./maintenance/doctor.js";
import { buildMemoryProfile, renderProfile, type MemoryProfile } from "./ux/profile.js";
import { runOnboarding, type OnboardingResult } from "./ux/onboarding.js";

function validateConfig(config: AegisConfig): void {
  const checks: Array<[string, number | undefined, (v: number) => boolean]> = [
    ["keepDaily", config.keepDaily, (v) => v >= 1 && v <= 365],
    ["keepWeekly", config.keepWeekly, (v) => v >= 1 && v <= 52],
    ["keepMonthly", config.keepMonthly, (v) => v >= 1 && v <= 120],
    ["maxInteractionStatesPerSession", config.maxInteractionStatesPerSession, (v) => v >= 1 && v <= 10000],
    ["maxScratchCaptureBytes", config.maxScratchCaptureBytes, (v) => v >= 1024 && v <= 100 * 1024 * 1024],
    ["archiveAfterDays", config.archiveAfterDays, (v) => v >= 1 && v <= 3650],
  ];
  for (const [name, value, isValid] of checks) {
    if (value !== undefined && !isValid(value)) {
      throw new Error(`AegisConfig: "${name}" value ${value} is out of allowed range`);
    }
  }
}

const MANAGER_CACHE = new Map<string, AegisMemoryManager>();

export class AegisMemoryManager {
  private constructor(
    private aegisDb: AegisDatabase,
    private workspaceDir: string,
    private dbPath: string,
    private config: AegisConfig,
  ) {}

  /**
   * Factory method to create or retrieve a manager for a workspace.
   * Chấp nhận config từ plugin và merge với default.
   */
  static async create(opts: {
    agentId: string;
    workspaceDir: string;
    config?: Partial<AegisConfig> & { preset?: AegisPreset };
  }): Promise<AegisMemoryManager> {
    const { workspaceDir, config = {} } = opts;
    if (MANAGER_CACHE.has(workspaceDir)) {
      return MANAGER_CACHE.get(workspaceDir)!;
    }

    const { preset, ...overrides } = config;
    const mergedConfig = resolveConfig(preset, overrides);
    validateConfig(mergedConfig);
    const dbPath = resolveDbPath(workspaceDir);
    const aegisDb = openDatabase(dbPath);

    // Initialize/Migrate schema
    runMigrations(aegisDb.db);

    const manager = new AegisMemoryManager(aegisDb, workspaceDir, dbPath, mergedConfig);
    MANAGER_CACHE.set(workspaceDir, manager);
    return manager;
  }

  async close(): Promise<void> {
    this.aegisDb.close();
  }

  getDb(): Database.Database {
    return this.aegisDb.db;
  }

  /**
   * Search memory using the cognitive pipeline.
   */
  async search(query: string, opts: any): Promise<MemorySearchResult[]> {
    return executeRetrievalPipeline(this.aegisDb.db, query, this.config as any, opts);
  }

  /**
   * Read a specific file's memory or a node citation.
   * Trả về object có thuộc tính 'text' để thỏa mãn index.ts.
   */
  async readFile(params: { relPath: string; from?: number; lines?: number }): Promise<{ text: string; [key: string]: any }> {
    const { relPath, from, lines } = params;

    // Trường hợp là citation (aegis://node-id)
    if (relPath.startsWith("aegis://")) {
      const nodeId = relPath.replace("aegis://", "");
      const node = this.aegisDb.db.prepare(`
        SELECT content FROM memory_nodes WHERE id = ?
      `).get(nodeId) as { content: string } | undefined;
      
      return { 
        text: node?.content || "Memory node not found.",
        nodeId 
      };
    }

    // Trường hợp là file vật lý trong workspace
    const fullPath = path.isAbsolute(relPath) ? relPath : path.join(this.workspaceDir, relPath);
    if (!fs.existsSync(fullPath)) {
      return { text: `File not found: ${relPath}` };
    }

    try {
      const content = fs.readFileSync(fullPath, "utf-8");
      const allLines = content.split("\n");
      const startLine = from || 0;
      const lineCount = lines || allLines.length;
      const fragment = allLines.slice(startLine, startLine + lineCount).join("\n");

      return {
        text: fragment,
        path: relPath, // Return relative path as expected by tests
        from: startLine,
        lines: lineCount
      };
    } catch (err) {
      return { text: `Error reading file: ${String(err)}` };
    }
  }

  /**
   * Status of the memory engine.
   */
  status(): any {
    return {
      backend: "aegis",
      provider: "aegis-fts5",
      fts: {
        enabled: true,
        available: true
      },
      chunks: (this.aegisDb.db.prepare("SELECT COUNT(*) as c FROM memory_nodes").get() as any).c,
      dbPath: this.dbPath,
      workspaceDir: this.workspaceDir,
      custom: {
        aegis: {
          version: "4.0.0",
          layers: this.config.enabledLayers,
          preset: (this.config as any).preset || "balanced",
          entityCount: (this.aegisDb.db.prepare("SELECT COUNT(*) as c FROM memory_nodes").get() as any).c,
          edgeCount: (this.aegisDb.db.prepare("SELECT COUNT(*) as c FROM memory_edges").get() as any).c
        }
      }
    };
  }

  /**
   * Probe if embedding is available (Aegis is local-first, always OK).
   */
  async probeEmbeddingAvailability(): Promise<{ ok: boolean; error?: string }> {
    return { ok: true };
  }

  /**
   * Probe if vector search is available (Aegis uses FTS5, always true).
   */
  async probeVectorAvailability(): Promise<boolean> {
    return true;
  }

  /**
   * Sync files into memory.
   * Nhận object { reason, sessionFiles } từ index.ts.
   */
  async sync(opts: { reason?: string; force?: boolean; sessionFiles?: string[]; progress?: (update: any) => void }): Promise<void> {
    const { reason, sessionFiles, progress } = opts;
    const filesToIngest: Array<{ path: string; content: string; source: MemorySource }> = [];
    
    // 1. Tìm các file capture trong workspace/memory
    const memoryDir = path.join(this.workspaceDir, "memory");
    if (fs.existsSync(memoryDir)) {
      const captureFiles = fs.readdirSync(memoryDir).filter(f => f.endsWith('.md') || f.endsWith('.txt'));
      for (const filename of captureFiles) {
        const filePath = path.join(memoryDir, filename);
        filesToIngest.push({
          path: filePath,
          content: fs.readFileSync(filePath, "utf-8"),
          source: "memory"
        });
      }
    }
    
    // 2. Thêm các session files cụ thể nếu có
    if (sessionFiles) {
      for (const filePath of sessionFiles) {
        if (fs.existsSync(filePath)) {
          filesToIngest.push({
            path: filePath,
            content: fs.readFileSync(filePath, "utf-8"),
            source: "sessions"
          });
        }
      }
    }

    if (filesToIngest.length === 0) {
      if (progress) progress({ completed: 0, total: 0 });
      return;
    }

    // 3. Flush work-in-progress if any
    if (this.layerEnabled("dolphin")) {
      flushPending(this.aegisDb.db);
    }

    // 4. Micro-chunk large files
    const chunks: Array<{ sourcePath: string; content: string; source: MemorySource }> = [];
    for (const file of filesToIngest) {
      const parts = microChunk(file.content);
      for (const part of parts) {
        chunks.push({ sourcePath: file.path, content: part.content, source: file.source });
      }
    }

    // 5. Batch ingest
    ingestBatch(this.aegisDb.db, chunks);

    // 6. Post-ingest cognitive tasks
    if (this.layerEnabled("octopus")) {
      autoPartition(this.aegisDb.db);
    }
    if (this.layerEnabled("nutcracker")) {
      autoSetScratchTTL(this.aegisDb.db);
    }

    if (progress) {
      progress({ completed: chunks.length, total: chunks.length });
    }
  }

  /**
   * Run background maintenance.
   */
  async maintenance(): Promise<any> {
    return runMaintenanceCycle(this.aegisDb.db, this.workspaceDir, this.config);
  }

  /**
   * Backwards compatibility for index.ts
   */
  async runMaintenance(): Promise<any> {
    return this.maintenance();
  }

  /**
   * Create a backup or logical export.
   */
  async backup(mode: "snapshot" | "export", destDir: string): Promise<BackupResult | ExportResult> {
    if (mode === "export") {
      return exportLogicalData(this.aegisDb.db, destDir);
    }
    return createSnapshot(this.aegisDb.db, this.workspaceDir);
  }

  /**
   * Restore from a snapshot.
   */
  async restore(snapshotPath: string): Promise<RestoreResult> {
    return restoreFromSnapshot(snapshotPath, this.dbPath);
  }

  /**
   * Human-friendly status report: Honeybee + Eagle + Taxonomy.
   */
  async getStatus(): Promise<{ text: string; data: AegisTelemetry; summary: EagleSummary }> {
    const honeybee = new Honeybee(this.aegisDb.db, this.workspaceDir);
    const eagle = new EagleEye(this.aegisDb.db);
    const bird = new BowerbirdTaxonomist(this.aegisDb.db);

    const data = await honeybee.collect();
    const summary = eagle.summarize();
    const taxonomyStats = bird.taxonomyStats();

    const text = [
      honeybee.renderHumanReport(data, taxonomyStats),
      "",
      eagle.renderSummary(summary),
    ].join("\n");

    return { text, data, summary };
  }

  /**
   * Honeybee technical stats (power users).
   */
  async getHoneybeeStats(): Promise<{ text: string; data: AegisTelemetry }> {
    const honeybee = new Honeybee(this.aegisDb.db, this.workspaceDir);
    const eagle = new EagleEye(this.aegisDb.db);
    const data = await honeybee.collect();
    const eagleReport = eagle.analyze();
    return { text: honeybee.render(data) + "\n\n" + eagleReport, data };
  }

  /**
   * Axolotl: Tái tạo dữ liệu phái sinh.
   */
  async regenerateDerivedData(): Promise<{ createdRelations: number }> {
    const axolotl = new Axolotl(this.aegisDb.db, this.config);
    return axolotl.regenerate();
  }

  /**
   * Meerkat: Quét mâu thuẫn nhận thức.
   */
  async runMeerkatScan(): Promise<Array<{ nodeA: string; nodeB: string; reason: string }>> {
    const meerkat = new MeerkatSentry(this.aegisDb.db);
    return meerkat.scan();
  }

  /**
   * Eagle: Chụp ảnh đồ thị.
   */
  async getEagleSnapshot(limit?: number): Promise<GraphData> {
    const eagle = new EagleEye(this.aegisDb.db);
    return eagle.captureSnapshot(limit);
  }

  /**
   * Eagle: Phân tích structured summary.
   */
  async getEagleSummary(): Promise<{ text: string; data: EagleSummary }> {
    const eagle = new EagleEye(this.aegisDb.db);
    const data = eagle.summarize();
    return { text: eagle.renderSummary(data), data };
  }

  /**
   * Bowerbird: Phân loại taxonomy.
   */
  async runTaxonomyCleanup(): Promise<{ classified: number }> {
    const bird = new BowerbirdTaxonomist(this.aegisDb.db);
    return { classified: bird.classifyAllUnknownNodes() };
  }

  /**
   * Bowerbird: Migrate nhãn cũ → Taxonomy v1.
   */
  async runTaxonomyMigration(): Promise<{ migrated: number; stray: string[] }> {
    const bird = new BowerbirdTaxonomist(this.aegisDb.db);
    const migrated = bird.migrateOldTaxonomy();
    const stray = bird.findStrayLabels();
    return { migrated, stray };
  }

  /**
   * Bowerbird: Taxonomy stats.
   */
  async getTaxonomyStats(): Promise<{ stats: Array<{ subject: string; count: number }>; stray: string[] }> {
    const bird = new BowerbirdTaxonomist(this.aegisDb.db);
    return { stats: bird.taxonomyStats(), stray: bird.findStrayLabels() };
  }

  /**
   * Full auto-clean: Meerkat scan + Zebra Finch supersede + Bowerbird classify + migrate.
   * Giai đoạn 2.2: Auto mode an toàn mặc định.
   */
  async runAutoClean(): Promise<{
    conflicts: number;
    superseded: number;
    classified: number;
    migrated: number;
  }> {
    const results = { conflicts: 0, superseded: 0, classified: 0, migrated: 0 };

    // 1. Meerkat: quét mâu thuẫn
    if (this.layerEnabled("meerkat")) {
      const conflicts = await this.runMeerkatScan();
      results.conflicts = conflicts.length;
    }

    // 2. Zebra Finch: auto-supersede safe conflicts
    if (this.layerEnabled("zebra-finch")) {
      const finch = new ZebraFinch(this.aegisDb.db);
      const report = await finch.performRemSleep();
      results.superseded = report.supersededCount;
    }

    // 3. Bowerbird: classify unlabeled nodes
    if (this.layerEnabled("bowerbird")) {
      const bird = new BowerbirdTaxonomist(this.aegisDb.db);
      results.classified = bird.classifyAllUnknownNodes();
      results.migrated = bird.migrateOldTaxonomy();
    }

    return results;
  }

  /**
   * Aegis Doctor: Kiểm tra sức khỏe.
   */
  async diagnose(): Promise<{ text: string; data: DoctorReport }> {
    const doctor = new AegisDoctor(this.aegisDb.db, this.workspaceDir, this.dbPath);
    const report = doctor.diagnose();
    return { text: doctor.render(report), data: report };
  }

  // === UX (Phase 5) ===

  /**
   * Memory Profile: What does Aegis remember about the user?
   */
  async getMemoryProfile(): Promise<{ text: string; data: MemoryProfile }> {
    const data = buildMemoryProfile(this.aegisDb.db);
    return { text: renderProfile(data), data };
  }

  /**
   * Guided onboarding: first-time setup with health check + test.
   */
  async runOnboarding(preset?: AegisPreset): Promise<OnboardingResult> {
    return runOnboarding(
      this.aegisDb.db,
      this.workspaceDir,
      this.dbPath,
      preset ?? "balanced",
    );
  }

  // === Phase 4.2: Debug Panel for Power Users ===

  /**
   * Debug search: Trả về kết quả search kèm full signal breakdown.
   * Dành cho power users muốn trace retrieval decisions.
   */
  async debugSearch(query: string, opts: any): Promise<{
    text: string;
    results: MemorySearchResult[];
  }> {
    const { buildDebugExplanation } = await import("./retrieval/packet.js");
    const results = await this.search(query, opts);

    // Re-run pipeline nhẹ để lấy raw candidates (with signals)
    // Ở đây dùng kết quả có sẵn và format debug
    const lines = [
      `## Debug Search: "${query}"`,
      `Results: ${results.length}`,
      "",
    ];

    for (let i = 0; i < results.length; i++) {
      const r = results[i];
      lines.push(`### #${i + 1} — Score: ${r.score.toFixed(4)}`);
      lines.push(`Path: ${r.path}`);
      lines.push(`Citation: ${r.citation}`);
      lines.push(`Snippet: ${r.snippet.substring(0, 200)}${r.snippet.length > 200 ? "..." : ""}`);
      lines.push("");
    }

    return { text: lines.join("\n"), results };
  }

  /**
   * Inspect a specific memory node with full metadata.
   */
  async inspectNode(nodeId: string): Promise<{ text: string; node: any }> {
    const node = this.aegisDb.db.prepare(`
      SELECT * FROM memory_nodes WHERE id = ?
    `).get(nodeId) as any;

    if (!node) return { text: `Node ${nodeId} not found.`, node: null };

    // Get edges
    const edges = this.aegisDb.db.prepare(`
      SELECT * FROM memory_edges
      WHERE (src_node_id = ? OR dst_node_id = ?) AND status = 'active'
    `).all(nodeId, nodeId) as any[];

    // Get events
    const events = this.aegisDb.db.prepare(`
      SELECT event_type, payload_json, created_at FROM memory_events
      WHERE node_id = ? ORDER BY created_at DESC LIMIT 10
    `).all(nodeId) as any[];

    const lines = [
      `## Node: ${node.id}`,
      `Type: ${node.memory_type} | State: ${node.memory_state} | Status: ${node.status}`,
      `Subject: ${node.canonical_subject ?? "(none)"}${node.taxonomy_confidence ? ` (conf: ${node.taxonomy_confidence.toFixed(2)})` : ""}`,
      `Scope: ${node.scope} | Importance: ${node.importance} | Salience: ${node.salience}`,
      `Recall: ${node.recall_count}x | Override: ${node.override_priority}`,
      `Created: ${node.created_at} | Updated: ${node.updated_at}`,
      `Last access: ${node.last_access_at ?? "never"}`,
      "",
      `### Content`,
      node.content.substring(0, 500),
      "",
    ];

    if (node.blueprint_version) {
      const total = (node.blueprint_success_count || 0) + (node.blueprint_fail_count || 0);
      const rate = total > 0 ? ((node.blueprint_success_count || 0) / total * 100).toFixed(0) : "N/A";
      lines.push(`### Blueprint v${node.blueprint_version}`);
      lines.push(`Success: ${node.blueprint_success_count || 0} | Fail: ${node.blueprint_fail_count || 0} | Rate: ${rate}%`);
      lines.push("");
    }

    if (edges.length > 0) {
      lines.push(`### Edges (${edges.length})`);
      for (const e of edges) {
        const dir = e.src_node_id === nodeId ? "→" : "←";
        const other = e.src_node_id === nodeId ? e.dst_node_id : e.src_node_id;
        lines.push(`  ${dir} ${other} (${e.relation_type}, weight: ${e.weight})`);
      }
      lines.push("");
    }

    if (events.length > 0) {
      lines.push(`### Recent Events (${events.length})`);
      for (const ev of events) {
        lines.push(`  ${ev.created_at} ${ev.event_type}: ${ev.payload_json?.substring(0, 100) || ""}`);
      }
    }

    return { text: lines.join("\n"), node: { ...node, edges, events } };
  }

  /**
   * Trace supersede chain for a node.
   */
  async traceSupersede(nodeId: string): Promise<{ text: string; chain: string[] }> {
    const chain: string[] = [nodeId];
    let currentId = nodeId;

    // Walk forward: find what superseded this node
    for (let i = 0; i < 20; i++) {
      const next = this.aegisDb.db.prepare(`
        SELECT dst_node_id FROM memory_edges
        WHERE src_node_id = ? AND relation_type = 'supersedes' AND status = 'active'
        LIMIT 1
      `).get(currentId) as { dst_node_id: string } | undefined;

      if (!next) break;
      chain.push(next.dst_node_id);
      currentId = next.dst_node_id;
    }

    // Walk backward: find what this node superseded
    currentId = nodeId;
    for (let i = 0; i < 20; i++) {
      const prev = this.aegisDb.db.prepare(`
        SELECT src_node_id FROM memory_edges
        WHERE dst_node_id = ? AND relation_type = 'supersedes' AND status = 'active'
        LIMIT 1
      `).get(currentId) as { src_node_id: string } | undefined;

      if (!prev) break;
      chain.unshift(prev.src_node_id);
      currentId = prev.src_node_id;
    }

    const lines = [`## Supersede Chain (${chain.length} nodes)`, ""];
    for (let i = 0; i < chain.length; i++) {
      const node = this.aegisDb.db.prepare(`
        SELECT id, status, memory_state, canonical_subject, created_at
        FROM memory_nodes WHERE id = ?
      `).get(chain[i]) as any;
      const marker = chain[i] === nodeId ? " ← current" : "";
      const status = node ? `${node.status}/${node.memory_state}` : "missing";
      lines.push(`${i + 1}. ${chain[i]} [${status}]${marker}`);
    }

    return { text: lines.join("\n"), chain };
  }

  // === Helpers ===

  layerEnabled(layer: CognitiveLayers): boolean {
    return this.config.enabledLayers.includes(layer);
  }
}

/**
 * Close all cached managers.
 */
export async function closeAllManagers(): Promise<void> {
  for (const manager of MANAGER_CACHE.values()) {
    await manager.close();
  }
  MANAGER_CACHE.clear();
}
