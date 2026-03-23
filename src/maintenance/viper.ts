import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import type { Database } from "better-sqlite3";
import type { AegisConfig } from "../core/models.js";

export class Viper {
  constructor(private db: Database, private workspaceDir: string, private config: AegisConfig) {}

  /**
   * Chạy toàn bộ quy trình "Lột xác" của Viper.
   */
  async shedSkin(dryRun = false): Promise<void> {
    const exportsDir = path.join(this.workspaceDir, "exports");
    if (fs.existsSync(exportsDir)) {
      this.rotateBackups(exportsDir, dryRun);
    }
    this.enforceInteractionStateCaps(dryRun);
    this.compactCaptureFiles(dryRun);
  }

  /**
   * Xoay vòng bản sao lưu theo quy tắc daily/weekly/monthly buckets.
   */
  private rotateBackups(dir: string, dryRun: boolean): void {
    const files = fs.readdirSync(dir)
      .filter(f => f.startsWith("aegis-snapshot-") || f.startsWith("aegis-export-"))
      .map(f => {
        const filePath = path.join(dir, f);
        return { name: f, path: filePath, mtime: fs.statSync(filePath).mtime };
      });

    if (files.length === 0) return;

    files.sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

    const keepDaily = this.config.keepDaily ?? 7;
    const keepWeekly = this.config.keepWeekly ?? 4;
    const keepMonthly = this.config.keepMonthly ?? 3;

    const toKeep = new Set<string>();

    // Daily bucket: newest file per calendar day, last keepDaily days
    const dailyMap = new Map<string, typeof files[0]>();
    for (const f of files) {
      const dayKey = f.mtime.toISOString().slice(0, 10); // YYYY-MM-DD
      if (!dailyMap.has(dayKey)) dailyMap.set(dayKey, f);
    }
    let dailyCount = 0;
    for (const [, f] of dailyMap) {
      if (dailyCount >= keepDaily) break;
      toKeep.add(f.path);
      dailyCount++;
    }

    // Weekly bucket: newest file per ISO week, last keepWeekly weeks
    const weeklyMap = new Map<string, typeof files[0]>();
    for (const f of files) {
      const weekKey = getISOWeekKey(f.mtime);
      if (!weeklyMap.has(weekKey)) weeklyMap.set(weekKey, f);
    }
    let weeklyCount = 0;
    for (const [, f] of weeklyMap) {
      if (weeklyCount >= keepWeekly) break;
      toKeep.add(f.path);
      weeklyCount++;
    }

    // Monthly bucket: newest file per YYYY-MM, last keepMonthly months
    const monthlyMap = new Map<string, typeof files[0]>();
    for (const f of files) {
      const monthKey = f.mtime.toISOString().slice(0, 7); // YYYY-MM
      if (!monthlyMap.has(monthKey)) monthlyMap.set(monthKey, f);
    }
    let monthlyCount = 0;
    for (const [, f] of monthlyMap) {
      if (monthlyCount >= keepMonthly) break;
      toKeep.add(f.path);
      monthlyCount++;
    }

    const toDelete = files.filter(f => !toKeep.has(f.path));
    const kept = toKeep.size;
    const deleted = dryRun ? 0 : toDelete.length;

    if (!dryRun) {
      for (const f of toDelete) {
        try { fs.unlinkSync(f.path); } catch (err) {
          console.error(`Viper: Lỗi khi xóa backup ${f.name}:`, err);
        }
      }
    }

    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(
      crypto.randomUUID(),
      "backup_rotation_completed",
      JSON.stringify({ kept, deleted: toDelete.length, dryRun })
    );
  }

  /**
   * Giới hạn số lượng Interaction States cho mỗi session.
   */
  private enforceInteractionStateCaps(dryRun: boolean): void {
    const maxStates = this.config.maxInteractionStatesPerSession ?? 10;
    const sessions = this.db.prepare("SELECT DISTINCT session_id FROM interaction_states").all() as any[];

    let totalPruned = 0;
    for (const session of sessions) {
      const excess = this.db.prepare(`
        SELECT COUNT(*) - ? as over FROM interaction_states WHERE session_id = ?
      `).get(maxStates, session.session_id) as { over: number };

      if (excess.over > 0) {
        if (!dryRun) {
          this.db.prepare(`
            DELETE FROM interaction_states
            WHERE id IN (
              SELECT id FROM interaction_states
              WHERE session_id = ?
              ORDER BY last_updated_at DESC
              LIMIT -1 OFFSET ?
            )
          `).run(session.session_id, maxStates);
        }
        totalPruned += excess.over;
      }
    }

    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(
      crypto.randomUUID(),
      "interaction_state_pruned",
      JSON.stringify({ pruned: totalPruned, dryRun })
    );
  }

  /**
   * Nén hoặc cắt bớt các file capture nếu quá dung lượng cho phép.
   */
  private compactCaptureFiles(dryRun: boolean): void {
    const memoryDir = path.join(this.workspaceDir, "memory");
    const captureFile = path.join(memoryDir, "aegis-session-capture.md");
    const maxBytes = this.config.maxScratchCaptureBytes ?? (1024 * 1024);

    if (!fs.existsSync(captureFile)) return;

    const stats = fs.statSync(captureFile);
    if (stats.size <= maxBytes) return;

    const originalBytes = stats.size;
    const content = fs.readFileSync(captureFile, "utf-8");
    const lines = content.split("\n");
    const keepLines = lines.slice(Math.floor(lines.length * 0.8));
    const keptBytes = Buffer.byteLength(keepLines.join("\n"), "utf-8");

    if (!dryRun) {
      fs.writeFileSync(captureFile, keepLines.join("\n"), "utf-8");
    }

    this.db.prepare(
      "INSERT INTO memory_events (id, event_type, payload_json, created_at) VALUES (?, ?, ?, datetime('now'))"
    ).run(
      crypto.randomUUID(),
      "capture_compacted",
      JSON.stringify({ originalBytes, keptBytes, dryRun })
    );
  }
}

/**
 * Tính ISO week key: "YYYY-WW"
 */
function getISOWeekKey(date: Date): string {
  const d = new Date(date);
  d.setUTCHours(0, 0, 0, 0);
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}
