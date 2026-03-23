/**
 * Planarian (Giun dẹp) Layer — Rebuild & Restore Tooling.
 *
 * Chức năng: Khôi phục lại trí nhớ từ các bản ghi đã lưu (Backup).
 * Tái sinh toàn bộ hệ thống SQLite DB từ snapshot.
 */

import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";
import { closeAllManagers } from "../aegis-manager.js";

export interface RestoreResult {
  success: boolean;
  message: string;
  restoredFrom: string;
  timestamp: string;
}

/**
 * Phục hồi bộ nhớ từ một file Snapshot (.db.bak).
 *
 * Quá trình này rất nguy hiểm vì nó ghi đè toàn bộ dữ liệu hiện tại.
 * Để an toàn, hàm này yêu cầu đóng mọi kết nối hiện tại đến DB trước khi thực hiện.
 *
 * @param sourceBackupPath Đường dẫn tới file backup
 * @param targetDbPath Đường dẫn tới file DB chính cần phục hồi
 */
export async function restoreFromSnapshot(
  sourceBackupPath: string,
  targetDbPath: string,
): Promise<RestoreResult> {
  const now = new Date().toISOString();

  if (!fs.existsSync(sourceBackupPath)) {
    throw new Error(`Backup file not found: ${sourceBackupPath}`);
  }

  // B1: Force close all connections and managers to release file locks
  await closeAllManagers();

  // B2: Xoá hoặc đổi tên DB hiện tại (kèm theo file WAL và SHM nếu có) để tránh xung đột
  const walPath = `${targetDbPath}-wal`;
  const shmPath = `${targetDbPath}-shm`;

  if (fs.existsSync(targetDbPath)) {
    // Đổi tên thành file tạm để fallback nếu lỗi
    fs.renameSync(targetDbPath, `${targetDbPath}.corrupted`);
  }
  if (fs.existsSync(walPath)) fs.unlinkSync(walPath);
  if (fs.existsSync(shmPath)) fs.unlinkSync(shmPath);

  // B3: Copy file backup thành file DB mới
  try {
    fs.copyFileSync(sourceBackupPath, targetDbPath);

    // Mở lại kết nối để chạy reindex (đảm bảo FTS5 search hoạt động chuẩn)
    const db = new Database(targetDbPath);
    try {
      rebuildIndexes(db);
    } finally {
      db.close();
    }

    // Xoá file corrupted nếu restore thành công
    if (fs.existsSync(`${targetDbPath}.corrupted`)) {
      fs.unlinkSync(`${targetDbPath}.corrupted`);
    }

    return {
      success: true,
      message: "Database successfully restored from snapshot.",
      restoredFrom: sourceBackupPath,
      timestamp: now,
    };
  } catch (error) {
    // Fallback: Nếu lỗi trong quá trình copy/reindex, trả lại file cũ
    if (fs.existsSync(`${targetDbPath}.corrupted`)) {
      if (fs.existsSync(targetDbPath)) fs.unlinkSync(targetDbPath);
      fs.renameSync(`${targetDbPath}.corrupted`, targetDbPath);
    }

    return {
      success: false,
      message: `Restore failed: ${error instanceof Error ? error.message : String(error)}`,
      restoredFrom: sourceBackupPath,
      timestamp: now,
    };
  }
}

/**
 * Chạy lại các query để cập nhật chỉ mục Full Text Search (FTS5).
 */
export function rebuildIndexes(db: Database.Database): void {
  // Rebuild FTS table to ensure sync with memory_nodes
  db.exec(`
    INSERT INTO memory_nodes_fts(memory_nodes_fts) VALUES('rebuild');
    INSERT INTO memory_nodes_fts(memory_nodes_fts) VALUES('optimize');
  `);
}
