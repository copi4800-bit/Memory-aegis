/**
 * Tardigrade (Gấu nước) Layer — Disaster Recovery & Snapshots.
 *
 * Chức năng: Đóng băng bộ nhớ (Cryptobiosis / Tun state).
 * Tạo các bản sao an toàn (backup) của SQLite DB và export dữ liệu
 * để phòng chống sự cố.
 */

import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import { createHash, randomUUID } from "node:crypto";
import { nowISO } from "../core/id.js";

export interface BackupResult {
  snapshotPath: string;
  checksum: string;
  sizeBytes: number;
  createdAt: string;
}

export interface ExportResult {
  exportPath: string;
  nodeCount: number;
  edgeCount: number;
  createdAt: string;
}

/**
 * Tạo một Snapshot an toàn của Database hiện tại (.db.bak).
 * Sử dụng SQLite Online Backup API tĩnh để không block các tiến trình khác.
 */
export async function createSnapshot(
  sourceDb: Database.Database,
  backupDir: string,
): Promise<BackupResult> {
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const fileName = `aegis-snapshot-${timestamp}.db.bak`;
  const backupPath = path.join(backupDir, fileName);

  try {
    // Thực hiện online backup từ sourceDb sang backupPath
    await sourceDb.backup(backupPath);

    const stats = fs.statSync(backupPath);
    const checksum = calculateChecksum(backupPath);

    const result: BackupResult = {
      snapshotPath: backupPath,
      checksum,
      sizeBytes: stats.size,
      createdAt: nowISO(),
    };

    // Ghi log backup
    sourceDb.prepare(`
      INSERT INTO memory_events (id, event_type, payload_json, created_at)
      VALUES (?, 'system_backup', ?, ?)
    `).run(randomUUID(), JSON.stringify(result), result.createdAt);

    return result;
  } finally {
    // no-op: sourceDb.backup() manages its own destination connection
  }
}

/**
 * Export dữ liệu memory nodes và edges ra định dạng JSONL tĩnh
 * để có thể lưu trữ raw data.
 */
export function exportLogicalData(
  db: Database.Database,
  exportPath: string,
): ExportResult {
  const dir = path.dirname(exportPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const fd = fs.openSync(exportPath, "w");
  let nodeCount = 0;
  let edgeCount = 0;

  try {
    // Xuất nodes
    const nodes = db.prepare("SELECT * FROM memory_nodes").all() as any[];
    for (const node of nodes) {
      fs.writeSync(fd, JSON.stringify({ type: "node", data: node }) + "\n");
      nodeCount++;
    }

    // Xuất edges
    const edges = db.prepare("SELECT * FROM memory_edges").all() as any[];
    for (const edge of edges) {
      fs.writeSync(fd, JSON.stringify({ type: "edge", data: edge }) + "\n");
      edgeCount++;
    }

    // Xuất entities
    const entities = db.prepare("SELECT * FROM entities").all() as any[];
    for (const entity of entities) {
      fs.writeSync(fd, JSON.stringify({ type: "entity", data: entity }) + "\n");
    }

    return {
      exportPath,
      nodeCount,
      edgeCount,
      createdAt: nowISO(),
    };
  } finally {
    fs.closeSync(fd);
  }
}

/**
 * Tính mã băm (checksum) của file để xác thực toàn vẹn dữ liệu.
 */
function calculateChecksum(filePath: string): string {
  const fileBuffer = fs.readFileSync(filePath);
  const hashSum = createHash("sha256");
  hashSum.update(fileBuffer);
  return hashSum.digest("hex");
}
