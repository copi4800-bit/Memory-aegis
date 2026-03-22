import fs from "node:fs";
import path from "node:path";
import type { OpenClawPluginApi, OpenClawPluginToolContext } from "openclaw/plugin-sdk/memory-core";
import { AegisMemoryManager, closeAllManagers } from "./aegis-manager.js";
import type { CognitiveLayers } from "./core/models.js";
import { AegisRouter } from "./retrieval/router.js";
import { WeaverBird } from "./cognitive/weaver-bird.js";

type AegisPluginConfig = {
  enabledLayers?: CognitiveLayers[];
  retrievalMaxHops?: number;
  dampingFactor?: number;
  decayHalfLifeDays?: number;
  crystallizationThreshold?: number;
  maintenanceCron?: string;
  maxNodesPerSearch?: number;
  autoCapture?: boolean;
  autoSyncOnAgentEnd?: boolean;
};

type ToolManagerContext = {
  manager: AegisMemoryManager;
  agentId: string;
  workspaceDir: string;
  sessionKey?: string;
};

const STRING_SCHEMA = (description: string) => ({ type: "string", description });
const NUMBER_SCHEMA = (description: string) => ({ type: "number", description });

const memorySearchParams = {
  type: "object",
  additionalProperties: false,
  properties: {
    query: STRING_SCHEMA("Search query"),
    limit: NUMBER_SCHEMA("Max results"),
    minScore: NUMBER_SCHEMA("Minimum score"),
  },
  required: ["query"],
} as const;

const memoryGetParams = {
  type: "object",
  additionalProperties: false,
  properties: {
    relPath: STRING_SCHEMA("Path or aegis:// node path"),
    from: NUMBER_SCHEMA("Start line offset"),
    lines: NUMBER_SCHEMA("Line count"),
  },
  required: ["relPath"],
} as const;

const memoryStoreParams = {
  type: "object",
  additionalProperties: false,
  properties: {
    text: STRING_SCHEMA("Text to store"),
  },
  required: ["text"],
} as const;

const backupParams = {
  type: "object",
  additionalProperties: false,
  properties: {
    mode: { type: "string", enum: ["snapshot", "export"] },
  },
} as const;

const restoreParams = {
  type: "object",
  additionalProperties: false,
  properties: {
    snapshotPath: STRING_SCHEMA("Local snapshot path"),
  },
  required: ["snapshotPath"],
} as const;

function readWorkspaceOverrideFromEnv(): string | undefined {
  const candidates = [
    process.env.OPENCLAW_WORKSPACE_DIR,
    process.env.OPENCLAW_WORKSPACE,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
  }
  return undefined;
}

function resolveWorkspaceDir(api: OpenClawPluginApi, ctx: OpenClawPluginToolContext): string {
  if (ctx.workspaceDir) {
    return ctx.workspaceDir;
  }
  const configured = api.config?.agents?.defaults?.workspace;
  if (typeof configured === "string" && configured.trim()) {
    return configured;
  }
  const envOverride = readWorkspaceOverrideFromEnv();
  if (envOverride) {
    return api.resolvePath(envOverride);
  }
  // Match OpenClaw's documented default workspace when no explicit workspace is available.
  return api.resolvePath("~/.openclaw/workspace");
}

async function resolveManagerContext(
  api: OpenClawPluginApi,
  ctx: OpenClawPluginToolContext,
): Promise<ToolManagerContext> {
  const agentId = ctx.agentId || "main";
  console.log("\n[⏳] 1. Bắt đầu nạp cấu hình Aegis...");
  const workspaceDir = resolveWorkspaceDir(api, ctx);
  const config = (api.pluginConfig ?? {}) as AegisPluginConfig;

  const fs = await import("node:fs");
  if (!fs.existsSync(workspaceDir)) {
    console.log(`[⏳] 2. Đang tạo thư mục: ${workspaceDir}`);
    fs.mkdirSync(workspaceDir, { recursive: true });
  }

  console.log("[⏳] 3. Đang gọi AegisMemoryManager.create() - Vui lòng đợi...");
  let manager;
  try {
    manager = await AegisMemoryManager.create({
      agentId,
      workspaceDir,
      config,
    });
    if (manager) {
      console.log("[✅] 4. Khởi tạo Manager THÀNH CÔNG!");
    }
  } catch (err) {
    console.error("\n[🔥 LỖI BỊ GIẤU CỦA AEGIS]:", err, "\n");
  }

  if (!manager) {
    console.log("[❌] 5. Quá trình tạo Manager thất bại ngầm.");
    throw new Error("memory-aegis-v4: failed to initialize manager");
  }
  return {
    manager,
    agentId,
    workspaceDir,
    sessionKey: ctx.sessionKey,
  };
}

async function tryResolveManagerContext(
  api: OpenClawPluginApi,
  ctx: OpenClawPluginToolContext,
  failureLabel: string,
): Promise<ToolManagerContext | null> {
  try {
    return await resolveManagerContext(api, ctx);
  } catch (err) {
    api.logger.warn(`${failureLabel}: ${String(err)}`);
    return null;
  }
}

function extractUserTexts(messages: unknown[]): string[] {
  const texts: string[] = [];
  for (const msg of messages) {
    if (!msg || typeof msg !== "object") continue;
    const record = msg as Record<string, unknown>;
    if (record.role !== "user") continue;
    const content = record.content;
    if (typeof content === "string") {
      texts.push(content);
      continue;
    }
    if (!Array.isArray(content)) continue;
    for (const block of content) {
      if (!block || typeof block !== "object") continue;
      const item = block as Record<string, unknown>;
      if (item.type === "text" && typeof item.text === "string") {
        texts.push(item.text);
      }
    }
  }
  return texts;
}

const memoryPlugin = {
  id: "memory-aegis-v4",
  name: "Memory Aegis v4",
  description: "Graph activation memory plugin with FTS5 retrieval and cognitive hooks",
  kind: "memory" as const,

  register(api: OpenClawPluginApi) {
    api.registerTool(
      (ctx: OpenClawPluginToolContext) => [
        {
          name: "memory_search",
          label: "Memory Search",
          description: "Search Aegis memory for relevant context.",
          parameters: memorySearchParams,
          async execute(_toolCallId: string, params: { query: string; limit?: number; minScore?: number }) {
            const { manager, sessionKey } = await resolveManagerContext(api, ctx);
            const results = await manager.search(params.query, {
              maxResults: params.limit,
              minScore: params.minScore,
              sessionKey,
            });
            if (results.length === 0) {
              return {
                content: [{ type: "text", text: "No relevant memories found." }],
                details: { count: 0 },
              };
            }
            const text = results
              .map(
                (entry: any, index: number) =>
                  `${index + 1}. ${entry.path}:${entry.startLine}-${entry.endLine} (${entry.score.toFixed(3)})\n${entry.snippet}`,
              )
              .join("\n\n");
            return {
              content: [{ type: "text", text }],
              details: { count: results.length, results },
            };
          },
        },
        {
          name: "memory_get",
          label: "Memory Get",
          description: "Read a specific Aegis memory citation or file fragment.",
          parameters: memoryGetParams,
          async execute(
            _toolCallId: string,
            params: { relPath: string; from?: number; lines?: number },
          ) {
            const { manager } = await resolveManagerContext(api, ctx);
            const result = await manager.readFile(params);
            return {
              content: [{ type: "text", text: result.text }],
              details: result,
            };
          },
        },
        {
          name: "memory_store",
          label: "Memory Store",
          description: "Persist user-provided text into Aegis memory by syncing a scratch note.",
          parameters: memoryStoreParams,
          async execute(_toolCallId: string, params: { text: string }) {
            const { manager, workspaceDir } = await resolveManagerContext(api, ctx);
            const storeDir = path.join(workspaceDir, "memory");
            const storePath = path.join(storeDir, "aegis-capture.md");
            await import("node:fs/promises").then(async (fs) => {
              await fs.mkdir(storeDir, { recursive: true });
              const line = `\n- ${new Date().toISOString()} ${params.text}\n`;
              await fs.appendFile(storePath, line, "utf8");
            });
            await manager.sync({ reason: "memory_store" });
            return {
              content: [{ type: "text", text: "Stored in Aegis memory." }],
              details: { path: storePath },
            };
          },
        },
        {
          name: "memory_backup_upload",
          label: "Memory Backup Upload",
          description: "Create a local Aegis snapshot/export for upload workflows.",
          parameters: backupParams,
          async execute(_toolCallId: string, params: { mode?: "snapshot" | "export" }) {
            const { manager, workspaceDir } = await resolveManagerContext(api, ctx);
            const destDir = path.join(workspaceDir, "exports");
            await import("node:fs/promises").then(async (fs) => {
              await fs.mkdir(destDir, { recursive: true });
            });
            const result = await manager.backup(params.mode === "export" ? "export" : "snapshot", destDir);
            return {
              content: [{ type: "text", text: `Backup created in ${destDir}` }],
              details: result,
            };
          },
        },
        {
          name: "memory_backup_download",
          label: "Memory Backup Download",
          description: "Restore Aegis memory from a local snapshot file path.",
          parameters: restoreParams,
          async execute(_toolCallId: string, params: { snapshotPath: string }) {
            const { manager } = await resolveManagerContext(api, ctx);
            const result = await manager.restore(params.snapshotPath);
            return {
              content: [{ type: "text", text: `Restore completed from ${params.snapshotPath}` }],
              details: result,
            };
          },
        },
        {
          name: "memory_stats",
          label: "Memory Stats",
          description: "View detailed Aegis memory telemetry and growth stats (Honeybee dance).",
          parameters: { type: "object", properties: {} },
          async execute(_toolCallId: string) {
            const { manager } = await resolveManagerContext(api, ctx);
            const { text, data } = await manager.getHoneybeeStats();
            return {
              content: [{ type: "text", text }],
              details: data,
            };
          },
        },
        {
          name: "memory_rebuild",
          label: "Memory Rebuild",
          description: "Trigger Axolotl regeneration to regrow derived knowledge links.",
          parameters: { type: "object", properties: {} },
          async execute(_toolCallId: string) {
            const { manager } = await resolveManagerContext(api, ctx);
            const result = await manager.regenerateDerivedData();
            return {
              content: [{ type: "text", text: `Axolotl regenerated ${result.createdRelations} new knowledge links.` }],
              details: result,
            };
          },
        },
        {
          name: "memory_scan",
          label: "Memory Scan",
          description: "Trigger Meerkat Sentry to scan for logical contradictions in memory.",
          parameters: { type: "object", properties: {} },
          async execute(_toolCallId: string) {
            const { manager } = await resolveManagerContext(api, ctx);
            const conflicts = await manager.runMeerkatScan();
            if (conflicts.length === 0) {
              return {
                content: [{ type: "text", text: "🦦 Meerkat scan completed: No contradictions found on the horizon." }],
                details: { count: 0 },
              };
            }
            const text = [
              `🦦 **Meerkat Sentry Alert: Found ${conflicts.length} contradictions!**`,
              ...conflicts.map((c: any, i: number) => `${i + 1}. ${c.reason}\n   Nodes: ${c.nodeA} ↔ ${c.nodeB}`),
              "\n👉 *Check 'drift_events' for full audit trail.*"
            ].join("\n");
            return {
              content: [{ type: "text", text }],
              details: { count: conflicts.length, conflicts },
            };
          },
        },
        {
          name: "memory_visualize",
          label: "Memory Visualize",
          description: "Generate an Eagle Eye visual snapshot of the memory graph.",
          parameters: { type: "object", properties: { limit: { type: "number", default: 1000 } } },
          async execute(toolCallId: string, params: any) {
            const { manager } = await resolveManagerContext(api, ctx);
            const data = await manager.getEagleSnapshot(params.limit);

            const canvasDir = path.join(process.env.HOME || "", ".openclaw", "canvas");
            const dataPath = path.join(canvasDir, "eagle_data.json");
            const viewerPath = path.join(canvasDir, "eagle-viewer.html");

            fs.writeFileSync(dataPath, JSON.stringify(data, null, 2));

            return {
              content: [{
                type: "text",
                text: `🦅 **Eagle Eye Snapshot Generated!**\n\n- Data: ${data.nodes.length} nodes, ${data.links.length} edges.\n- Viewer: ${viewerPath}\n\n👉 *Hãy mở file HTML trên bằng trình duyệt của đại ca để soi rọi bộ não.*`
              }],
              details: { path: viewerPath, nodeCount: data.nodes.length },
            };
          },
        },
        {
          name: "memory_taxonomy_clean",
          label: "Memory Taxonomy Clean",
          description: "Trigger Bowerbird to classify and harden missing taxonomies in memory nodes.",
          parameters: { type: "object", properties: {} },
          async execute(_toolCallId: string) {
            const { manager } = await resolveManagerContext(api, ctx);
            const result = await manager.runTaxonomyCleanup();
            return {
              content: [{ type: "text", text: `🪶 Bowerbird đã dán nhãn thành công cho ${result.classified} ký ức vô danh.` }],
              details: result,
            };
          },
        },
        {
          name: "memory_doctor",
          label: "Memory Doctor",
          description: "Check Aegis system health and diagnose issues.",
          parameters: { type: "object", properties: {} },
          async execute(_toolCallId: string) {
            const { manager } = await resolveManagerContext(api, ctx);
            const { text, data } = await manager.diagnose();
            return {
              content: [{ type: "text", text }],
              details: data,
            };
          },
        },
      ],
      { names: ["memory_search", "memory_get", "memory_store", "memory_backup_upload", "memory_backup_download", "memory_stats", "memory_rebuild", "memory_scan", "memory_visualize", "memory_taxonomy_clean", "memory_doctor"] },
    );

    api.on("before_agent_start", async (event: any, hookCtx: any) => {
      const context = await tryResolveManagerContext(
        api,
        {
          agentId: hookCtx.agentId,
          workspaceDir: hookCtx.workspaceDir,
          sessionKey: hookCtx.sessionKey,
          config: hookCtx.config,
        },
        "memory-aegis-v4 recall hook failed",
      );
      if (!context) {
        return;
      }
      const { manager } = context;
      const results = await manager.search(event.prompt, {
        maxResults: 10, // Lấy nhiều hơn để Cảnh sát giao thông lọc lại
        sessionKey: hookCtx.sessionKey,
      });

      console.log("\n[✅] 5. AEGIS ĐÃ TÌM XONG KÝ ỨC! Đang qua Cảnh sát giao thông Router...\n");

      if (results.length === 0) return;

      const prependContext = AegisRouter.enforce(results, {
        maxChars: 3000, // Thuế Token: giới hạn 3000 ký tự
        topK: 5,        // Xếp hàng: lấy Top 5 tinh túy nhất
        query: event.prompt
      });

      return { prependContext };
    });

    api.on("agent_end", async (event: any, hookCtx: any) => {
      const config = (api.pluginConfig ?? {}) as AegisPluginConfig;
      if (config.autoCapture === false) {
        return;
      }
      const context = await tryResolveManagerContext(
        api,
        {
          agentId: hookCtx.agentId,
          workspaceDir: hookCtx.workspaceDir,
          sessionKey: hookCtx.sessionKey,
          config: hookCtx.config,
        },
        "memory-aegis-v4 capture hook failed",
      );
      if (!context) {
        return;
      }
      const { manager } = context;
      void (async () => {
        try {
          const texts = extractUserTexts(event.messages ?? []);
          if (texts.length > 0) {
            const memoryDir = path.join(resolveWorkspaceDir(api, hookCtx), "memory");
            const storePath = path.join(memoryDir, "aegis-session-capture.md");
            await import("node:fs/promises").then(async (fs) => {
              await fs.mkdir(memoryDir, { recursive: true });
              const payload = texts.map((text) => `- ${new Date().toISOString()} ${text}`).join("\n") + "\n";
              await fs.appendFile(storePath, payload, "utf8");
            });
          }

          // === WEAVER BIRD (Nút thắt Quy Trình) ===
          try {
            const userGoal = texts[0] || "Autonomous Workflow";
            const blueprint = WeaverBird.extractProceduralBlueprint(event.messages ?? [], userGoal);
            if (blueprint) {
              // Hardened: pass goalFingerprint for versioning
              const goalFingerprint = userGoal.substring(0, 100).toLowerCase().replace(/\s+/g, " ").trim();
              WeaverBird.saveBlueprint(manager.getDb(), blueprint, goalFingerprint);
            }
          } catch (err) {
            console.warn("Weaver Bird trace extraction failed:", err);
          }

          if (config.autoSyncOnAgentEnd === true) {
            await manager.sync({
              reason: "agent_end",
              sessionFiles: hookCtx.sessionFile ? [hookCtx.sessionFile] : undefined,
            });
            await manager.runMaintenance();
          }
        } catch (err) {
          api.logger.warn(`memory-aegis-v4 background capture failed: ${String(err)}`);
        }
      })();
    });

    api.registerService({
      id: "memory-aegis-v4",
      start: () => {
        api.logger.info("memory-aegis-v4 registered");
      },
      stop: async () => {
        await closeAllManagers();
      },
    });
  },
};

export default memoryPlugin;
