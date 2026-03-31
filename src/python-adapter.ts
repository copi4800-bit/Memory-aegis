import fs from "node:fs";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export type PythonAdapterMode = "off" | "auto" | "force";

export type AdapterSearchResult = {
  path: string;
  startLine: number;
  endLine: number;
  score: number;
  snippet: string;
  source: "memory" | "sessions";
  citation?: string;
};

type PythonSearchMemory = {
  id: string;
  type: string;
  content: string;
  source_ref?: string | null;
};

type PythonSearchResult = {
  memory: PythonSearchMemory;
  score: number;
  reason?: string;
  provenance?: string;
  reasons?: string[];
  conflict_status?: string;
};

export type PythonSearchResponse = {
  mappedResults: AdapterSearchResult[];
  rawResults: PythonSearchResult[];
};

export type PythonToolInvocation = {
  tool: string;
  args?: Record<string, unknown>;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
};

export type PythonMemoryGetResponse = {
  text: string;
  path: string;
  from?: number;
  lines?: number;
  memory_id?: string;
  type?: string;
  source_ref?: string | null;
  backend: "python";
};

export function resolvePythonAdapterMode(
  configured: unknown,
  env: NodeJS.ProcessEnv = process.env,
): PythonAdapterMode {
  const raw = typeof configured === "string" && configured.trim()
    ? configured.trim().toLowerCase()
    : typeof env.AEGIS_PYTHON_RETRIEVAL === "string"
      ? env.AEGIS_PYTHON_RETRIEVAL.trim().toLowerCase()
      : "";

  if (raw === "force") return "force";
  if (raw === "auto" || raw === "1" || raw === "true" || raw === "on") return "auto";
  return "off";
}

export async function searchViaPython(args: {
  query: string;
  limit?: number;
  scopeType?: string;
  scopeId?: string;
  includeGlobal?: boolean;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<PythonSearchResponse> {
  const stdout = await invokePythonToolRaw({
    tool: "memory_search",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: {
      text: args.query,
      limit: args.limit ?? 5,
      scope_type: args.scopeType ?? "agent",
      scope_id: args.scopeId ?? "default",
      include_global: args.includeGlobal ?? true,
    },
  });
  const rawResults = parsePythonSearchResults(stdout);
  return {
    rawResults,
    mappedResults: rawResults.map(mapPythonResult),
  };
}

export async function contextPackViaPython(args: {
  query: string;
  limit?: number;
  scopeType?: string;
  scopeId?: string;
  includeGlobal?: boolean;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_context_pack",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        text: args.query,
        limit: args.limit ?? 5,
        scope_type: args.scopeType ?? "agent",
        scope_id: args.scopeId ?? "default",
        include_global: args.includeGlobal ?? true,
      },
    }),
  );
}

export async function linkStoreViaPython(args: {
  sourceId: string;
  targetId: string;
  linkType: string;
  weight?: number;
  metadata?: Record<string, unknown>;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_link_store",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        source_id: args.sourceId,
        target_id: args.targetId,
        link_type: args.linkType,
        weight: args.weight ?? 1.0,
        metadata: args.metadata ?? {},
      },
    }),
  );
}

export async function linkNeighborsViaPython(args: {
  memoryId: string;
  limit?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_link_neighbors",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        memory_id: args.memoryId,
        limit: args.limit ?? 10,
      },
    }),
  );
}

export async function storeViaPython(args: {
  text: string;
  scopeType?: string;
  scopeId?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  return invokePythonToolRaw({
    tool: "memory_store",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: {
      type: "episodic",
      content: args.text,
      scope_type: args.scopeType ?? "agent",
      scope_id: args.scopeId ?? "default",
      source_kind: "manual",
      source_ref: "openclaw:memory_store",
    },
  });
}

export async function statusViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_status",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function conflictPromptViaPython(args: {
  scopeType?: string;
  scopeId?: string;
  subject?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_conflict_prompt",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        subject: args.subject,
      },
    }),
  );
}

export async function conflictResolveViaPython(args: {
  conflictId: string;
  action: string;
  rationale?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_conflict_resolve",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        conflict_id: args.conflictId,
        action: args.action,
        rationale: args.rationale,
      },
    }),
  );
}

export async function getViaPython(args: {
  relPath: string;
  from?: number;
  lines?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<PythonMemoryGetResponse> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_get",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        rel_path: args.relPath,
        from: args.from ?? 0,
        lines: args.lines,
        workspace_dir: args.workspaceDir,
      },
    }),
  ) as PythonMemoryGetResponse;
}

export async function cleanViaPython(args: {
  subject?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_clean",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: { subject: args.subject },
    }),
  );
}

export async function profileViaPython(args: {
  scopeId?: string;
  scopeType?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  return invokePythonToolRaw({
    tool: "memory_profile",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: {
      scope_id: args.scopeId ?? "default",
      scope_type: args.scopeType ?? "agent",
    },
  });
}

export async function surfaceViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_surface",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function serviceInfoViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonServerCommandRaw({
      flag: "--service-info",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function startupProbeViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonServerCommandRaw({
      flag: "--startup-probe",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function scopePolicyViaPython(args: {
  scopeType?: string;
  scopeId?: string;
  syncPolicy?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_scope_policy",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        sync_policy: args.syncPolicy,
      },
    }),
  );
}

export async function syncExportViaPython(args: {
  scopeType: string;
  scopeId: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_sync_export",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        workspace_dir: args.workspaceDir,
      },
    }),
  );
}

export async function syncPreviewViaPython(args: {
  envelopePath: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_sync_preview",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        envelope_path: args.envelopePath,
      },
    }),
  );
}

export async function syncImportViaPython(args: {
  envelopePath: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_sync_import",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        envelope_path: args.envelopePath,
      },
    }),
  );
}

export async function doctorViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_doctor",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: { workspace_dir: args.workspaceDir },
    }),
  );
}

export async function storageFootprintViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_storage_footprint",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function storageCompactViaPython(args: {
  archivedMemoryDays?: number;
  supersededMemoryDays?: number;
  evidenceDays?: number;
  governanceDays?: number;
  replicationDays?: number;
  backgroundDays?: number;
  vacuum?: boolean;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_storage_compact",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        archived_memory_days: args.archivedMemoryDays ?? 30,
        superseded_memory_days: args.supersededMemoryDays ?? 14,
        evidence_days: args.evidenceDays ?? 30,
        governance_days: args.governanceDays ?? 30,
        replication_days: args.replicationDays ?? 14,
        background_days: args.backgroundDays ?? 14,
        vacuum: args.vacuum ?? true,
      },
    }),
  );
}

export async function onboardingViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  const stdout = await invokePythonCliRaw({
    command: "onboarding",
    workspaceDir: args.workspaceDir,
    env: args.env,
    cliArgs: ["--json"],
  });
  return parseJsonObject(stdout);
}

export async function backupUploadViaPython(args: {
  mode?: "snapshot" | "export";
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_backup_upload",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        mode: args.mode ?? "snapshot",
        workspace_dir: args.workspaceDir,
      },
    }),
  );
}

export async function backupListViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_backup_list",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        workspace_dir: args.workspaceDir,
      },
    }),
  );
}

export async function backupPreviewViaPython(args: {
  snapshotPath: string;
  scopeType?: string;
  scopeId?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_backup_preview",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        snapshot_path: args.snapshotPath,
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        workspace_dir: args.workspaceDir,
      },
    }),
  );
}

export async function taxonomyCleanViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_taxonomy_clean",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function rebuildViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_rebuild",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function scanViaPython(args: {
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_scan",
      workspaceDir: args.workspaceDir,
      env: args.env,
    }),
  );
}

export async function visualizeViaPython(args: {
  limit?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_visualize",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: { limit: args.limit ?? 1000 },
    }),
  );
}

export async function governanceViaPython(args: {
  scopeType?: string;
  scopeId?: string;
  memoryId?: string;
  limit?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_governance",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        memory_id: args.memoryId,
        limit: args.limit ?? 50,
      },
    }),
  );
}

export async function backgroundPlanViaPython(args: {
  scopeType: string;
  scopeId: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_background_plan",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        scope_type: args.scopeType,
        scope_id: args.scopeId,
      },
    }),
  );
}

export async function backgroundShadowViaPython(args: {
  runId: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_background_shadow",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: { run_id: args.runId },
    }),
  );
}

export async function backgroundApplyViaPython(args: {
  runId: string;
  maxMutations?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_background_apply",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        run_id: args.runId,
        max_mutations: args.maxMutations ?? 5,
      },
    }),
  );
}

export async function backgroundRollbackViaPython(args: {
  runId: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_background_rollback",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: { run_id: args.runId },
    }),
  );
}

export async function vectorInspectViaPython(args: {
  query: string;
  scopeType: string;
  scopeId: string;
  includeGlobal?: boolean;
  limit?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_vector_inspect",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        query: args.query,
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        include_global: args.includeGlobal ?? false,
        limit: args.limit ?? 10,
      },
    }),
  );
}

export async function evidenceArtifactsViaPython(args: {
  scopeType?: string;
  scopeId?: string;
  memoryId?: string;
  limit?: number;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_evidence_artifacts",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        memory_id: args.memoryId,
        limit: args.limit ?? 50,
      },
    }),
  );
}

export async function backupDownloadViaPython(args: {
  snapshotPath: string;
  scopeType?: string;
  scopeId?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<Record<string, unknown>> {
  return parseJsonObject(
    await invokePythonToolRaw({
      tool: "memory_backup_download",
      workspaceDir: args.workspaceDir,
      env: args.env,
      args: {
        snapshot_path: args.snapshotPath,
        scope_type: args.scopeType,
        scope_id: args.scopeId,
        workspace_dir: args.workspaceDir,
      },
    }),
  );
}

export async function rememberViaPython(args: {
  content: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  return invokePythonToolRaw({
    tool: "memory_remember",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: { content: args.content },
  });
}

export async function recallViaPython(args: {
  query: string;
  scopeType?: string;
  scopeId?: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  return invokePythonToolRaw({
    tool: "memory_recall",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: {
      query: args.query,
      scope_type: args.scopeType,
      scope_id: args.scopeId,
    },
  });
}

export async function correctViaPython(args: {
  content: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  return invokePythonToolRaw({
    tool: "memory_correct",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: { content: args.content },
  });
}

export async function forgetViaPython(args: {
  query: string;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  return invokePythonToolRaw({
    tool: "memory_forget",
    workspaceDir: args.workspaceDir,
    env: args.env,
    args: { query: args.query },
  });
}

function buildPythonEnv(workspaceDir: string | undefined, env: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  const repoRoot = resolveRepoRoot();
  const existingPythonPath = env.PYTHONPATH?.trim();
  const pythonPath = existingPythonPath
    ? `${repoRoot}${path.delimiter}${existingPythonPath}`
    : repoRoot;
  if (env.AEGIS_DB_PATH || !workspaceDir) {
    return {
      ...env,
      PYTHONPATH: pythonPath,
    };
  }
  return {
    ...env,
    AEGIS_DB_PATH: path.join(workspaceDir, ".aegis_py", "memory_aegis_py.db"),
    PYTHONPATH: pythonPath,
  };
}

function resolveRepoRoot(): string {
  const here = path.dirname(new URL(import.meta.url).pathname);
  const candidates = [
    path.resolve(here, ".."),
    path.resolve(here, "../.."),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "aegis_py", "mcp", "server.py"))) {
      return candidate;
    }
  }
  throw new Error("Unable to locate repository root for Aegis Python adapter.");
}

function resolveServerPath(repoRoot: string): string {
  const serverPath = path.join(repoRoot, "aegis_py", "mcp", "server.py");
  if (!fs.existsSync(serverPath)) {
    throw new Error(`Aegis Python server not found at ${serverPath}`);
  }
  return serverPath;
}

function resolvePythonExecutable(repoRoot: string, env: NodeJS.ProcessEnv): string {
  const configured = env.AEGIS_PYTHON_BIN;
  const candidates = [
    configured,
    path.join(repoRoot, ".venv", "bin", "python"),
    "python3",
    "python",
  ];
  for (const candidate of candidates) {
    if (!candidate) continue;
    if (candidate.includes(path.sep)) {
      if (fs.existsSync(candidate)) {
        return candidate;
      }
      continue;
    }
    return candidate;
  }
  throw new Error("No Python executable available for Aegis Python adapter.");
}

async function invokePythonToolRaw(invocation: PythonToolInvocation): Promise<string> {
  const env = buildPythonEnv(invocation.workspaceDir, invocation.env ?? process.env);
  const repoRoot = resolveRepoRoot();
  const pythonBin = resolvePythonExecutable(repoRoot, env);
  const commandArgs = [
    "-m",
    "aegis_py.mcp.server",
    "--tool",
    invocation.tool,
    "--args-json",
    JSON.stringify(invocation.args ?? {}),
  ];

  const { stdout } = await execFileAsync(pythonBin, commandArgs, {
    cwd: repoRoot,
    env,
    maxBuffer: 1024 * 1024,
  });
  return stdout.trim();
}

async function invokePythonServerCommandRaw(args: {
  flag: "--service-info" | "--startup-probe";
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  const env = buildPythonEnv(args.workspaceDir, args.env ?? process.env);
  const repoRoot = resolveRepoRoot();
  const pythonBin = resolvePythonExecutable(repoRoot, env);
  const commandArgs = ["-m", "aegis_py.mcp.server", args.flag];
  if (args.workspaceDir) {
    commandArgs.push("--workspace-dir", args.workspaceDir);
  }
  const { stdout } = await execFileAsync(pythonBin, commandArgs, {
    cwd: repoRoot,
    env,
    maxBuffer: 1024 * 1024,
  });
  return stdout.trim();
}

async function invokePythonCliRaw(args: {
  command: string;
  cliArgs?: string[];
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
}): Promise<string> {
  const env = buildPythonEnv(args.workspaceDir, args.env ?? process.env);
  const repoRoot = resolveRepoRoot();
  const pythonBin = resolvePythonExecutable(repoRoot, env);
  const commandArgs = ["-m", "aegis_py.cli"];
  if (args.workspaceDir) {
    commandArgs.push("--db-path", path.join(args.workspaceDir, ".aegis_py", "memory_aegis_py.db"));
  }
  commandArgs.push(args.command);
  if (args.workspaceDir) {
    commandArgs.push("--workspace-dir", args.workspaceDir);
  }
  commandArgs.push(...(args.cliArgs ?? []));
  const { stdout } = await execFileAsync(pythonBin, commandArgs, {
    cwd: repoRoot,
    env,
    maxBuffer: 1024 * 1024,
  });
  return stdout.trim();
}

function parsePythonSearchResults(stdout: string): PythonSearchResult[] {
  const payload = JSON.parse(stdout.trim() || "[]") as unknown;
  if (!Array.isArray(payload)) {
    throw new Error("Aegis Python search response was not an array.");
  }
  return payload as PythonSearchResult[];
}

function parseJsonObject(stdout: string): Record<string, unknown> {
  const payload = JSON.parse(stdout || "{}") as unknown;
  if (!payload || Array.isArray(payload) || typeof payload !== "object") {
    throw new Error("Aegis Python response was not a JSON object.");
  }
  return payload as Record<string, unknown>;
}

function mapPythonResult(result: PythonSearchResult): AdapterSearchResult {
  const memory = result.memory;
  return {
    path: memory.source_ref || `aegis://${memory.type}/${memory.id}`,
    startLine: 0,
    endLine: 0,
    score: clampScore(result.score),
    snippet: truncate(memory.content, 500),
    source: "memory",
    citation: buildCitation(result),
  };
}

function buildCitation(result: PythonSearchResult): string {
  const parts = [
    `[${result.memory.type}]`,
    result.reason,
    result.provenance,
    result.conflict_status && result.conflict_status !== "none"
      ? `conflict=${result.conflict_status}`
      : undefined,
  ].filter(Boolean);
  return parts.join(" ");
}

function truncate(value: string, maxLength: number): string {
  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 1)}...`;
}

function clampScore(score: number): number {
  if (!Number.isFinite(score)) {
    return 0;
  }
  return Math.max(0, Math.min(1, score));
}
