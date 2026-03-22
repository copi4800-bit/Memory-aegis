import fs from "node:fs";
import path from "node:path";
import type Database from "better-sqlite3";
import { getSchemaVersion } from "../db/migrate.js";

export interface DoctorReport {
  workspace: { path: string; exists: boolean; writable: boolean };
  database: { path: string; exists: boolean; version: number; healthy: boolean };
  folders: Array<{ name: string; path: string; exists: boolean }>;
  summary: { status: "healthy" | "degraded" | "broken"; issues: string[] };
}

export class AegisDoctor {
  constructor(
    private db: Database.Database,
    private workspaceDir: string,
    private dbPath: string
  ) {}

  diagnose(): DoctorReport {
    const issues: string[] = [];

    // 1. Workspace check
    const wsExists = fs.existsSync(this.workspaceDir);
    let wsWritable = false;
    if (wsExists) {
      try {
        const testFile = path.join(this.workspaceDir, ".doctor_test");
        fs.writeFileSync(testFile, "test");
        fs.unlinkSync(testFile);
        wsWritable = true;
      } catch {
        issues.push("Workspace directory is not writable.");
      }
    } else {
      issues.push("Workspace directory does not exist.");
    }

    // 2. Database check
    const dbExists = fs.existsSync(this.dbPath);
    const version = getSchemaVersion(this.db);
    const dbHealthy = version > 0;
    if (!dbExists) issues.push("Database file not found at expected path.");
    if (version === 0) issues.push("Database schema is uninitialized or corrupted.");

    // 3. Important Folders check
    const importantFolders = [
      { name: "Memory Capture", path: "memory" },
      { name: "Exports/Backups", path: "exports" },
      { name: "Archives", path: "archives" },
    ];
    const folderStatus = importantFolders.map(f => ({
      name: f.name,
      path: f.path,
      exists: fs.existsSync(path.join(this.workspaceDir, f.path)),
    }));

    // Summary
    let status: DoctorReport["summary"]["status"] = "healthy";
    if (issues.length > 0) {
      status = (wsExists && dbHealthy) ? "degraded" : "broken";
    }

    return {
      workspace: { path: this.workspaceDir, exists: wsExists, writable: wsWritable },
      database: { path: this.dbPath, exists: dbExists, version, healthy: dbHealthy },
      folders: folderStatus,
      summary: { status, issues },
    };
  }

  render(report: DoctorReport): string {
    const s = report.summary;
    const icon = s.status === "healthy" ? "✅" : s.status === "degraded" ? "⚠️" : "❌";

    let output = `[Aegis Doctor Report]\n`;
    output += `Status: ${icon} ${s.status.toUpperCase()}\n`;
    output += `----------------------------------\n`;
    output += `Workspace: ${report.workspace.path} (${report.workspace.exists ? "OK" : "MISSING"})\n`;
    output += `Database:  v${report.database.version} (${report.database.healthy ? "OK" : "ERROR"})\n`;
    output += `----------------------------------\n`;

    if (s.issues.length > 0) {
      output += `Issues Found:\n`;
      s.issues.forEach(iss => output += `- ${iss}\n`);
      output += `----------------------------------\n`;
    }

    output += `Directory Map:\n`;
    report.folders.forEach(f => {
      output += `  [${f.exists ? "v" : " "}] ${f.name} (/${f.path})\n`;
    });

    return output;
  }
}
