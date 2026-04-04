"use strict";

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const childProcess = require("node:child_process");

const REPO_ROOT = path.resolve(__dirname, "..");
const DEFAULT_TOOL_TIMEOUT_MS = 30000;

function sanitizeAgentId(value) {
  const raw = typeof value === "string" && value.trim().length > 0 ? value.trim() : "default";
  return raw.replace(/[^a-zA-Z0-9._-]+/g, "-");
}

function resolvePythonCommand() {
  return process.env.TRUTHKEEP_PYTHON || process.env.PYTHON || process.env.PYTHON3 || "python";
}

function resolveDbPath(agentId) {
  const explicit = process.env.TRUTHKEEP_DB_PATH || process.env.AEGIS_DB_PATH;
  if (typeof explicit === "string" && explicit.trim().length > 0) {
    return explicit;
  }
  const dir = path.join(os.homedir(), ".openclaw", "truthkeep-memory");
  fs.mkdirSync(dir, { recursive: true });
  return path.join(dir, `${sanitizeAgentId(agentId)}.db`);
}

function buildEnv(dbPath) {
  const currentPythonPath = process.env.PYTHONPATH;
  const nextPythonPath =
    typeof currentPythonPath === "string" && currentPythonPath.length > 0
      ? `${REPO_ROOT}${path.delimiter}${currentPythonPath}`
      : REPO_ROOT;
  return {
    ...process.env,
    AEGIS_DB_PATH: dbPath,
    PYTHONPATH: nextPythonPath,
  };
}

function runTruthKeepCommand(args, options = {}) {
  const agentId = options.agentId;
  const dbPath = resolveDbPath(agentId);
  const result = childProcess.spawnSync(resolvePythonCommand(), ["-m", "truthkeep.mcp", ...args], {
    cwd: REPO_ROOT,
    env: buildEnv(dbPath),
    encoding: "utf8",
    timeout: options.timeoutMs || DEFAULT_TOOL_TIMEOUT_MS,
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    const stderr = typeof result.stderr === "string" ? result.stderr.trim() : "";
    const stdout = typeof result.stdout === "string" ? result.stdout.trim() : "";
    const detail = stderr || stdout || `exit code ${result.status}`;
    throw new Error(`TruthKeep command failed: ${detail}`);
  }
  const stdout = typeof result.stdout === "string" ? result.stdout.trim() : "";
  if (!stdout) {
    throw new Error("TruthKeep command returned no output");
  }
  return {
    dbPath,
    payload: JSON.parse(stdout),
  };
}

function mapStatusPayload(statsPayload, fieldSnapshotPayload, startupPayload, dbPath) {
  const health = statsPayload && typeof statsPayload.health === "object" ? statsPayload.health : {};
  const storage = statsPayload && typeof statsPayload.storage === "object" ? statsPayload.storage : {};
  const rowCounts = storage && typeof storage.rows === "object" ? storage.rows : {};
  const counts =
    fieldSnapshotPayload && typeof fieldSnapshotPayload.counts === "object"
      ? fieldSnapshotPayload.counts
      : {};
  const energy =
    fieldSnapshotPayload && typeof fieldSnapshotPayload.energy === "object"
      ? fieldSnapshotPayload.energy
      : {};

  const memoryRows = Number(rowCounts.memories || 0);
  const totalFieldCount = Object.values(counts).reduce(
    (sum, value) => sum + (Number.isFinite(Number(value)) ? Number(value) : 0),
    0,
  );

  return {
    backend: "builtin",
    provider: "truthkeep-memory",
    model: "correctness-first",
    dbPath,
    fts: true,
    vector: false,
    files: 1,
    chunks: memoryRows,
    dirty: false,
    custom: {
      runtime: "truthkeep-python",
      healthState: startupPayload.health_state || statsPayload.health_state || "UNKNOWN",
      ready: Boolean(startupPayload.ready),
      capabilities: health.capabilities || {},
      fieldCounts: counts,
      fieldMemoryCount: totalFieldCount,
      stateCoverage: fieldSnapshotPayload.state_coverage || {},
      averages: fieldSnapshotPayload.averages || {},
      bundleEnergyProxy: energy.bundle_energy_proxy || 0,
      objectiveProxy: energy.objective_proxy || 0,
    },
  };
}

function createManagerSnapshot(agentId) {
  const startup = runTruthKeepCommand(["--startup-probe"], { agentId });
  const stats = runTruthKeepCommand(["--tool", "memory_stats", "--args-json", "{}"], { agentId });
  const fieldSnapshot = runTruthKeepCommand(["--tool", "memory_v10_field_snapshot", "--args-json", "{}"], {
    agentId,
  });

  const status = mapStatusPayload(stats.payload, fieldSnapshot.payload, startup.payload, startup.dbPath);

  return {
    status,
    dbPath: startup.dbPath,
  };
}

function createTruthKeepMemoryRuntime() {
  return {
    async getMemorySearchManager(params) {
      try {
        const snapshot = createManagerSnapshot(params && params.agentId);
        return {
          manager: {
            status() {
              return snapshot.status;
            },
            async probeEmbeddingAvailability() {
              return {
                ok: false,
                error:
                  "TruthKeep is correctness-first and does not expose dense embedding runtime dependencies.",
              };
            },
            async probeVectorAvailability() {
              return false;
            },
            async sync(syncParams) {
              if (syncParams && typeof syncParams.progress === "function") {
                syncParams.progress({
                  stage: "complete",
                  message:
                    "TruthKeep native adapter uses local-first storage and has no external sync backend.",
                });
              }
            },
            async close() {},
          },
        };
      } catch (error) {
        return {
          manager: null,
          error: error instanceof Error ? error.message : String(error),
        };
      }
    },
    resolveMemoryBackendConfig() {
      return { backend: "builtin" };
    },
    async closeAllMemorySearchManagers() {},
  };
}

module.exports = {
  createTruthKeepMemoryRuntime,
};
