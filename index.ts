import type { OpenClawPluginApi, OpenClawPluginToolContext } from "openclaw/plugin-sdk/memory-core";
import {
    type AdapterSearchResult,
    backgroundApplyViaPython,
    backgroundPlanViaPython,
    backgroundRollbackViaPython,
    backgroundShadowViaPython,
    backupListViaPython,
    backupPreviewViaPython,
    backupDownloadViaPython,
    backupUploadViaPython,
    cleanViaPython,
    conflictPromptViaPython,
    conflictResolveViaPython,
    contextPackViaPython,
    correctViaPython,
    doctorViaPython,
    evidenceArtifactsViaPython,
    forgetViaPython,
    getViaPython,
    governanceViaPython,
    linkNeighborsViaPython,
    linkStoreViaPython,
    onboardingViaPython,
    profileViaPython,
    rebuildViaPython,
    recallViaPython,
    rememberViaPython,
    scanViaPython,
    searchViaPython,
    syncExportViaPython,
    syncImportViaPython,
    syncPreviewViaPython,
    scopePolicyViaPython,
    storageCompactViaPython,
    storageFootprintViaPython,
    surfaceViaPython,
    statusViaPython,
    storeViaPython,
    taxonomyCleanViaPython,
    vectorInspectViaPython,
    visualizeViaPython,
} from "./src/python-adapter.js";

type AegisPluginConfig = {
    enabledLayers?: string[];
    retrievalMaxHops?: number;
    dampingFactor?: number;
    decayHalfLifeDays?: number;
    crystallizationThreshold?: number;
    maintenanceCron?: string;
    maxNodesPerSearch?: number;
    autoCapture?: boolean;
    autoSyncOnAgentEnd?: boolean;
    pythonRetrievalAdapter?: "off" | "auto" | "force";
    pythonToolAdapter?: "off" | "auto" | "force";
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

type PythonHealthPayload = Record<string, unknown> & {
    health_state?: string;
    health?: {
        state?: string;
        issues?: unknown[];
        capabilities?: Record<string, boolean>;
    };
    counts?: Record<string, unknown>;
    issues?: unknown[];
};

const memoryContextPackParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        query: STRING_SCHEMA("Query used to build a host-ready context pack"),
        limit: NUMBER_SCHEMA("Max results"),
    },
    required: ["query"],
} as const;

const memoryLinkStoreParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        sourceId: STRING_SCHEMA("Source memory ID"),
        targetId: STRING_SCHEMA("Target memory ID"),
        linkType: STRING_SCHEMA("Explicit relation type"),
        weight: NUMBER_SCHEMA("Relation weight"),
    },
    required: ["sourceId", "targetId", "linkType"],
} as const;

const memoryLinkNeighborsParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        memoryId: STRING_SCHEMA("Seed memory ID"),
        limit: NUMBER_SCHEMA("Max explicit linked neighbors"),
    },
    required: ["memoryId"],
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
        scopeType: STRING_SCHEMA("Optional scope type to restore selectively"),
        scopeId: STRING_SCHEMA("Optional scope ID to restore selectively"),
    },
    required: ["snapshotPath"],
} as const;

const backupPreviewParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        snapshotPath: STRING_SCHEMA("Backup path to validate without restoring"),
        scopeType: STRING_SCHEMA("Optional scope type to preview selectively"),
        scopeId: STRING_SCHEMA("Optional scope ID to preview selectively"),
    },
    required: ["snapshotPath"],
} as const;

const conflictPromptParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        scopeType: STRING_SCHEMA("Optional scope type to filter prompts"),
        scopeId: STRING_SCHEMA("Optional scope ID to filter prompts"),
        subject: STRING_SCHEMA("Optional subject to filter prompts"),
    },
} as const;

const conflictResolveParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        conflictId: STRING_SCHEMA("Conflict ID to resolve"),
        action: STRING_SCHEMA("Resolution action"),
        rationale: STRING_SCHEMA("Optional operator rationale"),
    },
    required: ["conflictId", "action"],
} as const;

const scopePolicyParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        scopeType: STRING_SCHEMA("Optional scope type to inspect"),
        scopeId: STRING_SCHEMA("Optional scope ID to inspect"),
        syncPolicy: STRING_SCHEMA("Optional sync policy filter for listing"),
    },
} as const;

const syncExportParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        scopeType: STRING_SCHEMA("Scope type to export"),
        scopeId: STRING_SCHEMA("Scope ID to export"),
    },
    required: ["scopeType", "scopeId"],
} as const;

const syncPreviewParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        envelopePath: STRING_SCHEMA("Sync envelope path to preview"),
    },
    required: ["envelopePath"],
} as const;

const syncImportParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        envelopePath: STRING_SCHEMA("Sync envelope path to import"),
    },
    required: ["envelopePath"],
} as const;

const governanceParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        scopeType: STRING_SCHEMA("Optional scope type"),
        scopeId: STRING_SCHEMA("Optional scope ID"),
        memoryId: STRING_SCHEMA("Optional memory ID"),
        limit: NUMBER_SCHEMA("Max governance rows"),
    },
} as const;

const backgroundPlanParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        scopeType: STRING_SCHEMA("Scope type"),
        scopeId: STRING_SCHEMA("Scope ID"),
    },
    required: ["scopeType", "scopeId"],
} as const;

const backgroundRunParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        runId: STRING_SCHEMA("Background run ID"),
    },
    required: ["runId"],
} as const;

const backgroundApplyParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        runId: STRING_SCHEMA("Background run ID"),
        maxMutations: NUMBER_SCHEMA("Maximum allowed mutations"),
    },
    required: ["runId"],
} as const;

const vectorInspectParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        query: STRING_SCHEMA("Vector inspection query"),
        scopeType: STRING_SCHEMA("Scope type"),
        scopeId: STRING_SCHEMA("Scope ID"),
        includeGlobal: { type: "boolean", description: "Include global scope" },
        limit: NUMBER_SCHEMA("Max matches"),
    },
    required: ["query", "scopeType", "scopeId"],
} as const;

const evidenceArtifactsParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        scopeType: STRING_SCHEMA("Optional scope type"),
        scopeId: STRING_SCHEMA("Optional scope ID"),
        memoryId: STRING_SCHEMA("Optional memory ID"),
        limit: NUMBER_SCHEMA("Max artifacts"),
    },
} as const;

const storageCompactParams = {
    type: "object",
    additionalProperties: false,
    properties: {
        archivedMemoryDays: NUMBER_SCHEMA("Delete archived memory older than this many days"),
        supersededMemoryDays: NUMBER_SCHEMA("Delete superseded memory older than this many days"),
        evidenceDays: NUMBER_SCHEMA("Delete cold evidence rows older than this many days"),
        governanceDays: NUMBER_SCHEMA("Delete cold governance rows older than this many days"),
        replicationDays: NUMBER_SCHEMA("Delete replication audit rows older than this many days"),
        backgroundDays: NUMBER_SCHEMA("Delete discarded background runs older than this many days"),
        vacuum: { type: "boolean", description: "Run VACUUM after pruning" },
    },
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

function renderSearchText(results: AdapterSearchResult[]): string {
    return results
        .map(
            (entry: AdapterSearchResult, index: number) =>
                `${index + 1}. ${entry.path}:${entry.startLine}-${entry.endLine} (${entry.score.toFixed(3)})\n${entry.snippet}`,
        )
        .join("\n\n");
}

function extractHealthState(payload: PythonHealthPayload): string {
    const nested = payload.health;
    if (nested && typeof nested === "object" && typeof nested.state === "string") {
        return nested.state;
    }
    return typeof payload.health_state === "string" ? payload.health_state : "UNKNOWN";
}

function renderPrependContext(results: AdapterSearchResult[], query: string): string {
    const top = results.slice(0, 5);
    const lines = [
        "Relevant Aegis memory context:",
        `Query: ${query}`,
        "",
    ];
    for (const [index, result] of top.entries()) {
        lines.push(`${index + 1}. ${result.snippet}`);
        lines.push(`   Source: ${result.path}`);
        if (result.citation) {
            lines.push(`   Why: ${result.citation}`);
        }
        lines.push("");
    }
    return lines.join("\n").trimEnd();
}

const memoryPlugin = {
    id: "memory-aegis-v8",
    name: "Memory Aegis v8",
    description: "Graph activation memory plugin with FTS5 retrieval and cognitive hooks",
    kind: "memory" as const,

    register(api: OpenClawPluginApi) {
        const buildTools = (ctx: OpenClawPluginToolContext) => {
            const tools = [
                {
                    name: "memory_search",
                    label: "Memory Search",
                    description: "Search Aegis memory for relevant context.",
                    parameters: memorySearchParams,
                    async execute(_toolCallId: string, params: { query: string; limit?: number; minScore?: number }) {
                        const python = await searchViaPython({
                            query: params.query,
                            limit: params.limit,
                            scopeType: "agent",
                            scopeId: ctx.agentId || "main",
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        if (python.mappedResults.length === 0) {
                            return {
                                content: [{ type: "text", text: "No relevant memories found." }],
                                details: { count: 0, backend: "python", pythonResults: python.rawResults },
                            };
                        }
                        return {
                            content: [{ type: "text", text: renderSearchText(python.mappedResults) }],
                            details: {
                                count: python.mappedResults.length,
                                backend: "python",
                                results: python.mappedResults,
                                pythonResults: python.rawResults,
                            },
                        };
                    },
                },
                {
                    name: "memory_conflict_prompt",
                    label: "Memory Conflict Prompt",
                    description: "List conflict prompts that require explicit review or resolution.",
                    parameters: conflictPromptParams,
                    async execute(
                        _toolCallId: string,
                        params: { scopeType?: string; scopeId?: string; subject?: string },
                    ) {
                        const payload = await conflictPromptViaPython({
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            subject: params.subject,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_conflict_resolve",
                    label: "Memory Conflict Resolve",
                    description: "Apply an explicit resolution action to a conflict prompt.",
                    parameters: conflictResolveParams,
                    async execute(
                        _toolCallId: string,
                        params: { conflictId: string; action: string; rationale?: string },
                    ) {
                        const payload = await conflictResolveViaPython({
                            conflictId: params.conflictId,
                            action: params.action,
                            rationale: params.rationale,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_context_pack",
                    label: "Memory Context Pack",
                    description: "Build a lexical-first, explainable context pack for the current host model.",
                    parameters: memoryContextPackParams,
                    async execute(_toolCallId: string, params: { query: string; limit?: number }) {
                        const payload = await contextPackViaPython({
                            query: params.query,
                            limit: params.limit,
                            scopeType: "agent",
                            scopeId: ctx.agentId || "main",
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_link_store",
                    label: "Memory Link Store",
                    description: "Create or update an explicit relation between two memories in the same scope.",
                    parameters: memoryLinkStoreParams,
                    async execute(
                        _toolCallId: string,
                        params: { sourceId: string; targetId: string; linkType: string; weight?: number },
                    ) {
                        const payload = await linkStoreViaPython({
                            sourceId: params.sourceId,
                            targetId: params.targetId,
                            linkType: params.linkType,
                            weight: params.weight,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_link_neighbors",
                    label: "Memory Link Neighbors",
                    description: "Inspect explicit linked neighbors for a memory node.",
                    parameters: memoryLinkNeighborsParams,
                    async execute(
                        _toolCallId: string,
                        params: { memoryId: string; limit?: number },
                    ) {
                        const payload = await linkNeighborsViaPython({
                            memoryId: params.memoryId,
                            limit: params.limit,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
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
                        const payload = await getViaPython({
                            relPath: params.relPath,
                            from: params.from,
                            lines: params.lines,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: payload.text }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_store",
                    label: "Memory Store",
                    description: "Persist user-provided text into Aegis memory by syncing a scratch note.",
                    parameters: memoryStoreParams,
                    async execute(_toolCallId: string, params: { text: string }) {
                        const message = await storeViaPython({
                            text: params.text,
                            scopeType: "agent",
                            scopeId: ctx.agentId || "main",
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: message || "Stored in Aegis memory." }],
                            details: { backend: "python" },
                        };
                    },
                },
                {
                    name: "memory_surface",
                    label: "Memory Surface",
                    description: "Describe the Python-owned public memory contract, including bounded health states and capability reporting.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await surfaceViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_scope_policy",
                    label: "Memory Scope Policy",
                    description: "Inspect local-only versus sync-eligible scope policy without requiring any remote backend.",
                    parameters: scopePolicyParams,
                    async execute(
                        _toolCallId: string,
                        params: { scopeType?: string; scopeId?: string; syncPolicy?: string },
                    ) {
                        const payload = await scopePolicyViaPython({
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            syncPolicy: params.syncPolicy,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_sync_export",
                    label: "Memory Sync Export",
                    description: "Export a Python-owned sync envelope for a specific scope.",
                    parameters: syncExportParams,
                    async execute(
                        _toolCallId: string,
                        params: { scopeType: string; scopeId: string },
                    ) {
                        const payload = await syncExportViaPython({
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_sync_preview",
                    label: "Memory Sync Preview",
                    description: "Preview a Python-owned sync envelope before importing it.",
                    parameters: syncPreviewParams,
                    async execute(
                        _toolCallId: string,
                        params: { envelopePath: string },
                    ) {
                        const payload = await syncPreviewViaPython({
                            envelopePath: params.envelopePath,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_sync_import",
                    label: "Memory Sync Import",
                    description: "Import a Python-owned sync envelope into local Aegis storage.",
                    parameters: syncImportParams,
                    async execute(
                        _toolCallId: string,
                        params: { envelopePath: string },
                    ) {
                        const payload = await syncImportViaPython({
                            envelopePath: params.envelopePath,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_backup_upload",
                    label: "Memory Backup Upload",
                    description: "Create a local Aegis snapshot/export for upload workflows.",
                    parameters: backupParams,
                    async execute(_toolCallId: string, params: { mode?: "snapshot" | "export" }) {
                        const payload = await backupUploadViaPython({
                            mode: params.mode,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_backup_download",
                    label: "Memory Backup Download",
                    description: "Restore Aegis memory from a local snapshot file path.",
                    parameters: restoreParams,
                    async execute(
                        _toolCallId: string,
                        params: { snapshotPath: string; scopeType?: string; scopeId?: string },
                    ) {
                        const payload = await backupDownloadViaPython({
                            snapshotPath: params.snapshotPath,
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_backup_list",
                    label: "Memory Backup List",
                    description: "List known Aegis backups with manifest-backed metadata.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await backupListViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_backup_preview",
                    label: "Memory Backup Preview",
                    description: "Validate a backup and preview restore impact without mutating the active DB.",
                    parameters: backupPreviewParams,
                    async execute(
                        _toolCallId: string,
                        params: { snapshotPath: string; scopeType?: string; scopeId?: string },
                    ) {
                        const payload = await backupPreviewViaPython({
                            snapshotPath: params.snapshotPath,
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_stats",
                    label: "Memory Stats",
                    description: "View Python-owned Aegis status with bounded health state, issues, and capability flags.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await statusViaPython({ workspaceDir: resolveWorkspaceDir(api, ctx) }) as PythonHealthPayload;
                        const healthState = extractHealthState(payload);
                        const activeCount = Number((payload.counts as Record<string, unknown> | undefined)?.active ?? 0);
                        const summaryLines = [
                            "Aegis status summary:",
                            healthState === "HEALTHY"
                                ? "Aegis is ready and local memory is working normally."
                                : healthState === "DEGRADED_SYNC"
                                  ? "Aegis is usable locally, but some optional sync-related features are degraded."
                                  : "Aegis is not ready for safe memory use right now.",
                            `Active memories: ${activeCount}`,
                            `Health state: ${healthState}`,
                        ];
                        if (healthState === "DEGRADED_SYNC") {
                            summaryLines.push("Local remember and recall still work.");
                        }
                        return {
                            content: [{ type: "text", text: summaryLines.join("\n") }],
                            details: { backend: "python", ...payload },
                        };
                    },
                },
                {
                    name: "memory_clean",
                    label: "Memory Clean",
                    description: "Run Aegis Python maintenance and conflict scan.",
                    parameters: {
                        type: "object",
                        additionalProperties: false,
                        properties: {
                            subject: STRING_SCHEMA("Optional subject to scan for conflicts"),
                            dryRun: { type: "boolean", description: "Not supported by the Python adapter yet" },
                        },
                    },
                    async execute(_toolCallId: string, params: { subject?: string; dryRun?: boolean }) {
                        if (params.dryRun) {
                            return {
                                content: [{ type: "text", text: "memory_clean dryRun is not supported by the Python adapter." }],
                                details: { backend: "python", dryRunSupported: false },
                            };
                        }
                        const payload = await cleanViaPython({
                            subject: params.subject,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: { backend: "python", ...payload },
                        };
                    },
                },
                {
                    name: "memory_setup",
                    label: "Memory Setup",
                    description: "Run the Python-owned first-run setup and readiness checks for Aegis.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await onboardingViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        const summary = typeof payload.summary === "string"
                            ? payload.summary
                            : JSON.stringify(payload, null, 2);
                        return {
                            content: [{ type: "text", text: summary }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_profile",
                    label: "Memory Profile",
                    description: "Show the Python memory profile for the current agent scope.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const profile = await profileViaPython({
                            scopeId: ctx.agentId || "main",
                            scopeType: "agent",
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: profile }],
                            details: { backend: "python" },
                        };
                    },
                },
                {
                    name: "memory_rebuild",
                    label: "Memory Rebuild",
                    description: "Trigger Axolotl regeneration to regrow derived knowledge links.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await rebuildViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_scan",
                    label: "Memory Scan",
                    description: "Trigger Meerkat Sentry to scan for logical contradictions in memory.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await scanViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_visualize",
                    label: "Memory Visualize",
                    description: "Generate an Eagle Eye visual snapshot of the memory graph.",
                    parameters: { type: "object", properties: { limit: { type: "number", default: 1000 } } },
                    async execute(_toolCallId: string, params: any) {
                        const payload = await visualizeViaPython({
                            limit: params.limit,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_governance",
                    label: "Memory Governance",
                    description: "Inspect governance events and state transitions for the Python-owned runtime.",
                    parameters: governanceParams,
                    async execute(
                        _toolCallId: string,
                        params: { scopeType?: string; scopeId?: string; memoryId?: string; limit?: number },
                    ) {
                        const payload = await governanceViaPython({
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            memoryId: params.memoryId,
                            limit: params.limit,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_background_plan",
                    label: "Memory Background Plan",
                    description: "Plan governed background intelligence proposals for a scope.",
                    parameters: backgroundPlanParams,
                    async execute(_toolCallId: string, params: { scopeType: string; scopeId: string }) {
                        const payload = await backgroundPlanViaPython({
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_background_shadow",
                    label: "Memory Background Shadow",
                    description: "Shadow-run a planned background intelligence proposal.",
                    parameters: backgroundRunParams,
                    async execute(_toolCallId: string, params: { runId: string }) {
                        const payload = await backgroundShadowViaPython({
                            runId: params.runId,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_background_apply",
                    label: "Memory Background Apply",
                    description: "Apply a governed background run with blast-radius controls.",
                    parameters: backgroundApplyParams,
                    async execute(_toolCallId: string, params: { runId: string; maxMutations?: number }) {
                        const payload = await backgroundApplyViaPython({
                            runId: params.runId,
                            maxMutations: params.maxMutations,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_background_rollback",
                    label: "Memory Background Rollback",
                    description: "Rollback an applied background intelligence run.",
                    parameters: backgroundRunParams,
                    async execute(_toolCallId: string, params: { runId: string }) {
                        const payload = await backgroundRollbackViaPython({
                            runId: params.runId,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_vector_inspect",
                    label: "Memory Vector Inspect",
                    description: "Inspect local vector-store matches for a scoped query.",
                    parameters: vectorInspectParams,
                    async execute(
                        _toolCallId: string,
                        params: { query: string; scopeType: string; scopeId: string; includeGlobal?: boolean; limit?: number },
                    ) {
                        const payload = await vectorInspectViaPython({
                            query: params.query,
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            includeGlobal: params.includeGlobal,
                            limit: params.limit,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_evidence_artifacts",
                    label: "Memory Evidence Artifacts",
                    description: "List evidence artifacts recorded by the Python-owned runtime.",
                    parameters: evidenceArtifactsParams,
                    async execute(
                        _toolCallId: string,
                        params: { scopeType?: string; scopeId?: string; memoryId?: string; limit?: number },
                    ) {
                        const payload = await evidenceArtifactsViaPython({
                            scopeType: params.scopeType,
                            scopeId: params.scopeId,
                            memoryId: params.memoryId,
                            limit: params.limit,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_storage_footprint",
                    label: "Memory Storage Footprint",
                    description: "Inspect SQLite storage footprint and current compaction policy.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await storageFootprintViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_storage_compact",
                    label: "Memory Storage Compact",
                    description: "Prune cold historical rows and reclaim SQLite space with bounded compaction.",
                    parameters: storageCompactParams,
                    async execute(
                        _toolCallId: string,
                        params: {
                            archivedMemoryDays?: number;
                            supersededMemoryDays?: number;
                            evidenceDays?: number;
                            governanceDays?: number;
                            replicationDays?: number;
                            backgroundDays?: number;
                            vacuum?: boolean;
                        },
                    ) {
                        const payload = await storageCompactViaPython({
                            archivedMemoryDays: params.archivedMemoryDays,
                            supersededMemoryDays: params.supersededMemoryDays,
                            evidenceDays: params.evidenceDays,
                            governanceDays: params.governanceDays,
                            replicationDays: params.replicationDays,
                            backgroundDays: params.backgroundDays,
                            vacuum: params.vacuum,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_taxonomy_clean",
                    label: "Memory Taxonomy Clean",
                    description: "Trigger Bowerbird to classify and harden missing taxonomies in memory nodes.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await taxonomyCleanViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_doctor",
                    label: "Memory Doctor",
                    description: "Check Python-owned Aegis health with structured issue codes and capability flags.",
                    parameters: { type: "object", properties: {} },
                    async execute(_toolCallId: string) {
                        const payload = await doctorViaPython({
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        }) as PythonHealthPayload;
                        const healthState = extractHealthState(payload);
                        const summaryLines = [
                            "Aegis doctor summary:",
                            healthState === "HEALTHY"
                                ? "Aegis memory is operating normally."
                                : healthState === "DEGRADED_SYNC"
                                  ? "Aegis is usable locally, but some optional sync-related features are degraded."
                                  : "Aegis is not ready for safe memory use right now.",
                            `Health state: ${healthState}`,
                        ];
                        const issues = Array.isArray(payload.issues) ? payload.issues : [];
                        if (issues.length > 0) {
                            summaryLines.push(`Current issues: ${issues.join(", ")}`);
                        }
                        return {
                            content: [{ type: "text", text: summaryLines.join("\n") }],
                            details: payload,
                        };
                    },
                },
                {
                    name: "memory_remember",
                    label: "Memory Remember",
                    description: "Simplified action: store a piece of information into memory using natural language.",
                    parameters: {
                        type: "object",
                        additionalProperties: false,
                        properties: {
                            content: STRING_SCHEMA("The information to remember"),
                        },
                        required: ["content"],
                    },
                    async execute(_toolCallId: string, params: { content: string }) {
                        const message = await rememberViaPython({
                            content: params.content,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: message }],
                            details: { backend: "python" },
                        };
                    },
                },
                {
                    name: "memory_recall",
                    label: "Memory Recall",
                    description: "Simplified action: retrieve memories related to a query using natural language.",
                    parameters: {
                        type: "object",
                        additionalProperties: false,
                        properties: {
                            query: STRING_SCHEMA("What to recall from memory"),
                        },
                        required: ["query"],
                    },
                    async execute(_toolCallId: string, params: { query: string }) {
                        const message = await recallViaPython({
                            query: params.query,
                            scopeType: "agent",
                            scopeId: ctx.agentId || "main",
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: message }],
                            details: { backend: "python" },
                        };
                    },
                },
                {
                    name: "memory_correct",
                    label: "Memory Correct",
                    description: "Simplified action: correct or update an existing piece of information in memory.",
                    parameters: {
                        type: "object",
                        additionalProperties: false,
                        properties: {
                            content: STRING_SCHEMA("The corrected information"),
                        },
                        required: ["content"],
                    },
                    async execute(_toolCallId: string, params: { content: string }) {
                        const message = await correctViaPython({
                            content: params.content,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: message }],
                            details: { backend: "python" },
                        };
                    },
                },
                {
                    name: "memory_forget",
                    label: "Memory Forget",
                    description: "Simplified action: remove a specific piece of information from memory.",
                    parameters: {
                        type: "object",
                        additionalProperties: false,
                        properties: {
                            query: STRING_SCHEMA("What to forget from memory"),
                        },
                        required: ["query"],
                    },
                    async execute(_toolCallId: string, params: { query: string }) {
                        const message = await forgetViaPython({
                            query: params.query,
                            workspaceDir: resolveWorkspaceDir(api, ctx),
                        });
                        return {
                            content: [{ type: "text", text: message }],
                            details: { backend: "python" },
                        };
                    },
                },
            ];
            return tools;
        };
        const toolNames = buildTools({ agentId: "", workspaceDir: "", sessionKey: "" } as OpenClawPluginToolContext).map(
            (tool) => tool.name,
        );
        api.registerTool(buildTools, { names: toolNames });

        api.on("before_agent_start", async (event: any, hookCtx: any) => {
            const python = await searchViaPython({
                query: event.prompt,
                limit: 10,
                scopeType: "agent",
                scopeId: hookCtx.agentId || "main",
                workspaceDir: resolveWorkspaceDir(api, hookCtx),
            });
            const results = python.mappedResults;

            console.log("\n[✅] 5. AEGIS ĐÃ TÌM XONG KÝ ỨC! Đang qua Cảnh sát giao thông Router...\n");

            if (results.length === 0) return;

            const prependContext = renderPrependContext(results, event.prompt);

            return { prependContext };
        });

        api.on("agent_end", async (event: any, hookCtx: any) => {
            const config = (api.pluginConfig ?? {}) as AegisPluginConfig;
            if (config.autoCapture === false) {
                return;
            }
            void (async () => {
                try {
                    const texts = extractUserTexts(event.messages ?? []);
                    for (const text of texts) {
                        await storeViaPython({
                            text,
                            scopeType: "agent",
                            scopeId: hookCtx.agentId || "main",
                            workspaceDir: resolveWorkspaceDir(api, hookCtx),
                        });
                    }

                    if (config.autoSyncOnAgentEnd === true) {
                        await cleanViaPython({
                            workspaceDir: resolveWorkspaceDir(api, hookCtx),
                        });
                    }
                } catch (err) {
                    api.logger.warn(`memory-aegis-v8 background capture failed: ${String(err)}`);
                }
            })();
        });

        api.registerService({
            id: "memory-aegis-v8",
            start: () => {
                api.logger.info("memory-aegis-v8 registered");
            },
            stop: async () => undefined,
        });
    },
};

export default memoryPlugin;
