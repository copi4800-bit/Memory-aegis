#!/usr/bin/env node
/**
 * Aegis v8 Quick Setup — Python-first onboarding CLI.
 */

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import fs from "node:fs";

const execFileAsync = promisify(execFile);

function resolveRepoRoot(): string {
  const here = path.dirname(new URL(import.meta.url).pathname);
  const candidates = [
    path.resolve(here, "../.."),
    path.resolve(here, "../../.."),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, "aegis_py", "mcp", "server.py"))) {
      return candidate;
    }
  }
  throw new Error("Unable to locate the Aegis repository root.");
}

function resolvePythonExecutable(repoRoot: string): string {
  const configured = process.env.AEGIS_PYTHON_BIN;
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
  throw new Error("No Python executable available for Aegis setup.");
}

async function main() {
  console.log("================================================");
  console.log("   Welcome to Memory Aegis v8 — Quick Setup   ");
  console.log("================================================");
  console.log("");

  const workspaceDir = process.cwd();
  console.log(`- Workspace detected: ${workspaceDir}`);

  try {
    const repoRoot = resolveRepoRoot();
    const pythonBin = resolvePythonExecutable(repoRoot);
    const dbPath = process.env.AEGIS_DB_PATH ?? path.join(workspaceDir, ".aegis_py", "memory_aegis_py.db");
    const env = {
      ...process.env,
      PYTHONPATH: process.env.PYTHONPATH
        ? `${repoRoot}:${process.env.PYTHONPATH}`
        : repoRoot,
      AEGIS_DB_PATH: dbPath,
    };

    console.log("- Running Python onboarding checks...");
    const { stdout } = await execFileAsync(
      pythonBin,
      ["-m", "aegis_py.cli", "--db-path", dbPath, "onboarding", "--workspace-dir", workspaceDir],
      {
      cwd: repoRoot,
      env,
      maxBuffer: 1024 * 1024,
      },
    );

    console.log("");
    process.stdout.write(stdout.trimEnd());
    console.log("");
    console.log("");
    console.log("Aegis Python onboarding finished.");
  } catch (err) {
    console.error("Critical error during setup:", err);
    process.exit(1);
  }

  console.log("");
  console.log("================================================");
}

main();
